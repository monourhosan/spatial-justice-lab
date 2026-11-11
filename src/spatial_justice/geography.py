"""Geographic spatial processing, boundary containment, and origin proxies module.

Implements:
1. Reprojection to metric coordinate reference systems (EPSG:26971)
2. Tract filtering for Cook County and Chicago municipal footprint
3. Documented representative origins (representative_point) vs centroids
4. Population density calculations (P_i / area_km2)
5. Robust spatial joins on 11-digit GEOID
"""

from __future__ import annotations

import logging
from pathlib import Path

import geopandas as gpd
import pandas as pd
from shapely.validation import make_valid

logger = logging.getLogger(__name__)


def prepare_chicago_tracts(
    tiger_shp_path: Path | str,
    demographics_df: pd.DataFrame,
    boundary_gdf: gpd.GeoDataFrame,
    target_crs: str = "EPSG:26971",
    inclusion_rule: str = "representative_point",
) -> gpd.GeoDataFrame:
    """Filter, reproject, join, and bound Chicago census tracts.

    Parameters
    ----------
    tiger_shp_path : Path | str
        Path to Illinois TIGER/Line tracts shapefile.
    demographics_df : pd.DataFrame
        Cleaned ACS demographic DataFrame containing GEOID and poverty attributes.
    boundary_gdf : gpd.GeoDataFrame
        City of Chicago municipal boundary GeoDataFrame.
    target_crs : str
        Target metric projected CRS (default EPSG:26971).
    inclusion_rule : str
        Rule to identify tracts within Chicago:
        - "representative_point": tract representative point is within city boundary (primary).
        - "centroid": tract centroid is within city boundary.
        - "intersection": tract polygon intersects city boundary with >= 10% area overlap.

    Returns
    -------
    gpd.GeoDataFrame
        Final analysis GeoDataFrame with geometries, representative points, areas,
        and demographic indicators.
    """
    logger.info(f"Loading Illinois TIGER tracts from {tiger_shp_path}...")
    il_tracts = gpd.read_file(tiger_shp_path)

    # Filter to Cook County (FIPS 031)
    cook_tracts = il_tracts[il_tracts["COUNTYFP"] == "031"].copy()
    logger.info(f"Extracted {len(cook_tracts)} Cook County tracts from Illinois TIGER file.")

    # Fix geometry topology and reproject
    cook_tracts["geometry"] = cook_tracts["geometry"].apply(make_valid)
    cook_tracts = cook_tracts.to_crs(target_crs)
    boundary_proj = boundary_gdf.to_crs(target_crs)
    city_polygon = boundary_proj.unary_union

    # Compute areas and origin representations in metric units (meters)
    cook_tracts["area_m2"] = cook_tracts.geometry.area
    cook_tracts["area_km2"] = cook_tracts["area_m2"] / 1e6
    cook_tracts["representative_point"] = cook_tracts.geometry.representative_point()
    cook_tracts["centroid"] = cook_tracts.geometry.centroid

    # Standardize GEOID
    cook_tracts["GEOID"] = cook_tracts["GEOID"].astype(str).str.strip().str.zfill(11)

    # Determine municipal boundary inclusion
    if inclusion_rule == "representative_point":
        in_city = cook_tracts["representative_point"].within(city_polygon)
    elif inclusion_rule == "centroid":
        in_city = cook_tracts["centroid"].within(city_polygon)
    elif inclusion_rule == "intersection":
        # At least 10% of tract area within city boundary to exclude trivial border slivers
        intersections = cook_tracts.geometry.intersection(city_polygon)
        overlap_ratio = intersections.area / cook_tracts["area_m2"]
        in_city = overlap_ratio >= 0.10
    else:
        raise ValueError(f"Unknown inclusion_rule: {inclusion_rule}")

    chicago_tracts = cook_tracts[in_city].copy().reset_index(drop=True)
    logger.info(
        f"Inclusion rule '{inclusion_rule}': identified {len(chicago_tracts)} tracts inside Chicago "
        f"out of {len(cook_tracts)} Cook County tracts."
    )

    # Join with ACS demographics
    merged = chicago_tracts.merge(demographics_df, on="GEOID", how="left")
    missing_demo = merged["total_population"].isna().sum()
    if missing_demo > 0:
        logger.warning(f"{missing_demo} tracts lacked corresponding demographic records.")

    # Compute population density: P_i / area_km2
    merged["pop_density_km2"] = merged["total_population"].fillna(0) / merged["area_km2"]

    # Record boundary diagnostics
    border_tracts = merged.geometry.boundary.intersects(city_polygon.boundary)
    merged["is_border_tract"] = border_tracts
    logger.info(f"Border tracts count: {int(border_tracts.sum())}")

    # Set primary origin point geometry column
    merged["origin_point"] = merged["representative_point"]

    return merged
