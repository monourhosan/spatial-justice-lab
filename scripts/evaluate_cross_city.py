"""Cross-City Validation & Model Accuracy Evaluation: Chicago vs. Washington, D.C.

This script acquires official Washington, D.C. open data (census tracts, ACS 2019-2023 demographics,
and DC Public Library branches), integrates it with the spatial justice mathematical modeling framework,
and rigorously tests the accuracy of the model trained on Chicago on the new city dataset.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import requests
from scipy import stats
from scipy.spatial import cKDTree

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("evaluate_cross_city")

# Paths
ROOT_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT_DIR / "data" / "raw"
PROC_DIR = ROOT_DIR / "data" / "processed"
RESULTS_DIR = ROOT_DIR / "results"
FIG_DIR = RESULTS_DIR / "figures"
TAB_DIR = RESULTS_DIR / "tables"

for d in [RAW_DIR, PROC_DIR, RESULTS_DIR, FIG_DIR, TAB_DIR]:
    d.mkdir(parents=True, exist_ok=True)


def acquire_dc_data() -> tuple[gpd.GeoDataFrame, gpd.GeoDataFrame]:
    """Acquire official Washington, D.C. open data."""
    tracts_path = RAW_DIR / "dc_census_tracts_economic.geojson"
    demo_path = RAW_DIR / "dc_demographics.json"
    lib_path = RAW_DIR / "dc_public_libraries.geojson"

    # 1. Economic characteristics (Tract geometries, poverty rate, median income, land area)
    if not tracts_path.exists():
        logger.info("Downloading DC Census Tracts with Economic Characteristics from DC GIS...")
        url_econ = (
            "https://maps2.dcgis.dc.gov/dcgis/rest/services/OP/ACS_Economic_Characteristics/MapServer/59/query"
        )
        params_econ = {"where": "1=1", "outFields": "*", "f": "geojson", "returnGeometry": "true"}
        r_econ = requests.get(url_econ, params=params_econ, timeout=60)
        r_econ.raise_for_status()
        tracts_path.write_text(r_econ.text, encoding="utf-8")
        logger.info(f"Saved {tracts_path}")

    # 2. Demographic characteristics (Total Population)
    if not demo_path.exists():
        logger.info("Downloading DC Demographics (Total Population) from DC GIS...")
        url_demo = (
            "https://maps2.dcgis.dc.gov/dcgis/rest/services/OP/ACS_Demographic_Characteristics/MapServer/57/query"
        )
        params_demo = {"where": "1=1", "outFields": "GEOID,DP05_0001E", "f": "json", "returnGeometry": "false"}
        r_demo = requests.get(url_demo, params=params_demo, timeout=60)
        r_demo.raise_for_status()
        demo_path.write_text(r_demo.text, encoding="utf-8")
        logger.info(f"Saved {demo_path}")

    # 3. DC Public Library branches
    if not lib_path.exists():
        logger.info("Downloading DC Public Library locations from Open Data DC...")
        url_lib = "https://opendata.dc.gov/api/download/v1/items/cab0eaaad4e242c18a36422c3323e6ac/geojson?layers=4"
        r_lib = requests.get(url_lib, timeout=60)
        r_lib.raise_for_status()
        lib_path.write_text(r_lib.text, encoding="utf-8")
        logger.info(f"Saved {lib_path}")

    tracts_gdf = gpd.read_file(tracts_path)
    demo_json = json.loads(demo_path.read_text(encoding="utf-8"))
    demo_df = pd.DataFrame([f["attributes"] for f in demo_json["features"]])

    tracts_gdf = tracts_gdf.merge(demo_df, on="GEOID", how="left")
    libraries_gdf = gpd.read_file(lib_path)

    return tracts_gdf, libraries_gdf


def population_weighted_mean(values: np.ndarray, weights: np.ndarray) -> float:
    """Compute population-weighted mean."""
    v = np.asarray(values, dtype=float)
    w = np.asarray(weights, dtype=float)
    valid = ~np.isnan(v) & ~np.isnan(w) & (w > 0)
    if not np.any(valid):
        return np.nan
    return float(np.sum(v[valid] * w[valid]) / np.sum(w[valid]))


def population_weighted_gini(values: np.ndarray, weights: np.ndarray) -> float:
    """Compute population-weighted Gini coefficient."""
    v = np.asarray(values, dtype=float)
    w = np.asarray(weights, dtype=float)
    valid = ~np.isnan(v) & ~np.isnan(w) & (w > 0) & (v >= 0)
    v = v[valid]
    w = w[valid]
    if len(v) == 0 or np.all(v == 0):
        return 0.0

    order = np.argsort(v)
    v_sorted = v[order]
    w_sorted = w[order]

    cum_w = np.cumsum(w_sorted) / np.sum(w_sorted)
    cum_v = np.cumsum(v_sorted * w_sorted) / np.sum(v_sorted * w_sorted)

    cum_w = np.insert(cum_w, 0, 0.0)
    cum_v = np.insert(cum_v, 0, 0.0)

    area = np.trapezoid(cum_v, cum_w)
    return float(np.clip(1.0 - 2.0 * area, 0.0, 1.0))


def compute_correlations(x: np.ndarray, y: np.ndarray, n_boot: int = 1000, seed: int = 42) -> dict:
    """Compute Spearman and Pearson correlations with bootstrap CIs."""
    valid = ~np.isnan(x) & ~np.isnan(y)
    xv = x[valid]
    yv = y[valid]
    n = len(xv)

    spearman_res = stats.spearmanr(xv, yv)
    pearson_res = stats.pearsonr(xv, yv)

    rng = np.random.default_rng(seed)
    boot_rhos = []
    for _ in range(n_boot):
        idx = rng.choice(n, size=n, replace=True)
        r, _ = stats.spearmanr(xv[idx], yv[idx])
        if not np.isnan(r):
            boot_rhos.append(r)

    return {
        "n": n,
        "spearman_rho": float(spearman_res.statistic),
        "spearman_pvalue": float(spearman_res.pvalue),
        "spearman_ci95_lower": float(np.percentile(boot_rhos, 2.5)),
        "spearman_ci95_upper": float(np.percentile(boot_rhos, 97.5)),
        "pearson_r": float(pearson_res.statistic),
        "pearson_pvalue": float(pearson_res.pvalue),
    }


def fit_robust_ols(y: np.ndarray, X: np.ndarray, feature_names: list[str]) -> dict:
    """Fit OLS with White / HC1 robust standard errors."""
    n, k = X.shape
    beta, _residuals, _rank, _s = np.linalg.lstsq(X, y, rcond=None)
    y_pred = X @ beta
    e = y - y_pred

    ss_tot = np.sum((y - np.mean(y)) ** 2)
    ss_res = np.sum(e**2)
    r_squared = 1.0 - (ss_res / ss_tot)
    adj_r_squared = 1.0 - ((1.0 - r_squared) * (n - 1) / (n - k))

    XtX_inv = np.linalg.inv(X.T @ X)
    meat = X.T @ (e[:, None] ** 2 * X)
    v_hc1 = (n / (n - k)) * (XtX_inv @ meat @ XtX_inv)
    se_hc1 = np.sqrt(np.maximum(0.0, np.diag(v_hc1)))
    t_stats = beta / np.where(se_hc1 > 0, se_hc1, np.nan)
    p_values = 2.0 * (1.0 - stats.t.cdf(np.abs(t_stats), df=n - k))
    crit_val = stats.t.ppf(0.975, df=n - k)

    summary_table = []
    for i, name in enumerate(feature_names):
        summary_table.append(
            {
                "variable": name,
                "coefficient": float(beta[i]),
                "std_error_hc1": float(se_hc1[i]),
                "t_statistic": float(t_stats[i]),
                "p_value": float(p_values[i]),
                "ci95_lower": float(beta[i] - crit_val * se_hc1[i]),
                "ci95_upper": float(beta[i] + crit_val * se_hc1[i]),
            }
        )

    return {
        "n": n,
        "k": k,
        "beta": beta,
        "r_squared": float(r_squared),
        "adj_r_squared": float(adj_r_squared),
        "residuals": e,
        "fitted_values": y_pred,
        "summary_table": summary_table,
    }


def main():
    logger.info("=" * 70)
    logger.info("SPATIAL JUSTICE CROSS-CITY MODEL ACCURACY VALIDATION")
    logger.info("=" * 70)

    # 1. Acquire DC data
    tracts_gdf, libraries_gdf = acquire_dc_data()

    # 2. Coordinate Reference System Projection
    # Project to standard NAD83 / Maryland (meters) EPSG:26985
    target_crs = "EPSG:26985"
    tracts_proj = tracts_gdf.to_crs(target_crs)
    lib_proj = libraries_gdf.to_crs(target_crs)

    # 3. Variable Extraction
    # DP05_0001E: Total Population
    # DP03_0128PE: Percent of all people below federal poverty line
    # DP03_0062E: Median household income
    # ALAND: Land area in square meters
    pop = tracts_proj["DP05_0001E"].values
    area_km2 = tracts_proj.geometry.area.values / 1e6
    density = pop / area_km2
    poverty_rate = tracts_proj["DP03_0128PE"].values / 100.0  # Fraction [0, 1]
    income = tracts_proj["DP03_0062E"].fillna(tracts_proj["DP03_0062E"].median()).values
    income = np.maximum(1000.0, income)

    # 4. Representative origins and distances
    orig_points = tracts_proj.geometry.representative_point()
    orig_xy = np.column_stack([orig_points.x, orig_points.y])
    lib_xy = np.column_stack([lib_proj.geometry.x, lib_proj.geometry.y])

    tree = cKDTree(lib_xy)
    euc_dists, nearest_lib_idx = tree.query(orig_xy, k=1)

    # Empirical network circuity multiplier (1.3203 from Chicago pedestrian network)
    circuity = 1.3203
    net_dists = euc_dists * circuity

    # Add to tracts GeoDataFrame
    tracts_proj["euclidean_distance_m"] = euc_dists
    tracts_proj["network_distance_m"] = net_dists
    tracts_proj["total_population"] = pop
    tracts_proj["poverty_rate"] = poverty_rate
    tracts_proj["median_income"] = income
    tracts_proj["pop_density_km2"] = density
    tracts_proj["dist_km"] = net_dists / 1000.0

    # Exponential accessibility scores
    tracts_proj["access_score_1000"] = np.exp(-net_dists / 1000.0)
    tracts_proj["access_score_500"] = np.exp(-net_dists / 500.0)
    tracts_proj["access_score_2000"] = np.exp(-net_dists / 2000.0)
    tracts_proj["spatial_disadvantage"] = poverty_rate * (1.0 - tracts_proj["access_score_1000"])

    # -------------------------------------------------------------
    # 5. Model Accuracy Evaluation: Chicago Model on Washington, D.C.
    # -------------------------------------------------------------
    logger.info("Evaluating Chicago-trained econometric model on Washington, D.C. dataset...")

    # Load Chicago benchmark metrics from metrics.json
    chicago_metrics_path = RESULTS_DIR / "metrics.json"
    with open(chicago_metrics_path, "r", encoding="utf-8") as f:
        chicago_data = json.load(f)["results"]

    chicago_summary = chicago_data["regression"]["summary_table"]
    beta_chicago = np.array([row["coefficient"] for row in chicago_summary])
    # [Intercept, poverty_rate, log(1 + density), log(median_income)]

    # Form design matrix for DC
    y_dc = np.log1p(net_dists)
    X_dc = np.column_stack([
        np.ones(len(y_dc)),
        poverty_rate,
        np.log1p(density),
        np.log(income),
    ])

    # Out-of-sample prediction using Chicago coefficients
    y_pred_dc = X_dc @ beta_chicago
    d_pred_dc = np.expm1(y_pred_dc)

    # Quantitative Accuracy Metrics
    ss_tot = np.sum((y_dc - np.mean(y_dc)) ** 2)
    ss_res = np.sum((y_dc - y_pred_dc) ** 2)
    r2_oos = 1.0 - (ss_res / ss_tot)

    mae_log = float(np.mean(np.abs(y_dc - y_pred_dc)))
    rmse_log = float(np.sqrt(np.mean((y_dc - y_pred_dc) ** 2)))
    mae_meters = float(np.mean(np.abs(net_dists - d_pred_dc)))
    rmse_meters = float(np.sqrt(np.mean((net_dists - d_pred_dc) ** 2)))
    medae_meters = float(np.median(np.abs(net_dists - d_pred_dc)))
    mape = float(np.mean(np.abs((net_dists - d_pred_dc) / net_dists)) * 100.0)
    bias_meters = float(np.mean(d_pred_dc - net_dists))
    corr_pred_actual, p_corr = stats.pearsonr(net_dists, d_pred_dc)

    accuracy_metrics = {
        "r2_out_of_sample": float(r2_oos),
        "correlation_actual_vs_predicted": float(corr_pred_actual),
        "mae_log_distance": mae_log,
        "rmse_log_distance": rmse_log,
        "mae_meters": mae_meters,
        "rmse_meters": rmse_meters,
        "median_absolute_error_meters": medae_meters,
        "mape_percent": mape,
        "mean_bias_meters": bias_meters,
    }

    # -------------------------------------------------------------
    # 6. In-Sample Econometric Fit on Washington, D.C.
    # -------------------------------------------------------------
    logger.info("Fitting Econometric OLS Regression on Washington, D.C....")
    feature_names = ["Intercept", "poverty_rate (q_i)", "log(1 + density)", "log(median_income)"]
    ols_dc = fit_robust_ols(y_dc, X_dc, feature_names=feature_names)

    # -------------------------------------------------------------
    # 7. Spatial Justice Hypothesis Testing on Washington, D.C.
    # -------------------------------------------------------------
    logger.info("Computing Spatial Accessibility and Disparity Metrics for DC...")
    corrs_dc = compute_correlations(poverty_rate, net_dists, n_boot=1000, seed=42)
    gini_1000 = population_weighted_gini(tracts_proj["access_score_1000"].values, pop)
    gini_500 = population_weighted_gini(tracts_proj["access_score_500"].values, pop)
    gini_2000 = population_weighted_gini(tracts_proj["access_score_2000"].values, pop)

    mean_acc_1000 = population_weighted_mean(tracts_proj["access_score_1000"].values, pop)
    mean_acc_500 = population_weighted_mean(tracts_proj["access_score_500"].values, pop)
    mean_acc_2000 = population_weighted_mean(tracts_proj["access_score_2000"].values, pop)

    # Quintile disparity
    # Sort by poverty rate and form 5 population-balanced or tract-based quintiles
    q_sort = np.argsort(poverty_rate)
    tracts_sorted = tracts_proj.iloc[q_sort].copy()
    n_per_q = len(tracts_sorted) // 5
    q1 = tracts_sorted.iloc[:n_per_q]
    q5 = tracts_sorted.iloc[4 * n_per_q :]
    mean_acc_q1 = population_weighted_mean(q1["access_score_1000"].values, q1["total_population"].values)
    mean_acc_q5 = population_weighted_mean(q5["access_score_1000"].values, q5["total_population"].values)
    delta_a = mean_acc_q5 - mean_acc_q1

    quintile_metrics = {
        "mean_high_poverty_q5": mean_acc_q5,
        "mean_low_poverty_q1": mean_acc_q1,
        "disparity_delta": delta_a,
        "n_tracts_q1": len(q1),
        "n_tracts_q5": len(q5),
        "pop_q1": float(q1["total_population"].sum()),
        "pop_q5": float(q5["total_population"].sum()),
    }

    # -------------------------------------------------------------
    # 8. Save Processed GeoDataFrames
    # -------------------------------------------------------------
    logger.info("Saving processed datasets to GPKG...")
    tracts_save = tracts_proj[[
        "GEOID", "NAME", "total_population", "poverty_rate", "median_income",
        "pop_density_km2", "euclidean_distance_m", "network_distance_m",
        "access_score_1000", "access_score_500", "access_score_2000",
        "spatial_disadvantage", "geometry"
    ]].copy()
    tracts_save.to_file(PROC_DIR / "dc_tracts_analysis.gpkg", layer="tracts", driver="GPKG")
    lib_proj[["NAME", "ADDRESS", "geometry"]].to_file(PROC_DIR / "dc_libraries.gpkg", layer="libraries", driver="GPKG")

    # Export CSV table
    tracts_save.drop(columns="geometry").to_csv(TAB_DIR / "dc_tract_level_metrics.csv", index=False)

    # -------------------------------------------------------------
    # 9. Plotting Publication Figures
    # -------------------------------------------------------------
    logger.info("Generating publication-quality comparison maps and figures...")

    # Plot 1: DC Poverty Rate Choropleth
    fig, ax = plt.subplots(figsize=(9, 8))
    tracts_proj.plot(column="poverty_rate", cmap="YlOrRd", legend=True,
                     legend_kwds={"label": "Poverty Rate (ACS 2019-2023)", "orientation": "horizontal"},
                     ax=ax, edgecolor="#333333", linewidth=0.3)
    ax.set_title("Washington, D.C. Census Tract Poverty Rates ($q_i$)", fontsize=13, fontweight="bold")
    ax.axis("off")
    plt.tight_layout()
    plt.savefig(FIG_DIR / "fig_dc_poverty_choropleth.png", dpi=300)
    plt.close()

    # Plot 2: DC Walking Distance Choropleth
    fig, ax = plt.subplots(figsize=(9, 8))
    tracts_proj.plot(column="dist_km", cmap="viridis_r", legend=True,
                     legend_kwds={"label": "Walking Distance to Nearest Library (km)", "orientation": "horizontal"},
                     ax=ax, edgecolor="#333333", linewidth=0.3)
    lib_proj.plot(ax=ax, color="red", markersize=35, edgecolor="black", label="Public Libraries (n=28)")
    ax.legend(loc="lower left")
    ax.set_title("Washington, D.C. Walking Distance to Nearest Public Library ($d_i$)", fontsize=13, fontweight="bold")
    ax.axis("off")
    plt.tight_layout()
    plt.savefig(FIG_DIR / "fig_dc_walking_distance_choropleth.png", dpi=300)
    plt.close()

    # Plot 3: DC Accessibility Score Choropleth
    fig, ax = plt.subplots(figsize=(9, 8))
    tracts_proj.plot(column="access_score_1000", cmap="viridis", legend=True,
                     legend_kwds={"label": "Modeled Access Score $A_i(\\tau=1000\\text{m})$", "orientation": "horizontal"},
                     ax=ax, edgecolor="#333333", linewidth=0.3)
    lib_proj.plot(ax=ax, color="magenta", markersize=35, edgecolor="black", label="Public Libraries")
    ax.legend(loc="lower left")
    ax.set_title("Washington, D.C. Modeled Library Accessibility Score ($A_i$)", fontsize=13, fontweight="bold")
    ax.axis("off")
    plt.tight_layout()
    plt.savefig(FIG_DIR / "fig_dc_access_score_choropleth.png", dpi=300)
    plt.close()

    # Plot 4: Chicago Model Predictions vs Actual Distances in DC
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.scatter(net_dists, d_pred_dc, alpha=0.6, color="#1f78b4", edgecolors="black", linewidths=0.5, label="DC Tracts (n=206)")
    max_val = max(np.max(net_dists), np.max(d_pred_dc)) + 200
    ax.plot([0, max_val], [0, max_val], "r--", linewidth=1.5, label="Perfect 1:1 Transfer")
    ax.set_xlim(0, max_val)
    ax.set_ylim(0, max_val)
    ax.set_xlabel("Actual Walking Distance to Nearest Library ($d_i$, meters)", fontsize=11)
    ax.set_ylabel("Predicted Distance by Chicago Model (meters)", fontsize=11)
    ax.set_title("Cross-City Generalization: Chicago Model Applied to Washington, D.C.\n"
                 f"Out-of-Sample $R^2 = {r2_oos:.3f}$, $r = {corr_pred_actual:.3f}$, MAE = {mae_meters:.0f}m",
                 fontsize=12, fontweight="bold")
    ax.grid(True, linestyle="--", alpha=0.5)
    ax.legend(loc="upper left")
    plt.tight_layout()
    plt.savefig(FIG_DIR / "fig_dc_chicago_model_actual_vs_predicted.png", dpi=300)
    plt.close()

    # Plot 5: Cross-City Metric Comparison Bar Chart
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
    cities = ["Chicago", "Washington, D.C."]

    # Subplot 1: Spearman rho and Quintile Disparity
    rhos = [chicago_data["correlations"]["spearman_rho"], corrs_dc["spearman_rho"]]
    deltas = [chicago_data["quintile_disparity"]["disparity_delta"], quintile_metrics["disparity_delta"]]

    x = np.arange(len(cities))
    width = 0.35
    ax1.bar(x - width/2, rhos, width, label="Spearman Correlation $\\rho(q, d)$", color="#3182bd")
    ax1.bar(x + width/2, deltas, width, label="Quintile Disparity Contrast $\\Delta_A$", color="#de2d26")
    ax1.axhline(0, color="black", linewidth=0.8, linestyle="--")
    ax1.set_xticks(x)
    ax1.set_xticklabels(cities, fontsize=11, fontweight="bold")
    ax1.set_ylabel("Metric Value", fontsize=11)
    ax1.set_title("Spatial Justice Metric Comparison", fontsize=12, fontweight="bold")
    ax1.legend(loc="upper right")
    ax1.grid(True, linestyle=":", alpha=0.6)

    # Subplot 2: Model R-squared comparison
    r2_vals = [chicago_data["regression"]["r_squared"], ols_dc["r_squared"]]
    ax2.bar(cities, r2_vals, color=["#756bb1", "#2ca25f"], width=0.5)
    ax2.set_ylabel("Econometric In-Sample $R^2$", fontsize=11)
    ax2.set_title("Model Explanatory Power ($R^2$)", fontsize=12, fontweight="bold")
    ax2.set_ylim(0, max(r2_vals) * 1.3)
    for i, v in enumerate(r2_vals):
        ax2.text(i, v + 0.005, f"{v:.4f} ({v*100:.1f}%)", ha="center", fontweight="bold")
    ax2.grid(True, linestyle=":", alpha=0.6)

    plt.tight_layout()
    plt.savefig(FIG_DIR / "fig_cross_city_comparison_bar.png", dpi=300)
    plt.close()

    # -------------------------------------------------------------
    # 10. Compile Full Cross-City Results JSON
    # -------------------------------------------------------------
    full_results = {
        "metadata": {
            "source_model": "Chicago, Illinois (ACS 2019-2023, n=778 tracts, 82 libraries)",
            "target_evaluation": "Washington, District of Columbia (ACS 2019-2023, n=206 tracts, 28 libraries)",
            "projection_crs": "EPSG:26985 (NAD83 / Maryland meters)",
        },
        "sample_comparison": {
            "chicago": {
                "n_tracts": chicago_data["sample_sizes"]["n_analysis_tracts"],
                "total_population": chicago_data["sample_sizes"]["total_population"],
                "n_libraries": chicago_data["sample_sizes"]["n_libraries"],
                "mean_distance_m": chicago_data["distance_summary"]["mean_network_m"],
                "median_distance_m": chicago_data["distance_summary"]["median_network_m"],
                "mean_access_tau1000": chicago_data["accessibility_summary"]["pop_weighted_mean_tau1000"],
                "gini_access_tau1000": chicago_data["accessibility_summary"]["gini_tau1000"],
            },
            "washington_dc": {
                "n_tracts": len(tracts_proj),
                "total_population": float(np.sum(pop)),
                "n_libraries": len(lib_proj),
                "mean_distance_m": float(np.mean(net_dists)),
                "median_distance_m": float(np.median(net_dists)),
                "mean_access_tau1000": mean_acc_1000,
                "gini_access_tau1000": gini_1000,
            },
        },
        "out_of_sample_model_accuracy": accuracy_metrics,
        "dc_in_sample_econometric_fit": {
            "n": ols_dc["n"],
            "r_squared": ols_dc["r_squared"],
            "adj_r_squared": ols_dc["adj_r_squared"],
            "summary_table": ols_dc["summary_table"],
        },
        "dc_spatial_justice_hypotheses": {
            "correlations": corrs_dc,
            "quintile_disparity": quintile_metrics,
            "accessibility_summary": {
                "pop_weighted_mean_tau500": mean_acc_500,
                "pop_weighted_mean_tau1000": mean_acc_1000,
                "pop_weighted_mean_tau2000": mean_acc_2000,
                "gini_tau500": gini_500,
                "gini_tau1000": gini_1000,
                "gini_tau2000": gini_2000,
            },
        },
    }

    metrics_out = RESULTS_DIR / "cross_city_comparison.json"
    with open(metrics_out, "w", encoding="utf-8") as f:
        json.dump(full_results, f, indent=2)
    logger.info(f"Saved full cross-city metrics to {metrics_out}")

    print("\n" + "=" * 70)
    print("CROSS-CITY VALIDATION COMPLETE")
    print("=" * 70)
    print(f"Out-of-sample R^2 (Chicago Model on DC): {r2_oos:.4f}")
    print(f"Correlation (Predicted vs Actual):       {corr_pred_actual:.4f} (p = {p_corr:.4e})")
    print(f"Mean Absolute Error (Meters):            {mae_meters:.1f} m")
    print(f"Median Absolute Error (Meters):          {medae_meters:.1f} m")
    print(f"Mean Absolute Percentage Error (MAPE):   {mape:.1f}%")
    print(f"In-sample DC OLS R^2:                    {ols_dc['r_squared']:.4f}")
    print(f"Spearman rho (Poverty vs Distance, DC):  {corrs_dc['spearman_rho']:.4f} (p = {corrs_dc['spearman_pvalue']:.4e})")
    print(f"Quintile Disparity Delta_A (DC):         {delta_a:.4f}")
    print("=" * 70)


if __name__ == "__main__":
    main()
