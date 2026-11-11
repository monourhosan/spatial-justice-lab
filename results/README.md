# Empirical Results and Output Artifacts

This directory contains the computed outputs, publication figures, econometric tables, structured metrics, and interactive maps from the empirical pipeline.

## Deliverables Summary

- `metrics.json`: Full machine-readable manifest of computed statistical parameters, sample sizes, distance metrics, and regression results.
- `findings.md`: Scientific research report formatted for academic publication, reporting exact observed values, confidence intervals, and hypothesis tests.
- `interactive_chicago_map.html`: Interactive Folium map displaying tract-level poverty rates, library branch markers, and street layouts.

### Figures (`figures/`)
1. `fig01_poverty_rate_choropleth.png`: Spatial distribution of tract poverty rates ($q_i = B_i / U_i$) across Chicago.
2. `fig02_walking_distance_choropleth.png`: Shortest walking network distance to the nearest Chicago Public Library branch ($d_i$ in km).
3. `fig03_access_score_choropleth.png`: Modeled exponential accessibility score ($A_i = \exp(-d_i / 1000)$).
4. `fig04_poverty_vs_distance_scatter.png`: Nonparametric scatterplot and OLS fit of poverty rate vs. walking distance with 95% bootstrap CI.
5. `fig05_quintile_disparity_contrast.png`: Population-weighted accessibility comparison between the lowest (Q1) and highest (Q5) poverty quintiles.
6. `fig06_weighted_lorenz_curve.png`: Population-weighted Lorenz curve illustrating inequality in library accessibility ($G_A = 0.301$).
7. `fig07_spatial_disadvantage_map.png`: Spatial disadvantage prioritization score map ($S_i = q_i (1 - A_i)$).
8. `fig08_facility_simulation_map.png`: Hypothetical optimal location simulation for one additional library branch under an equity-weighted objective.

### Tables (`tables/`)
- `chicago_tract_level_metrics.csv`: Tract-by-tract dataset with 778 populated Chicago tracts, containing GEOID, total population, poverty universe, poverty count, poverty rate, median household income, population density, walking distance, Euclidean distance, access scores, and spatial disadvantage indices.
- `regression_coefficients.csv`: Full OLS regression results with White / HC1 heteroskedasticity-consistent standard errors, t-statistics, p-values, and 95% confidence intervals.
