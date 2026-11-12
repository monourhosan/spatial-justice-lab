# Empirical Results and Output Artifacts

This directory contains the computed outputs, publication figures, econometric tables, structured metrics, and interactive maps from the empirical pipeline.

## Deliverables Summary

### Chicago Primary Study
- `metrics.json`: Full machine-readable manifest of computed statistical parameters, sample sizes, distance metrics, and regression results for Chicago.
- `findings.md`: Scientific research report formatted for academic publication, reporting exact observed values, confidence intervals, and hypothesis tests for Chicago.
- `interactive_chicago_map.html`: Interactive Folium map displaying Chicago tract-level poverty rates, library branch markers, and street layouts.

### Cross-City Validation (Washington, D.C.)
- `cross_city_comparison.json`: Structured comparison of sample demographics, out-of-sample predictive accuracy metrics, and econometric parameter estimates between Chicago and Washington, D.C.
- `cross_city_findings.md`: Full cross-city scientific findings report detailing model accuracy, transferability, structural replication, and theoretical conclusions.
- `interactive_dc_map.html`: Interactive Folium map displaying Washington, D.C. tract-level poverty rates and DC Public Library branch locations.

### Figures (`figures/`)
#### Chicago Primary Analysis
1. `fig01_poverty_rate_choropleth.png`: Spatial distribution of tract poverty rates ($q_i = B_i / U_i$) across Chicago.
2. `fig02_walking_distance_choropleth.png`: Shortest walking network distance to the nearest Chicago Public Library branch ($d_i$ in km).
3. `fig03_access_score_choropleth.png`: Modeled exponential accessibility score ($A_i = \exp(-d_i / 1000)$).
4. `fig04_poverty_vs_distance_scatter.png`: Nonparametric scatterplot and OLS fit of poverty rate vs. walking distance with 95% bootstrap CI.
5. `fig05_quintile_disparity_contrast.png`: Population-weighted accessibility comparison between the lowest (Q1) and highest (Q5) poverty quintiles.
6. `fig06_weighted_lorenz_curve.png`: Population-weighted Lorenz curve illustrating inequality in library accessibility ($G_A = 0.301$).
7. `fig07_spatial_disadvantage_map.png`: Spatial disadvantage prioritization score map ($S_i = q_i (1 - A_i)$).
8. `fig08_facility_simulation_map.png`: Hypothetical optimal location simulation for one additional library branch under an equity-weighted objective.

#### Cross-City & Washington, D.C. Validation
9. `fig_cross_city_comparison_bar.png`: Side-by-side bar chart comparison of Spearman correlations, quintile disparities, and econometric $R^2$ across Chicago and Washington, D.C.
10. `fig_dc_chicago_model_actual_vs_predicted.png`: Out-of-sample scatter plot evaluating Chicago-trained model predictions against actual walking distances in DC ($r = 0.279, p < 0.0001$).
11. `fig_dc_poverty_choropleth.png`: Spatial distribution of tract poverty rates across Washington, D.C. (ACS 2019–2023).
12. `fig_dc_walking_distance_choropleth.png`: Shortest walking network distance to the nearest DC Public Library branch with facility markers.
13. `fig_dc_access_score_choropleth.png`: Modeled exponential accessibility score ($A_i = \exp(-d_i / 1000)$) across Washington, D.C.

### Tables (`tables/`)
- `chicago_tract_level_metrics.csv`: Tract-by-tract dataset with 778 populated Chicago tracts, containing GEOID, total population, poverty universe, poverty count, poverty rate, median household income, population density, walking distance, Euclidean distance, access scores, and spatial disadvantage indices.
- `regression_coefficients.csv`: Full Chicago OLS regression results with White / HC1 heteroskedasticity-consistent standard errors, t-statistics, p-values, and 95% confidence intervals.
- `dc_tract_level_metrics.csv`: Tract-by-tract dataset with 206 populated Washington, D.C. tracts, containing socioeconomic indicators, walking distances, and accessibility scores.
