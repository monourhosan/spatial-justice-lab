"""Statistical inference, associational regression, and spatial autocorrelation module.

Implements:
1. Nonparametric Spearman rank correlation with permutation/bootstrap confidence intervals
2. Ordinary Least Squares regression with White / HC1 heteroskedasticity-robust standard errors
3. Global Moran's I spatial autocorrelation test on regression residuals
4. ACS sampling margin of error (MOE) Monte Carlo sensitivity simulation
"""

from __future__ import annotations

import logging
from typing import Any

import geopandas as gpd
import numpy as np
from scipy import stats

try:
    import libpysal
    from esda.moran import Moran
    HAS_PYESDA = True
except ImportError:
    HAS_PYESDA = False

logger = logging.getLogger(__name__)


def compute_correlations(
    x: np.ndarray,
    y: np.ndarray,
    n_bootstrap: int = 1000,
    random_seed: int = 42,
) -> dict[str, Any]:
    """Compute Spearman and Pearson correlations with bootstrap confidence intervals.

    Parameters
    ----------
    x : np.ndarray
        Predictor (e.g., poverty rate q_i).
    y : np.ndarray
        Outcome (e.g., walking distance d_i or access score A_i).
    n_bootstrap : int
        Number of bootstrap replications for 95% CI.
    random_seed : int
        Deterministic random seed.

    Returns
    -------
    dict[str, Any]
        Dictionary with correlation coefficients, p-values, 95% CI, and sample size.
    """
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)

    valid = ~np.isnan(x) & ~np.isnan(y)
    x = x[valid]
    y = y[valid]
    n = len(x)

    if n < 5:
        raise ValueError(f"Insufficient sample size for correlation: n={n}")

    spearman_res = stats.spearmanr(x, y)
    pearson_res = stats.pearsonr(x, y)

    # Bootstrap 95% CI for Spearman rho
    rng = np.random.default_rng(random_seed)
    boot_rhos = []
    for _ in range(n_bootstrap):
        idx = rng.choice(n, size=n, replace=True)
        r, _ = stats.spearmanr(x[idx], y[idx])
        if not np.isnan(r):
            boot_rhos.append(r)

    ci_lower = float(np.percentile(boot_rhos, 2.5)) if boot_rhos else np.nan
    ci_upper = float(np.percentile(boot_rhos, 97.5)) if boot_rhos else np.nan

    return {
        "n": n,
        "spearman_rho": float(spearman_res.statistic),
        "spearman_pvalue": float(spearman_res.pvalue),
        "spearman_ci95_lower": ci_lower,
        "spearman_ci95_upper": ci_upper,
        "pearson_r": float(pearson_res.statistic),
        "pearson_pvalue": float(pearson_res.pvalue),
    }


def fit_robust_ols(
    y: np.ndarray,
    X: np.ndarray,
    feature_names: list[str] | None = None,
) -> dict[str, Any]:
    """Fit Ordinary Least Squares with White / HC1 heteroskedasticity-consistent covariance.

    Model:
        y = X beta + epsilon
        V_{HC1} = (n / (n - k)) * (X^T X)^{-1} (X^T diag(e^2) X) (X^T X)^{-1}

    Parameters
    ----------
    y : np.ndarray
        Dependent variable (e.g., log(1 + d_i)). Shape (n,).
    X : np.ndarray
        Independent variable matrix (including constant column). Shape (n, k).
    feature_names : list[str] | None
        Names corresponding to columns of X.

    Returns
    -------
    dict[str, Any]
        Dictionary with coefficients, HC1 standard errors, t-statistics,
        p-values, 95% CIs, R^2, and residuals.
    """
    y = np.asarray(y, dtype=float)
    X = np.asarray(X, dtype=float)

    n, k = X.shape
    if n <= k:
        raise ValueError(f"Degrees of freedom non-positive: n={n}, k={k}")

    # OLS estimation via QR decomposition / pseudoinverse
    beta, _residuals, _rank, _s = np.linalg.lstsq(X, y, rcond=None)

    y_pred = X @ beta
    e = y - y_pred

    ss_tot = np.sum((y - np.mean(y)) ** 2)
    ss_res = np.sum(e**2)
    r_squared = 1.0 - (ss_res / ss_tot) if ss_tot > 0 else 0.0
    adj_r_squared = 1.0 - ((1.0 - r_squared) * (n - 1) / (n - k))

    # Heteroskedasticity-consistent covariance (HC1)
    XtX_inv = np.linalg.inv(X.T @ X)
    meat = X.T @ (e[:, None] ** 2 * X)
    v_hc1 = (n / (n - k)) * (XtX_inv @ meat @ XtX_inv)

    se_hc1 = np.sqrt(np.maximum(0.0, np.diag(v_hc1)))
    t_stats = beta / np.where(se_hc1 > 0, se_hc1, np.nan)
    dof = n - k
    p_values = 2.0 * (1.0 - stats.t.cdf(np.abs(t_stats), df=dof))

    t_crit = stats.t.ppf(0.975, df=dof)
    ci_lower = beta - t_crit * se_hc1
    ci_upper = beta + t_crit * se_hc1

    names = feature_names or [f"x{i}" for i in range(k)]

    params_summary = []
    for i, name in enumerate(names):
        params_summary.append(
            {
                "variable": name,
                "coefficient": float(beta[i]),
                "std_error_hc1": float(se_hc1[i]),
                "t_statistic": float(t_stats[i]),
                "p_value": float(p_values[i]),
                "ci95_lower": float(ci_lower[i]),
                "ci95_upper": float(ci_upper[i]),
            }
        )

    return {
        "n": n,
        "k": k,
        "dof": dof,
        "r_squared": float(r_squared),
        "adj_r_squared": float(adj_r_squared),
        "coefficients": beta,
        "residuals": e,
        "fitted_values": y_pred,
        "summary_table": params_summary,
    }


def compute_spatial_autocorrelation(
    values: np.ndarray,
    geometries: gpd.GeoSeries,
    k_neighbors: int = 5,
    permutations: int = 999,
    random_seed: int = 42,
) -> dict[str, Any]:
    """Compute Global Moran's I test for spatial autocorrelation on tract values or residuals.

    Parameters
    ----------
    values : np.ndarray
        Array of values to test (e.g. regression residuals).
    geometries : gpd.GeoSeries
        Tract polygon geometries.
    k_neighbors : int
        Number of nearest neighbors for spatial weight matrix W.
    permutations : int
        Number of random permutations for empirical pseudo-p-value.
    random_seed : int
        Random seed for reproducibility.

    Returns
    -------
    dict[str, Any]
        Dictionary with Moran's I, expected I, z-score, and permutation p-value.
    """
    v = np.asarray(values, dtype=float)
    valid = ~np.isnan(v)
    v_clean = v[valid]
    geom_clean = geometries[valid].reset_index(drop=True)

    n = len(v_clean)
    if n < k_neighbors + 2:
        return {"morans_i": np.nan, "p_value": np.nan, "message": "Sample size too small."}

    if HAS_PYESDA:
        # Build spatial weights using libpysal KNN
        np.random.seed(random_seed)
        w = libpysal.weights.KNN.from_dataframe(gpd.GeoDataFrame(geometry=geom_clean), k=k_neighbors)
        w.transform = "R"  # Row-standardized weights
        moran = Moran(v_clean, w, transformation="r", permutations=permutations)
        return {
            "morans_i": float(moran.I),
            "expected_i": float(moran.EI),
            "z_score": float(moran.z_sim),
            "p_value": float(moran.p_sim),
            "k_neighbors": k_neighbors,
            "permutations": permutations,
        }
    else:
        # Fallback pure-numpy Moran's I
        logger.info("esda not available; using pure numpy spatial autocorrelation calculation.")
        centroids = np.array([[g.centroid.x, g.centroid.y] for g in geom_clean])
        from scipy.spatial import cKDTree

        tree = cKDTree(centroids)
        _, indices = tree.query(centroids, k=k_neighbors + 1)  # self is index 0

        # Construct row-standardized binary KNN weights
        z = v_clean - np.mean(v_clean)
        n * 1.0  # row standardized sum = n
        lag_z = np.zeros(n)
        for i in range(n):
            neighbors = indices[i, 1:]  # exclude self
            lag_z[i] = np.mean(z[neighbors])

        num = np.sum(z * lag_z)
        denom = np.sum(z**2)
        moran_i = float(num / denom) if denom > 0 else 0.0

        # Permutation test
        rng = np.random.default_rng(random_seed)
        perm_i = []
        for _ in range(permutations):
            z_perm = rng.permutation(z)
            perm_i.append(np.sum(z_perm * lag_z) / denom)

        perm_i = np.array(perm_i)
        p_val = float((np.sum(np.abs(perm_i) >= np.abs(moran_i)) + 1) / (permutations + 1))

        return {
            "morans_i": moran_i,
            "expected_i": float(-1.0 / (n - 1)),
            "z_score": float((moran_i - np.mean(perm_i)) / np.std(perm_i)),
            "p_value": p_val,
            "k_neighbors": k_neighbors,
            "permutations": permutations,
        }


def run_sampling_error_sensitivity(
    b: np.ndarray,
    u: np.ndarray,
    b_moe: np.ndarray,
    u_moe: np.ndarray,
    distances: np.ndarray,
    population: np.ndarray,
    tau: float = 1000.0,
    n_simulations: int = 100,
    random_seed: int = 42,
) -> dict[str, Any]:
    """Assess sensitivity of findings to Census sampling error using published MOEs.

    Census MOEs reflect a 90% confidence level: sigma = MOE / 1.645.
    Perturbs B_i and U_i via truncated Gaussian draws and recomputes Spearman rho and disparity.
    """
    from spatial_justice.mathematics import (
        compute_access_score,
        compute_group_disparity,
        compute_poverty_rate,
    )

    rng = np.random.default_rng(random_seed)

    b_sigma = np.nan_to_num(b_moe / 1.645, nan=0.0)
    u_sigma = np.nan_to_num(u_moe / 1.645, nan=0.0)

    sim_rhos = []
    sim_deltas = []

    for _ in range(n_simulations):
        # Perturb counts
        b_sim = np.maximum(0.0, rng.normal(b, b_sigma))
        u_sim = np.maximum(1.0, rng.normal(u, u_sigma))
        # Ensure b <= u
        b_sim = np.minimum(b_sim, u_sim)

        q_sim = compute_poverty_rate(b_sim, u_sim)
        valid = ~np.isnan(q_sim) & ~np.isnan(distances)

        rho, _ = stats.spearmanr(q_sim[valid], distances[valid])
        sim_rhos.append(rho)

        a_sim = compute_access_score(distances[valid], tau=tau)
        disp = compute_group_disparity(a_sim, q_sim[valid], population[valid])
        sim_deltas.append(disp["disparity_delta"])

    return {
        "n_simulations": n_simulations,
        "spearman_rho_mean": float(np.mean(sim_rhos)),
        "spearman_rho_std": float(np.std(sim_rhos)),
        "spearman_rho_ci95": [float(np.percentile(sim_rhos, 2.5)), float(np.percentile(sim_rhos, 97.5))],
        "disparity_delta_mean": float(np.mean(sim_deltas)),
        "disparity_delta_std": float(np.std(sim_deltas)),
        "disparity_delta_ci95": [float(np.percentile(sim_deltas, 2.5)), float(np.percentile(sim_deltas, 97.5))],
    }
