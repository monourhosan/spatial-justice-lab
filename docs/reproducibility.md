# Reproducibility Guide

This guide provides instructions to reproduce the complete empirical study, mathematical tests, figures, and research findings from scratch on Windows, macOS, or Linux.

---

## 1. Prerequisites

- **Python:** Version 3.11 or 3.12 (tested and certified on Python 3.12.10).
- **Git:** Version 2.40+ (portable MinGit or system Git).
- **Disk Space:** ~200 MB for raw cached datasets and network graphs.
- **Operating System:** Platform-agnostic (Windows 10/11, macOS, Ubuntu/Debian).

---

## 2. Environment Setup

### Step 2.1: Clone or Enter Repository
```bash
git clone https://github.com/placeholder/spatial-justice-mathematical-model.git
cd spatial-justice-mathematical-model
```

### Step 2.2: Create and Activate Virtual Environment
```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# macOS / Linux
python3 -m venv .venv
source .venv/bin/activate
```

### Step 2.3: Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
pip install -e . --no-deps
```

---

## 3. Configuration and API Keys (Optional)

Copy the example environment configuration:
```bash
cp .env.example .env
```

*Note on Census API Keys:*
A Census API key is **not required** to reproduce the findings. When `CENSUS_API_KEY` is omitted, the pipeline automatically streams official Census Bureau ACS 5-Year summary data directly from `www2.census.gov`. If you wish to use an authenticated API key, obtain one freely at [https://api.census.gov/data/key_signup.html](https://api.census.gov/data/key_signup.html) and add it to `.env`:
```ini
CENSUS_API_KEY=your_key_here
```

---

## 4. Execution Commands

### 4.1 Run Unit Tests (Offline Verification)
To verify all mathematical formulas, routing algorithms, and schema parsers:
```bash
pytest tests/
```
*Expected result:* 16 tests pass in < 5 seconds.

### 4.2 Run Offline Synthetic Smoke Test
To verify the complete pipeline end-to-end without downloading external data:
```bash
python -m spatial_justice.pipeline --synthetic
```
*Expected result:* Pipeline completes in < 1 second and outputs synthetic metrics to `results/metrics.json`.

### 4.3 Run Full Empirical Pipeline on Real Chicago Data
To acquire official datasets, build the street network, compute walking distances, fit regressions, and generate publication figures:
```bash
python -m spatial_justice.pipeline --config configs/chicago.yaml
```

### 4.4 Run Specific Sub-Tasks
```bash
# Download and cache raw datasets only:
python -m spatial_justice.pipeline --download-only

# Run analysis using existing cached datasets:
python -m spatial_justice.pipeline --analyze-only

# Run in strict offline mode (refuses network requests):
python -m spatial_justice.pipeline --offline
```

---

## 5. Generated Artifacts Verification

After executing the empirical pipeline, verify that the following files exist in `results/`:

| Artifact Path | Description | Expected Size / Format |
|---|---|---|
| `results/metrics.json` | Complete structured empirical parameters | ~4.7 KB JSON |
| `results/findings.md` | Full academic results report | ~6.7 KB Markdown |
| `results/interactive_chicago_map.html` | Interactive web map | ~3.7 MB HTML |
| `results/figures/fig01_poverty_rate_choropleth.png` | Poverty rate choropleth | ~490 KB PNG |
| `results/figures/fig02_walking_distance_choropleth.png` | Walking distance choropleth | ~535 KB PNG |
| `results/figures/fig03_access_score_choropleth.png` | Accessibility score choropleth | ~500 KB PNG |
| `results/figures/fig04_poverty_vs_distance_scatter.png` | Scatter association plot | ~466 KB PNG |
| `results/figures/fig05_quintile_disparity_contrast.png` | Quintile disparity bar chart | ~120 KB PNG |
| `results/figures/fig06_weighted_lorenz_curve.png` | Population-weighted Lorenz curve | ~200 KB PNG |
| `results/figures/fig07_spatial_disadvantage_map.png` | Prioritization index map | ~554 KB PNG |
| `results/figures/fig08_facility_simulation_map.png` | Optimal site simulation map | ~561 KB PNG |
| `results/tables/chicago_tract_level_metrics.csv` | 778-tract analysis dataset | ~125 KB CSV |
| `results/tables/regression_coefficients.csv` | OLS regression parameters | ~590 bytes CSV |
