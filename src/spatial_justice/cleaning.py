"""Data cleaning, schema standardization, and validation module.

Cleans and validates:
1. Chicago Public Library branch locations (coordinates, deduplication, bounding filter)
2. Census demographic counts (sentinel values, universe checks, poverty rates)
3. Municipal boundary geometries (validity, projection)
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
from shapely.geometry import Point
from shapely.validation import make_valid

from spatial_justice.mathematics import compute_poverty_rate

logger = logging.getLogger(__name__)

# Chicago metropolitan geographic bounding box safeguards
LAT_MIN, LAT_MAX = 41.60, 42.10
LON_MIN, LON_MAX = -88.00, -87.45

# Census sentinel missing value thresholds
CENSUS_SENTINELS = {-666666666, -888888888, -999999999, -555555555}


def clean_chicago_libraries(
    raw_json_path: Path | str,
    target_crs: str = "EPSG:26971",
    boundary_gdf: gpd.GeoDataFrame | None = None,
) -> gpd.GeoDataFrame:
    """Clean, geocode, and validate Chicago Public Library locations.

    Parameters
    ----------
    raw_json_path : Path | str
        Path to the downloaded library locations JSON.
    target_crs : str
        Target projected metric CRS (default EPSG:26971, Illinois East meters).
    boundary_gdf : gpd.GeoDataFrame | None
        Optional city boundary to verify spatial coverage.

    Returns
    -------
    gpd.GeoDataFrame
        Validated library branches with point geometries in target_crs.
    """
    path = Path(raw_json_path)
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    logger.info(f"Loaded {len(data)} raw library records from {path}")
    cleaned_rows = []

    for item in data:
        branch = item.get("branch_", item.get("name", "Unknown Branch")).strip()
        address = item.get("address", "").strip()
        zip_code = item.get("zip", "").strip()

        loc = item.get("location", {})
        if not loc or not isinstance(loc, dict):
            logger.warning(f"Excluding library '{branch}': missing location object.")
            continue

        lat_val = loc.get("latitude")
        lon_val = loc.get("longitude")
        if lat_val is None or lon_val is None:
            logger.warning(f"Excluding library '{branch}': null coordinates.")
            continue

        try:
            lat = float(lat_val)
            lon = float(lon_val)
        except (ValueError, TypeError):
            logger.warning(f"Excluding library '{branch}': non-numeric coordinates ({lat_val}, {lon_val}).")
            continue

        # Spatial sanity check
        if not (LAT_MIN <= lat <= LAT_MAX and LON_MIN <= lon <= LON_MAX):
            logger.warning(f"Excluding library '{branch}': coordinates ({lat}, {lon}) outside Chicago region.")
            continue

        cleaned_rows.append(
            {
                "branch_name": branch,
                "address": address,
                "zip_code": zip_code,
                "latitude": lat,
                "longitude": lon,
                "geometry": Point(lon, lat),
            }
        )

    df = pd.DataFrame(cleaned_rows)
    # Deduplicate by coordinates and branch name
    initial_len = len(df)
    df = df.drop_duplicates(subset=["latitude", "longitude"])
    df = df.drop_duplicates(subset=["branch_name"])
    if len(df) < initial_len:
        logger.info(f"Removed {initial_len - len(df)} duplicate library entries.")

    gdf = gpd.GeoDataFrame(df, geometry="geometry", crs="EPSG:4326")
    gdf_proj = gdf.to_crs(target_crs)

    if boundary_gdf is not None:
        boundary_union = boundary_gdf.to_crs(target_crs).unary_union
        # Keep libraries within 500m buffer of city boundary to ensure border coverage
        buffered_boundary = boundary_union.buffer(500.0)
        within_mask = gdf_proj.geometry.intersects(buffered_boundary)
        excluded_count = int((~within_mask).sum())
        if excluded_count > 0:
            logger.info(f"Excluded {excluded_count} libraries beyond municipal buffer.")
        gdf_proj = gdf_proj[within_mask].reset_index(drop=True)

    logger.info(f"Cleaned libraries count: {len(gdf_proj)} valid facilities in {target_crs}.")
    return gdf_proj


def clean_census_demographics(df: pd.DataFrame) -> pd.DataFrame:
    """Standardize, clean, and validate ACS demographic variables.

    Parameters
    ----------
    df : pd.DataFrame
        Raw or merged ACS DataFrame.

    Returns
    -------
    pd.DataFrame
        Cleaned DataFrame with numeric counts, sentinel values resolved to NaN,
        and validated poverty rates.
    """
    clean_df = df.copy()

    # Ensure GEOID is 11-digit zero-padded string
    clean_df["GEOID"] = clean_df["GEOID"].astype(str).str.strip().str.zfill(11)

    numeric_cols = [
        "B01003_001E",
        "B01003_001M",
        "B17001_001E",
        "B17001_001M",
        "B17001_002E",
        "B17001_002M",
        "B19013_001E",
        "B19013_001M",
    ]

    for col in numeric_cols:
        if col in clean_df.columns:
            clean_df[col] = pd.to_numeric(clean_df[col], errors="coerce")
            # Replace Census sentinels with NaN
            clean_df.loc[clean_df[col].isin(CENSUS_SENTINELS), col] = np.nan
            clean_df.loc[clean_df[col] < 0, col] = np.nan

    # Population and poverty universe validation
    universe = clean_df["B17001_001E"].values
    poverty = clean_df["B17001_002E"].values

    # Guard: b_i <= u_i
    invalid_mask = (poverty > universe) & ~np.isnan(poverty) & ~np.isnan(universe)
    if np.any(invalid_mask):
        logger.warning(
            f"Found {int(invalid_mask.sum())} tracts where B_i > U_i. Capping B_i at U_i."
        )
        clean_df.loc[invalid_mask, "B17001_002E"] = clean_df.loc[invalid_mask, "B17001_001E"]
        poverty = clean_df["B17001_002E"].values

    # Compute poverty rate q_i
    clean_df["poverty_rate"] = compute_poverty_rate(poverty, universe)
    clean_df["total_population"] = clean_df["B01003_001E"]
    clean_df["poverty_universe"] = clean_df["B17001_001E"]
    clean_df["poverty_count"] = clean_df["B17001_002E"]
    clean_df["median_income"] = clean_df["B19013_001E"]

    # Flag unpopulated tracts (e.g., airports, industrial zones, parks, water)
    clean_df["is_unpopulated"] = (clean_df["total_population"].fillna(0) == 0) | (
        clean_df["poverty_universe"].fillna(0) == 0
    )

    logger.info(
        f"Cleaned demographics: {len(clean_df)} tracts. "
        f"Unpopulated/zero-universe tracts: {int(clean_df['is_unpopulated'].sum())}"
    )
    return clean_df


def clean_chicago_boundary(
    raw_geojson_path: Path | str,
    target_crs: str = "EPSG:26971",
) -> gpd.GeoDataFrame:
    """Load, validate, and reproject Chicago municipal boundary polygon."""
    path = Path(raw_geojson_path)
    gdf = gpd.read_file(path)

    # Validate geometries
    gdf["geometry"] = gdf["geometry"].apply(make_valid)
    gdf_proj = gdf.to_crs(target_crs)
    logger.info(f"Loaded boundary from {path}. CRS: {gdf_proj.crs}. Total features: {len(gdf_proj)}")
    return gdf_proj
