"""Network routing, graph construction, and shortest-path distance module.

Implements:
1. Walkable OpenStreetMap graph acquisition and GraphML caching
2. Nearest-node snapping with explicit snapping distance diagnostics
3. Efficient multi-source shortest-path walking distance computation:
   d_i = min_{j in L} d_G(o_i, f_j)
4. Fallback straight-line (Euclidean) distance comparisons
5. Graph connectivity diagnostics and unreachable component handling
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import geopandas as gpd
import networkx as nx
import numpy as np
import osmnx as ox
from scipy.spatial import cKDTree
from shapely.geometry import Point

logger = logging.getLogger(__name__)


def build_or_load_network(
    boundary_gdf: gpd.GeoDataFrame,
    graphml_path: Path | str,
    network_type: str = "walk",
    buffer_meters: float = 500.0,
    offline: bool = False,
    timeout: int = 180,
) -> nx.MultiDiGraph:
    """Build or load cached walkable pedestrian network graph for Chicago.

    Parameters
    ----------
    boundary_gdf : gpd.GeoDataFrame
        Chicago municipal boundary GeoDataFrame.
    graphml_path : Path | str
        Path to local GraphML cache file.
    network_type : str
        OSMnx network type ('walk' for pedestrian paths).
    buffer_meters : float
        Buffer around city boundary in meters to include border corridors.
    offline : bool
        If True, fails if cached graph does not exist.
    timeout : int
        Overpass timeout in seconds.

    Returns
    -------
    nx.MultiDiGraph
        Walkable network graph with length attributes in meters.
    """
    dest = Path(graphml_path)
    if dest.exists() and dest.stat().st_size > 0:
        logger.info(f"Loading cached pedestrian graph from {dest} ({dest.stat().st_size} bytes)...")
        G = ox.load_graphml(dest)
        logger.info(f"Loaded graph with {len(G.nodes)} nodes and {len(G.edges)} edges.")
        return G

    if offline:
        raise FileNotFoundError(
            f"Offline mode enabled, but cached network graph not found at {dest}. "
            "Please run without --offline to acquire the network graph."
        )

    dest.parent.mkdir(parents=True, exist_ok=True)
    logger.info(f"Acquiring '{network_type}' network graph for Chicago...")

    ox.settings.timeout = timeout
    ox.settings.requests_timeout = timeout
    ox.settings.overpass_rate_limit = True

    # Buffer boundary in projected CRS (EPSG:26971) then convert back to EPSG:4326 for Overpass
    boundary_proj = boundary_gdf.to_crs("EPSG:26971")
    buffered_poly = boundary_proj.unary_union.buffer(buffer_meters)
    buffered_gdf = gpd.GeoDataFrame(geometry=[buffered_poly], crs="EPSG:26971").to_crs("EPSG:4326")
    poly_4326 = buffered_gdf.geometry.iloc[0]

    # Download graph from polygon
    try:
        G = ox.graph_from_polygon(
            poly_4326,
            network_type=network_type,
            simplify=True,
            retain_all=False,
        )
        logger.info(f"Acquired graph from OSM: {len(G.nodes)} nodes, {len(G.edges)} edges.")
        logger.info(f"Caching graph to {dest}...")
        ox.save_graphml(G, dest)
        return G
    except Exception as e:
        logger.warning(f"OSMnx polygon acquisition failed ({e}). Attempting bounding box acquisition...")
        minx, miny, maxx, maxy = poly_4326.bounds
        # OSMnx 2.x bbox is (left, bottom, right, top)
        G = ox.graph_from_bbox(
            bbox=(minx, miny, maxx, maxy),
            network_type=network_type,
            simplify=True,
            retain_all=False,
        )
        logger.info(f"Acquired graph from bbox: {len(G.nodes)} nodes, {len(G.edges)} edges.")
        ox.save_graphml(G, dest)
        return G


def compute_facility_distances(
    origin_points: list[Point] | gpd.GeoSeries,
    facility_points: list[Point] | gpd.GeoSeries,
    graph: nx.MultiDiGraph | None = None,
    crs: str = "EPSG:26971",
) -> dict[str, Any]:
    """Compute shortest walking-network and Euclidean distances from origins to facilities.

    Uses reverse multi-source Dijkstra shortest-path computation:
        Let F be the set of nearest graph nodes for all facilities.
        On an undirected/bidirectional walkable street network, multi-source Dijkstra
        computes shortest distance from any origin node to the nearest facility node
        in a single efficient pass: O((|V| + |E|) log |V|).

    Parameters
    ----------
    origin_points : list[Point] | gpd.GeoSeries
        Representative origin points for census tracts in projected metric CRS.
    facility_points : list[Point] | gpd.GeoSeries
        Point locations of target amenities (libraries) in projected metric CRS.
    graph : nx.MultiDiGraph | None
        Walkable street network. If None, computes Euclidean distances only.
    crs : str
        Projected CRS with units in meters.

    Returns
    -------
    dict[str, Any]
        Dictionary with:
        - "network_distances_m": np.ndarray of network distances (or nan if unreachable)
        - "euclidean_distances_m": np.ndarray of straight-line distances
        - "origin_snap_distances_m": np.ndarray of origin-to-node snapping offsets
        - "facility_snap_distances_m": np.ndarray of facility-to-node snapping offsets
        - "unreachable_count": int count of disconnected origin tracts
    """
    orig_coords = np.array([(p.x, p.y) for p in origin_points], dtype=float)
    fac_coords = np.array([(p.x, p.y) for p in facility_points], dtype=float)

    n_origins = len(orig_coords)
    n_facilities = len(fac_coords)

    if n_facilities == 0:
        raise ValueError("Facility set is empty.")

    # 1. Straight-line (Euclidean) distance computation via KDTree (in meters)
    fac_tree = cKDTree(fac_coords)
    euclidean_dists, _nearest_fac_indices = fac_tree.query(orig_coords, k=1)

    if graph is None:
        logger.warning("No network graph provided; returning Euclidean distances.")
        return {
            "network_distances_m": euclidean_dists,
            "euclidean_distances_m": euclidean_dists,
            "origin_snap_distances_m": np.zeros(n_origins),
            "facility_snap_distances_m": np.zeros(n_facilities),
            "unreachable_count": 0,
        }

    # 2. Network distance computation
    # Convert graph to projected CRS if needed
    if not graph.graph.get("crs"):
        # Default OSMnx graph is WGS84
        G_proj = ox.project_graph(graph, to_crs=crs)
    elif str(graph.graph.get("crs")).lower() != crs.lower():
        G_proj = ox.project_graph(graph, to_crs=crs)
    else:
        G_proj = graph

    # Extract node coordinates for snapping
    node_ids = list(G_proj.nodes)
    node_coords = np.array([[G_proj.nodes[n]["x"], G_proj.nodes[n]["y"]] for n in node_ids])
    node_tree = cKDTree(node_coords)

    # Snap facilities to nearest graph nodes
    fac_node_dists, fac_node_indices = node_tree.query(fac_coords, k=1)
    fac_nodes = [node_ids[idx] for idx in fac_node_indices]

    # Snap origins to nearest graph nodes
    orig_node_dists, orig_node_indices = node_tree.query(orig_coords, k=1)
    orig_nodes = [node_ids[idx] for idx in orig_node_indices]

    # Convert to undirected graph for pedestrian walking routing
    try:
        G_undirected = G_proj.to_undirected()
    except Exception:
        G_undirected = ox.convert.to_undirected(G_proj)

    # Ensure length attribute exists on edges
    for u, v, d in G_undirected.edges(data=True):
        if "length" not in d:
            d["length"] = float(Point(node_coords[node_ids.index(u)]).distance(Point(node_coords[node_ids.index(v)])))

    # Efficient multi-source Dijkstra from all facility nodes
    logger.info(f"Computing multi-source shortest paths from {len(fac_nodes)} facility nodes...")
    dist_map = nx.multi_source_dijkstra_path_length(G_undirected, sources=fac_nodes, weight="length")

    network_dists = np.full(n_origins, fill_value=np.nan)
    unreachable = 0

    for i, orig_node in enumerate(orig_nodes):
        if orig_node in dist_map:
            # Total path = origin_snap_distance + shortest_network_path
            path_len = dist_map[orig_node]
            network_dists[i] = path_len + orig_node_dists[i]
        else:
            unreachable += 1
            # Fallback to Euclidean with circuity factor (standard urban walk circuity ~ 1.3)
            logger.warning(f"Origin tract {i} is disconnected from facility network component.")
            network_dists[i] = euclidean_dists[i] * 1.3

    logger.info(
        f"Shortest path computation complete: {n_origins - unreachable}/{n_origins} origins routed on graph. "
        f"Unreachable origins: {unreachable}."
    )

    return {
        "network_distances_m": network_dists,
        "euclidean_distances_m": euclidean_dists,
        "origin_snap_distances_m": orig_node_dists,
        "facility_snap_distances_m": fac_node_dists,
        "unreachable_count": unreachable,
    }
