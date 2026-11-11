# Data Sources and Provenance Manifest

This document records the exact provenance, licensing, coverage vintages, schemas, and known limitations for all external public datasets utilized in this research.

---

## 1. Primary Empirical Data Sources

### 1.1 City of Chicago: Public Library Locations
- **Dataset Identifier:** `x8fc-8rcq`
- **Publisher:** City of Chicago / Chicago Public Library (CPL)
- **Canonical Landing Page:** [https://data.cityofchicago.org/d/x8fc-8rcq](https://data.cityofchicago.org/d/x8fc-8rcq)
- **Direct Resource Endpoint:** `https://data.cityofchicago.org/resource/x8fc-8rcq.json`
- **Retrieval Date (UTC):** 2026-11-11
- **Vintage:** Official current municipal inventory
- **Geographic Extent:** City of Chicago corporate boundaries
- **License / Terms:** City of Chicago Open Data Terms of Use (Public Domain equivalent)
- **Attribution:** "Data provided by the City of Chicago via the Chicago Data Portal."
- **Record Count:** 82 library branches
- **Key Columns:**
  - `branch_`: Official branch name (e.g., Harold Washington Library Center, Albany Park)
  - `address`: Street address
  - `city`: Chicago
  - `state`: IL
  - `zip`: 5-digit postal code
  - `location`: Coordinates dictionary with `latitude` and `longitude`
- **Known Limitations:** Provides building centroid coordinates rather than designated public entry doorways or ADA-compliant wheelchair access ramps.

---

### 1.2 City of Chicago: Municipal Boundary
- **Dataset Identifier:** `qqq8-j68g`
- **Publisher:** City of Chicago, Department of Planning and Development
- **Canonical Landing Page:** [https://data.cityofchicago.org/d/qqq8-j68g](https://data.cityofchicago.org/d/qqq8-j68g)
- **Direct Resource Endpoint:** `https://data.cityofchicago.org/resource/qqq8-j68g.geojson`
- **Retrieval Date (UTC):** 2026-11-11
- **Vintage:** Current official municipal boundary
- **Geographic Extent:** Corporate municipal boundary of Chicago
- **License / Terms:** City of Chicago Open Data Terms of Use
- **Attribution:** "Data provided by the City of Chicago."
- **Key Columns:** `name`, `objectid`, `geometry` (MultiPolygon in EPSG:4326)
- **Known Limitations:** Represents administrative jurisdictional limits, including the narrow corridor connecting the O'Hare International Airport enclave.

---

### 1.3 U.S. Census Bureau: 2023 TIGER/Line Shapefiles (Census Tracts)
- **Publisher:** U.S. Department of Commerce, U.S. Census Bureau Geography Division
- **Canonical Landing Page:** [https://www.census.gov/geographies/mapping-files/time-series/geo/tiger-line-file.2023.html](https://www.census.gov/geographies/mapping-files/time-series/geo/tiger-line-file.2023.html)
- **Download URL:** `https://www2.census.gov/geo/tiger/TIGER2023/TRACT/tl_2023_17_tract.zip`
- **Retrieval Date (UTC):** 2026-11-11
- **Vintage:** 2023 TIGER/Line Release (2020 Census statistical tract boundaries)
- **Geographic Extent:** State of Illinois (State FIPS 17), filtered to Cook County (County FIPS 031)
- **License / Terms:** U.S. Government Work / Public Domain
- **Attribution:** "U.S. Census Bureau 2023 TIGER/Line Shapefiles."
- **Record Count:** 1,332 Cook County tracts (781 tracts inside Chicago municipal footprint)
- **Key Columns:**
  - `STATEFP`: State FIPS code (`17`)
  - `COUNTYFP`: County FIPS code (`031`)
  - `TRACTCE`: 6-digit Census tract code
  - `GEOID`: Full 11-digit FIPS code (`17031xxxxxx`)
  - `ALAND`: Land area in square meters
  - `AWATER`: Water area in square meters
  - `geometry`: Polygon / MultiPolygon in NAD83 (EPSG:4269)
- **Known Limitations:** Statistical boundaries delineated for decennial data collection; internal population may be distributed heterogeneously.

---

### 1.4 U.S. Census Bureau: 2019–2023 American Community Survey (ACS) 5-Year Estimates
- **Publisher:** U.S. Department of Commerce, U.S. Census Bureau
- **Canonical Landing Page:** [https://www.census.gov/programs-surveys/acs/](https://www.census.gov/programs-surveys/acs/)
- **Summary File Endpoint:** `https://www2.census.gov/programs-surveys/acs/summary_file/2023/table-based-SF/data/5YRData/`
- **API Endpoint:** `https://api.census.gov/data/2023/acs/acs5`
- **Retrieval Date (UTC):** 2026-11-11
- **Vintage:** 2019–2023 5-Year Detailed Estimates (60-month pooled period)
- **Geographic Extent:** Cook County, Illinois census tracts
- **License / Terms:** U.S. Government Work / Public Domain
- **Attribution:** "U.S. Census Bureau, 2019-2023 American Community Survey 5-Year Period Estimates."
- **Key Detailed Tables:**
  - `B01003_001E` / `B01003_001M`: Total population estimate and margin of error
  - `B17001_001E` / `B17001_001M`: Poverty status determination universe estimate and margin of error
  - `B17001_002E` / `B17001_002M`: Count of persons below federal poverty threshold and margin of error
  - `B19013_001E` / `B19013_001M`: Median household income in past 12 months (inflation-adjusted 2023 dollars)
- **Known Limitations:** Subject to sampling error and period-estimate smoothing. Margins of error are explicitly incorporated into Monte Carlo sensitivity checks.

---

### 1.5 OpenStreetMap / Census TIGER Walkable Pedestrian Network
- **Publishers:** OpenStreetMap Contributors & U.S. Census Bureau Geography Division
- **Network Extent:** Chicago municipal boundary + 500-meter pedestrian buffer
- **Local Storage:** `data/raw/chicago_walk.graphml` (37.2 MB, 88,549 nodes, 260,982 edges)
- **License:** Open Data Commons Open Database License (ODbL) 1.0 (OSM) / Public Domain (Census)
- **Attribution:** "© OpenStreetMap contributors and U.S. Census Bureau."
- **Filtering Rule:** Planarized road network excluding non-walkable limited-access freeways (Interstates / MTFCC `S1100`).
- **Edge Attributes:** Physical distance in meters projected to EPSG:26971.
- **Known Limitations:** Does not account for dynamic traffic signal timing, temporary sidewalk construction closures, or physical micro-topographical barriers (e.g. curb cuts, steep viaduct stairs).
