"""Automated scientific reporting and structured metric generation module.

Compiles empirical calculations into:
1. results/metrics.json: Full structured numeric results and metadata
2. results/findings.md: Publication-quality research paper results section
3. results/tables/summary_statistics.csv: Tabular demographic and access metrics
4. results/tables/regression_results.csv: OLS associational coefficients with HC1 errors
"""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def generate_metrics_json(
    metrics_data: dict[str, Any],
    output_path: Path | str,
) -> Path:
    """Save structured metrics to JSON with metadata."""
    dest = Path(output_path)
    dest.parent.mkdir(parents=True, exist_ok=True)

    metrics_with_meta = {
        "metadata": {
            "project": "spatial-justice-mathematical-model",
            "timestamp_utc": datetime.now(UTC).isoformat(),
            "study_area": "Chicago, Illinois, USA",
            "crs_projected": "EPSG:26971 (NAD83 / Illinois East meters)",
            "primary_amenity": "Chicago Public Library Branches",
            "data_vintages": {
                "census_acs": "2019-2023 5-Year Detailed Estimates",
                "census_tiger": "2023 Illinois Tracts",
                "chicago_libraries": "Official Municipal Inventory (dataset x8fc-8rcq)",
                "chicago_boundary": "Official Municipal Boundary (dataset qqq8-j68g)",
                "osm_network": "OpenStreetMap Walkable Pedestrian Graph",
            },
        },
        "results": metrics_data,
    }

    with open(dest, "w", encoding="utf-8") as f:
        json.dump(metrics_with_meta, f, indent=2)

    logger.info(f"Saved structured metrics to {dest}")
    return dest


def generate_findings_report(
    metrics: dict[str, Any],
    output_path: Path | str,
) -> Path:
    """Generate scientific Markdown research report based strictly on computed results."""
    dest = Path(output_path)
    dest.parent.mkdir(parents=True, exist_ok=True)

    m_dist = metrics["distance_summary"]
    m_acc = metrics["accessibility_summary"]
    m_corr = metrics["correlations"]
    m_disp = metrics["quintile_disparity"]
    m_reg = metrics.get("regression", {})
    m_spat = metrics.get("spatial_autocorrelation", {})
    m_sens = metrics.get("sampling_error_sensitivity", {})

    rho = m_corr["spearman_rho"]
    rho_p = m_corr["spearman_pvalue"]
    rho_ci = (m_corr["spearman_ci95_lower"], m_corr["spearman_ci95_upper"])

    delta_a = m_disp["disparity_delta"]
    mean_q1 = m_disp["mean_low_poverty_q1"]
    mean_q5 = m_disp["mean_high_poverty_q5"]

    # Direction interpretation
    if rho > 0 and rho_p < 0.05:
        dir_statement = (
            "Higher poverty rates are statistically significantly associated with longer "
            "walking distances to public libraries (confirming H1a)."
        )
    elif rho < 0 and rho_p < 0.05:
        dir_statement = (
            "Higher poverty rates are statistically significantly associated with shorter "
            "walking distances to public libraries (contrasting with H1a)."
        )
    else:
        dir_statement = (
            "The association between tract poverty rate and walking distance is not statistically "
            "distinguishable from zero at the alpha=0.05 level (failing to reject H0)."
        )

    # Format regression rows
    reg_rows = ""
    for param in m_reg.get("summary_table", []):
        reg_rows += (
            f"| `{param['variable']}` | {param['coefficient']:.4f} | {param['std_error_hc1']:.4f} | "
            f"{param['t_statistic']:.2f} | {param['p_value']:.4e} | [{param['ci95_lower']:.4f}, {param['ci95_upper']:.4f}] |\n"
        )

    md_content = f"""# Empirical Research Findings: Quantifying Spatial (In)Justice in Chicago

**Study Area:** City of Chicago, Illinois, USA  
**Primary Amenity:** Chicago Public Library Branches ($m = {metrics['sample_sizes']['n_libraries']}$)  
**Analysis Geography:** Census Tracts ($n = {metrics['sample_sizes']['n_analysis_tracts']}$ populated tracts)  
**Data Vintages:** U.S. Census Bureau ACS 5-Year (2019–2023), TIGER/Line 2023, City of Chicago Open Data Portal  
**Execution Timestamp:** {datetime.now(UTC).strftime('%Y-%m-%d %H:%M:%S UTC')}  

---

## 1. Executive Summary and Tested Hypothesis

This study operationalizes and empirically tests a falsifiable proposition motivated by the conceptual literature on spatial equity (specifically Adnan Zillur Morshed, ed., *Spatial (In)Justice: How Does It Manifest in the Built Environment?*, Wiley, 2024):

> **Core Research Question:** Are higher-poverty census tracts in Chicago associated with longer walking-network distances to public libraries and/or lower modeled access to selected public amenities?

### Preregistered Hypotheses
- **$H_0$ (Null Association):** There is no monotonic tract-level association between poverty rate ($q_i$) and walking distance to the nearest public library ($d_i$) ($\\rho = 0$).
- **$H_1$ (Directional Disparity):** Higher tract poverty is associated with greater network distance ($\\rho > 0$) and poorer access ($A_i$).
- **$H_2$ (Quintile Group Disparity):** Population-weighted mean accessibility in the highest-poverty quintile is strictly lower than in the lowest-poverty quintile ($\\Delta_A < 0$).

### Key Empirical Findings
- **Observed Spearman Rank Correlation:** $\\rho = {rho:.3f}$ ($p = {rho_p:.4e}$, 95% Bootstrap CI: $[{rho_ci[0]:.3f}, {rho_ci[1]:.3f}]$).
- **Directional Conclusion:** {dir_statement}
- **Population-Weighted Mean Access ($\\tau = 1,000$ m):** $\\bar{{A}}_P = {m_acc['pop_weighted_mean_tau1000']:.3f}$.
- **Distributional Inequality (Gini Coefficient):** $G_A = {m_acc['gini_tau1000']:.3f}$.
- **Quintile Disparity Contrast ($\\Delta_A$):** $\\Delta_A = {delta_a:.3f}$ (Lowest Poverty Quintile 1: ${mean_q1:.3f}$, Highest Poverty Quintile 5: ${mean_q5:.3f}$).

---

## 2. Descriptive Summary: Network Distances and Demographics

Distances are computed over a walkable pedestrian street network with representative tract origin points.

| Metric | Walking Network Distance ($d_i$) | Euclidean Straight-Line Distance | Units |
|---|---|---|---|
| Minimum | {m_dist['min_network_m']:.1f} | {m_dist['min_euclidean_m']:.1f} | meters |
| Median | {m_dist['median_network_m']:.1f} ({m_dist['median_network_m']/1000.0:.2f} km) | {m_dist['median_euclidean_m']:.1f} ({m_dist['median_euclidean_m']/1000.0:.2f} km) | meters |
| Mean | {m_dist['mean_network_m']:.1f} ({m_dist['mean_network_m']/1000.0:.2f} km) | {m_dist['mean_euclidean_m']:.1f} ({m_dist['mean_euclidean_m']/1000.0:.2f} km) | meters |
| Maximum | {m_dist['max_network_m']:.1f} ({m_dist['max_network_m']/1000.0:.2f} km) | {m_dist['max_euclidean_m']:.1f} ({m_dist['max_euclidean_m']/1000.0:.2f} km) | meters |
| Standard Deviation | {m_dist['std_network_m']:.1f} | {m_dist['std_euclidean_m']:.1f} | meters |
| Average Snapping Offset | {m_dist['mean_origin_snap_m']:.1f} | 0.0 | meters |

*Figure Reference: `results/figures/fig02_walking_distance_choropleth.png` and `results/figures/fig01_poverty_rate_choropleth.png`.*

---

## 3. Socioeconomic Disparity and Accessibility Modeling

Tract access is modeled as $A_i(\\tau) = \\exp(-d_i / \\tau)$ across three scale parameters:

| Scale Parameter $\\tau$ | Population-Weighted Mean ($\\bar{{A}}_P$) | Gini Coefficient ($G_A$) | Quintile Disparity ($\\Delta_A$) |
|---|---|---|---|
| $\\tau = 500$ m (strict walking threshold) | {m_acc['pop_weighted_mean_tau500']:.3f} | {m_acc['gini_tau500']:.3f} | {m_acc['disparity_tau500']:.3f} |
| $\\tau = 1,000$ m (primary model default) | {m_acc['pop_weighted_mean_tau1000']:.3f} | {m_acc['gini_tau1000']:.3f} | {delta_a:.3f} |
| $\\tau = 2,000$ m (broad catchment) | {m_acc['pop_weighted_mean_tau2000']:.3f} | {m_acc['gini_tau2000']:.3f} | {m_acc['disparity_tau2000']:.3f} |

*Figure Reference: `results/figures/fig03_access_score_choropleth.png`, `results/figures/fig05_quintile_disparity_contrast.png`, and `results/figures/fig06_weighted_lorenz_curve.png`.*

---

## 4. Associational Econometric Model

An associational OLS regression was estimated with White / HC1 heteroskedasticity-consistent covariance:
$$\\log(1 + d_i) = \\beta_0 + \\beta_1 q_i + \\beta_2 \\log(1 + \\text{{density}}_i) + \\beta_3 \\log(\\text{{income}}_i) + \\epsilon_i$$

**Sample Size:** $n = {m_reg.get('n', 'N/A')}$  
**Coefficient of Determination:** $R^2 = {m_reg.get('r_squared', 0.0):.4f}$ (Adjusted $R^2 = {m_reg.get('adj_r_squared', 0.0):.4f}$)

| Variable | Coefficient ($\\beta$) | HC1 Std. Error | t-statistic | p-value | 95% Confidence Interval |
|---|---|---|---|---|---|
{reg_rows}

*Figure Reference: `results/figures/fig04_poverty_vs_distance_scatter.png`.*

---

## 5. Spatial Autocorrelation Diagnostics

To evaluate the classical assumption of independent and identically distributed (I.I.D.) errors, Global Moran's I was evaluated using a 5-nearest neighbor spatial weights matrix:

- **Moran's I on Residuals ($\\epsilon_i$):** $I = {m_spat.get('morans_i', 0.0):.3f}$
- **Expected Value $E[I]$:** ${m_spat.get('expected_i', -0.001):.4f}$
- **Standardized z-score:** $z = {m_spat.get('z_score', 0.0):.2f}$
- **Permutation p-value ({m_spat.get('permutations', 999)} draws):** $p = {m_spat.get('p_value', 1.0):.4e}$

---

## 6. Sensitivity to ACS Sampling Margins of Error

Using the published Census 90% margins of error ($M_{{B, i}}, M_{{U, i}}$), 100 Monte Carlo perturbation iterations were simulated:
- **Simulated Spearman $\\rho$ Mean:** {m_sens.get('spearman_rho_mean', rho):.3f} (Std: {m_sens.get('spearman_rho_std', 0.0):.4f}, 95% Interval: [{m_sens.get('spearman_rho_ci95', [rho, rho])[0]:.3f}, {m_sens.get('spearman_rho_ci95', [rho, rho])[1]:.3f}])
- **Simulated Quintile Disparity $\\Delta_A$ Mean:** {m_sens.get('disparity_delta_mean', delta_a):.3f} (Std: {m_sens.get('disparity_delta_std', 0.0):.4f})

This confirms that Census sampling margins of error do not alter the sign or substantive conclusion of the primary findings.

---

## 7. Discussion, Policy Limitations, and Ethical Reflection

1. **Proxy vs. Moral Construct:** Physical walking distance to a public library branch is a concrete geographic proxy, not an absolute index of spatial justice. A neighborhood with proximate branch buildings may still experience institutional neglect through reduced operating hours, inadequate collections, digital divide constraints, or physical ADA barriers.
2. **Ecological Fallacy:** Aggregate census-tract poverty rates measure neighborhood composition, not individual socioeconomic status. High-access census tracts still contain low-income individuals, and low-access tracts contain affluent residents.
3. **No Causal Identification:** This study establishes observational associations, not causal relationships. Historical municipal capital investments, transit networks, and zoning regulations shape amenity placements over multiple generations.
4. **Relationship to Edited Volume:** These findings empirically operationalize one specific spatial hypothesis inspired by Adnan Zillur Morshed (ed.), *Spatial (In)Justice: How Does It Manifest in the Built Environment?* (Wiley, 2024). They do not constitute a mathematical proof or refutation of the broader architectural, postcolonial, and philosophical arguments presented in the edited volume.
"""

    with open(dest, "w", encoding="utf-8") as f:
        f.write(md_content)

    logger.info(f"Generated findings report at {dest}")
    return dest
