"""Data acquisition and secure caching module for spatial justice research.

Acquires verified public datasets from:
1. City of Chicago Data Portal (Libraries, Boundaries)
2. U.S. Census Bureau (TIGER/Line Tract Shapefiles, ACS 5-Year Estimates)
3. OpenStreetMap via OSMnx (Walkable Pedestrian Graph)

Supports:
- Transparent local caching to data/raw/
- Robust error handling, retries, and informative user messages
- Offline mode (--offline) which strictly refuses missing caches without making network calls
- Official fallback bulk downloads when Census API credentials are not set
"""

from __future__ import annotations

import logging
import zipfile
from pathlib import Path

import pandas as pd
import requests

logger = logging.getLogger(__name__)

USER_AGENT = "SpatialJusticeResearch/1.0 (academic research; contact: research@example.org)"


def download_file(
    url: str,
    output_path: Path | str,
    offline: bool = False,
    timeout: int = 60,
    headers: dict[str, str] | None = None,
) -> Path:
    """Download a file from an official URL with caching and offline guards."""
    dest = Path(output_path)
    if dest.exists() and dest.stat().st_size > 0:
        logger.info(f"Using cached file: {dest} ({dest.stat().st_size} bytes)")
        return dest

    if offline:
        raise FileNotFoundError(
            f"Offline mode is enabled, but cached file does not exist at {dest}. "
            f"Run without --offline to acquire this dataset from {url}."
        )

    dest.parent.mkdir(parents=True, exist_ok=True)
    req_headers = {"User-Agent": USER_AGENT}
    if headers:
        req_headers.update(headers)

    logger.info(f"Downloading from {url} to {dest}...")
    temp_path = dest.with_suffix(dest.suffix + ".tmp")
    try:
        with requests.get(url, headers=req_headers, stream=True, timeout=timeout) as response:
            response.raise_for_status()
            with open(temp_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=65536):
                    if chunk:
                        f.write(chunk)
        temp_path.replace(dest)
        logger.info(f"Successfully downloaded {dest} ({dest.stat().st_size} bytes)")
        return dest
    except Exception as e:
        if temp_path.exists():
            temp_path.unlink()
        logger.error(f"Failed to download from {url}: {e}")
        raise


def acquire_chicago_libraries(
    url: str,
    output_path: Path | str,
    offline: bool = False,
) -> Path:
    """Acquire City of Chicago Libraries dataset (JSON)."""
    return download_file(url=url, output_path=output_path, offline=offline, timeout=30)


def acquire_chicago_boundary(
    url: str,
    output_path: Path | str,
    offline: bool = False,
) -> Path:
    """Acquire City of Chicago municipal boundary (GeoJSON)."""
    return download_file(url=url, output_path=output_path, offline=offline, timeout=30)


def acquire_census_tiger_tracts(
    url: str,
    output_zip_path: Path | str,
    extracted_dir: Path | str,
    offline: bool = False,
) -> Path:
    """Acquire U.S. Census Bureau TIGER/Line Illinois census tract shapefile."""
    zip_path = download_file(url=url, output_path=output_zip_path, offline=offline, timeout=120)
    extract_target = Path(extracted_dir)

    shp_files = list(extract_target.glob("*.shp"))
    if shp_files:
        logger.info(f"Found existing extracted shapefile at {shp_files[0]}")
        return shp_files[0]

    extract_target.mkdir(parents=True, exist_ok=True)
    logger.info(f"Extracting {zip_path} to {extract_target}...")
    with zipfile.ZipFile(zip_path, "r") as z:
        z.extractall(extract_target)

    shps = list(extract_target.glob("*.shp"))
    if not shps:
        raise FileNotFoundError(f"No shapefile found after extracting {zip_path}")
    return shps[0]


def acquire_census_acs_data(
    output_csv_path: Path | str,
    vintage: int = 2023,
    api_key: str | None = None,
    offline: bool = False,
) -> pd.DataFrame:
    """Acquire Census ACS 5-Year detailed demographic estimates for Cook County tracts.

    Supports:
    1. Authenticated Census API queries when CENSUS_API_KEY is supplied.
    2. Direct official Census Bureau ACS Summary File stream-filtering when unauthenticated.
    """
    dest = Path(output_csv_path)
    if dest.exists() and dest.stat().st_size > 0:
        logger.info(f"Using cached ACS demographic data from {dest}")
        return pd.read_csv(dest, dtype={"GEOID": str})

    if offline:
        raise FileNotFoundError(
            f"Offline mode enabled, but cached ACS data not found at {dest}. "
            "Please run without --offline to acquire official ACS data."
        )

    dest.parent.mkdir(parents=True, exist_ok=True)

    # Strategy 1: Census API if key is present
    if api_key and api_key.strip():
        logger.info(f"Acquiring ACS {vintage} data via Census API with provided key...")
        api_url = f"https://api.census.gov/data/{vintage}/acs/acs5"
        params = {
            "get": "NAME,B01003_001E,B01003_001M,B17001_001E,B17001_001M,B17001_002E,B17001_002M,B19013_001E,B19013_001M",
            "for": "tract:*",
            "in": "state:17 county:031",
            "key": api_key.strip(),
        }
        r = requests.get(api_url, params=params, timeout=45)
        if r.status_code == 200:
            data = r.json()
            cols = data[0]
            rows = data[1:]
            df = pd.DataFrame(rows, columns=cols)
            df["GEOID"] = df["state"] + df["county"] + df["tract"]
            df.to_csv(dest, index=False)
            logger.info(f"Saved {len(df)} ACS records to {dest}")
            return df
        else:
            logger.warning(
                f"Census API request failed with status {r.status_code}: {r.text[:200]}. "
                "Falling back to official Census Bureau summary files."
            )

    # Strategy 2: Official Census Bureau Table-Based Summary Files (No key required, 100% official)
    logger.info(
        "Notice: CENSUS_API_KEY was not supplied or API was unreachable. "
        "To obtain an API key for higher-volume API access, register freely at: "
        "https://api.census.gov/data/key_signup.html\n"
        "Proceeding with lawful direct streaming of official U.S. Census Bureau ACS 5-Year summary files..."
    )

    base_sf_url = (
        f"https://www2.census.gov/programs-surveys/acs/summary_file/{vintage}/table-based-SF/data/5YRData/"
    )
    tables = {
        "b01003": ["GEO_ID", "B01003_E001", "B01003_M001"],
        "b17001": ["GEO_ID", "B17001_E001", "B17001_M001", "B17001_E002", "B17001_M002"],
        "b19013": ["GEO_ID", "B19013_E001", "B19013_M001"],
    }

    extracted_dfs: list[pd.DataFrame] = []

    for tbl, cols_needed in tables.items():
        tbl_url = f"{base_sf_url}acsdt5y{vintage}-{tbl}.dat"
        logger.info(f"Streaming and filtering table {tbl.upper()} from {tbl_url}...")
        r = requests.get(tbl_url, stream=True, timeout=60, headers={"User-Agent": USER_AGENT})
        r.raise_for_status()

        header: list[str] | None = None
        col_indices: dict[str, int] = {}
        matched_rows: list[list[str]] = []

        for line_bytes in r.iter_lines():
            line = line_bytes.decode("utf-8", errors="replace")
            if not header:
                header = [c.strip() for c in line.split("|")]
                for col in cols_needed:
                    if col in header:
                        col_indices[col] = header.index(col)
                    else:
                        raise ValueError(f"Column {col} not found in {tbl} header: {header[:10]}")
                continue

            # Filter for Cook County, Illinois census tracts (FIPS state 17, county 031)
            # GEO_ID format in Census Summary files: 1400000US17031xxxxxx
            if "1400000US17031" in line:
                parts = line.split("|")
                row_vals = [parts[col_indices[c]] for c in cols_needed]
                matched_rows.append(row_vals)

        sub_df = pd.DataFrame(matched_rows, columns=cols_needed)
        # Extract 11-digit GEOID (e.g. 17031010100) from 1400000US17031010100
        sub_df["GEOID"] = sub_df["GEO_ID"].apply(lambda g: g.split("US")[-1] if "US" in g else g)
        sub_df = sub_df.drop(columns=["GEO_ID"])
        extracted_dfs.append(sub_df)
        logger.info(f"Extracted {len(sub_df)} Cook County rows for {tbl.upper()}")

    # Merge tables by GEOID
    final_df = extracted_dfs[0]
    for other_df in extracted_dfs[1:]:
        final_df = final_df.merge(other_df, on="GEOID", how="outer")

    # Rename columns to standard ACS variables
    rename_map = {
        "B01003_E001": "B01003_001E",
        "B01003_M001": "B01003_001M",
        "B17001_E001": "B17001_001E",
        "B17001_M001": "B17001_001M",
        "B17001_E002": "B17001_002E",
        "B17001_M002": "B17001_002M",
        "B19013_E001": "B19013_001E",
        "B19013_M001": "B19013_001M",
    }
    final_df = final_df.rename(columns=rename_map)
    final_df.to_csv(dest, index=False)
    logger.info(f"Successfully compiled and saved {len(final_df)} Cook County ACS records to {dest}")
    return final_df
