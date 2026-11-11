"""Unit tests for network routing, Dijkstra shortest paths, and snapping diagnostics."""

import networkx as nx
import numpy as np
import pytest
from shapely.geometry import Point

from spatial_justice.routing import compute_facility_distances


def test_routing_known_synthetic_graph():
    """Create a synthetic L-shaped street graph with known lengths:

    Node 0: (0, 0)
    Node 1: (300, 0)     -- edge length = 300
    Node 2: (300, 400)   -- edge length = 400

    Network distance between Node 0 and Node 2 = 300 + 400 = 700.
    Euclidean distance between (0, 0) and (300, 400) = sqrt(300^2 + 400^2) = 500.
    """
    G = nx.MultiDiGraph()
    G.graph["crs"] = "EPSG:26971"

    G.add_node(0, x=0.0, y=0.0)
    G.add_node(1, x=300.0, y=0.0)
    G.add_node(2, x=300.0, y=400.0)

    # Add bidirectional edges
    G.add_edge(0, 1, length=300.0)
    G.add_edge(1, 0, length=300.0)
    G.add_edge(1, 2, length=400.0)
    G.add_edge(2, 1, length=400.0)

    origin = [Point(0.0, 0.0)]
    facility = [Point(300.0, 400.0)]

    results = compute_facility_distances(origin, facility, graph=G, crs="EPSG:26971")

    # Euclidean distance must be 500
    assert np.isclose(results["euclidean_distances_m"][0], 500.0)

    # Network distance must be 700
    assert np.isclose(results["network_distances_m"][0], 700.0)

    # Verification: Network distance strictly exceeds Euclidean distance on L-shape
    assert results["network_distances_m"][0] > results["euclidean_distances_m"][0]
    assert results["origin_snap_distances_m"][0] == 0.0
    assert results["facility_snap_distances_m"][0] == 0.0
    assert results["unreachable_count"] == 0


def test_routing_multi_facility():
    """Test that multi-source Dijkstra finds the closest facility among several."""
    G = nx.MultiDiGraph()
    G.graph["crs"] = "EPSG:26971"

    # Line of nodes: 0 - 1 - 2 - 3, each spaced by 100m
    for i in range(4):
        G.add_node(i, x=float(i * 100), y=0.0)
    for i in range(3):
        G.add_edge(i, i + 1, length=100.0)
        G.add_edge(i + 1, i, length=100.0)

    # Origin at Node 1 (x=100)
    origin = [Point(100.0, 0.0)]
    # Facilities at Node 0 (x=0, dist=100) and Node 3 (x=300, dist=200)
    facilities = [Point(0.0, 0.0), Point(300.0, 0.0)]

    res = compute_facility_distances(origin, facilities, graph=G, crs="EPSG:26971")
    # Closest is Node 0 at 100m
    assert np.isclose(res["network_distances_m"][0], 100.0)


def test_routing_empty_facilities_raises():
    origin = [Point(0.0, 0.0)]
    with pytest.raises(ValueError, match="Facility set is empty"):
        compute_facility_distances(origin, [], graph=None)
