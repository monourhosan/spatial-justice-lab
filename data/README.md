# Data Directory Structure and Provenance

This directory stores raw, processed, and metadata assets for the Chicago spatial access research project.

## Directory Layout

- `metadata/`: Contains machine-readable `datasets.yml` recording download URLs, checksums, licenses, schemas, and limitations.
- `raw/`: Stores pristine downloaded artifacts from original government and OpenStreetMap servers. Ignored by git to avoid committing multi-megabyte binaries.
- `processed/`: Stores cleaned, projected, joined GeoDataFrames and tract-level metrics tables.
- `sample/`: Contains tiny synthetic test fixtures for offline pipeline verification and automated CI tests.

## Data Acquisition Rules

1. All primary empirical datasets are obtained directly from official governmental APIs/servers (U.S. Census Bureau and City of Chicago Data Portal) or OpenStreetMap.
2. No proprietary, commercial, or unverified secondary data files are used.
3. No credentials (such as `CENSUS_API_KEY`) are committed or written into logs.
4. Large downloads are cached in `data/raw/` so repeated pipeline runs do not flood external public services.
