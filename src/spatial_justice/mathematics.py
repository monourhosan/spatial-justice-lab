"""Mathematical foundations and index formulations for spatial justice modeling.

This module implements the mathematical functions defining:
1. Poverty rates (q_i = B_i / U_i)
2. Bounded exponential accessibility scores (A_i(tau) = exp(-d_i / tau))
3. Population-weighted mean accessibility (A_bar_P)
4. Population-weighted Gini coefficient (G_A)
5. Poverty-gradient quintile disparity (Delta_A)
6. Spatial disadvantage indicator (S_i = q_i * (1 - A_i))
7. Illustrative facility allocation optimization
"""

from __future__ import annotations

from typing import Any

import numpy as np


def compute_poverty_rate(b: np.ndarray, u: np.ndarray) -> np.ndarray:
    """Compute census tract poverty rate: q_i = B_i / U_i.

    Parameters
    ----------
    b : np.ndarray
        Count of persons below the poverty threshold (B_i >= 0).
    u : np.ndarray
        Count of persons in the poverty status determination universe (U_i >= 0).

    Returns
    -------
    np.ndarray
        Poverty rates in [0, 1]. For U_i == 0, returns np.nan.

    Raises
    ------
    ValueError
        If inputs have differing shapes or if any B_i > U_i or negative counts appear.
    """
    b = np.asarray(b, dtype=float)
    u = np.asarray(u, dtype=float)

    if b.shape != u.shape:
        raise ValueError(f"Shape mismatch: b {b.shape} vs u {u.shape}")

    # Check for invalid values (ignoring NaNs)
    valid_mask = ~np.isnan(b) & ~np.isnan(u)
    if np.any(b[valid_mask] < 0) or np.any(u[valid_mask] < 0):
        raise ValueError("Poverty counts cannot be negative.")

    # Guard: persons below poverty cannot exceed universe
    invalid_ratio = (b[valid_mask] > u[valid_mask]) & (u[valid_mask] > 0)
    if np.any(invalid_ratio):
        raise ValueError("Persons below poverty threshold (B_i) exceeds universe (U_i).")

    q = np.full_like(b, fill_value=np.nan)
    positive_u = (u > 0) & valid_mask
    q[positive_u] = b[positive_u] / u[positive_u]
    return q


def compute_access_score(
    distances: np.ndarray,
    tau: float = 1000.0,
    unreachable_val: float = 0.0,
) -> np.ndarray:
    """Compute bounded exponential accessibility score: A_i(tau) = exp(-d_i / tau).

    Mathematical Properties:
    - Bounded: 0 < A_i <= 1 for all finite non-negative d_i.
    - Origin property: A_i(0) = 1.
    - Strictly monotonic decrease: dA_i / dd_i = -(1 / tau) * exp(-d_i / tau) < 0.
    - Asymptotic behavior: lim_{d -> inf} A_i = 0.

    Parameters
    ----------
    distances : np.ndarray
        Shortest walking network distances in meters (d_i >= 0).
    tau : float
        Analytical scale parameter in meters (tau > 0).
    unreachable_val : float
        Score assigned to unreachable or disconnected locations (default 0.0).

    Returns
    -------
    np.ndarray
        Accessibility scores in [0, 1].
    """
    if tau <= 0:
        raise ValueError(f"Scale parameter tau must be strictly positive, got {tau}.")

    d = np.asarray(distances, dtype=float)
    valid_mask = ~np.isnan(d) & (d >= 0)

    scores = np.full_like(d, fill_value=unreachable_val)
    scores[valid_mask] = np.exp(-d[valid_mask] / tau)

    # Infinite distance maps to 0.0
    scores[np.isinf(d)] = unreachable_val
    return scores


def compute_multi_amenity_score(
    distances_dict: dict[str, np.ndarray],
    taus: dict[str, float],
    weights: dict[str, float],
) -> np.ndarray:
    """Compute composite multi-amenity accessibility score: A_i^(multi) = sum_k w_k exp(-d_{ik} / tau_k).

    Parameters
    ----------
    distances_dict : dict[str, np.ndarray]
        Dictionary mapping amenity name to distance array.
    taus : dict[str, float]
        Dictionary mapping amenity name to scale parameter tau.
    weights : dict[str, float]
        Dictionary mapping amenity name to relative weight w_k (sum w_k = 1, w_k >= 0).

    Returns
    -------
    np.ndarray
        Composite multi-amenity score in [0, 1].
    """
    if set(distances_dict.keys()) != set(weights.keys()):
        raise ValueError("Mismatch between amenity distance keys and weight keys.")

    total_weight = sum(weights.values())
    if not np.isclose(total_weight, 1.0, atol=1e-5):
        raise ValueError(f"Weights must sum to 1.0, got {total_weight}.")

    first_key = next(iter(distances_dict))
    composite = np.zeros_like(distances_dict[first_key], dtype=float)

    for k, d in distances_dict.items():
        w = weights[k]
        if w < 0:
            raise ValueError(f"Negative weight {w} for amenity {k}.")
        tau = taus.get(k, 1000.0)
        score_k = compute_access_score(d, tau=tau)
        composite += w * score_k

    return composite


def population_weighted_mean(values: np.ndarray, weights: np.ndarray) -> float:
    """Compute population-weighted mean: bar{A}_P = (1 / P) * sum_{i} P_i A_i.

    Parameters
    ----------
    values : np.ndarray
        Metric values (e.g., accessibility scores A_i).
    weights : np.ndarray
        Population weights (P_i >= 0).

    Returns
    -------
    float
        Population-weighted mean.
    """
    v = np.asarray(values, dtype=float)
    w = np.asarray(weights, dtype=float)

    valid_mask = ~np.isnan(v) & ~np.isnan(w) & (w > 0)
    if not np.any(valid_mask):
        return np.nan

    total_weight = np.sum(w[valid_mask])
    if total_weight <= 0:
        return np.nan

    return float(np.sum(v[valid_mask] * w[valid_mask]) / total_weight)


def population_weighted_gini(values: np.ndarray, weights: np.ndarray) -> float:
    """Compute population-weighted Gini coefficient of accessibility.

    Definition:
        G_A = sum_{i} sum_{j} P_i P_j |A_i - A_j| / (2 * P^2 * bar{A}_P)

    Implementation uses fast O(n log n) sorting algorithm, mathematically
    identical to the pairwise O(n^2) definition:
        Order values such that A_(1) <= A_(2) <= ... <= A_(n).
        Let cum_w_i be cumulative weight and S_i = sum_{k=1}^i w_k A_k.
        G_A = 1 - (sum_{i=1}^n w_i (S_{i-1} + S_i)) / (P * S_n).

    Parameters
    ----------
    values : np.ndarray
        Non-negative values to evaluate.
    weights : np.ndarray
        Non-negative population weights.

    Returns
    -------
    float
        Gini coefficient in [0, 1]. Returns 0.0 if all values are equal or mean is 0.
    """
    v = np.asarray(values, dtype=float)
    w = np.asarray(weights, dtype=float)

    valid_mask = ~np.isnan(v) & ~np.isnan(w) & (w > 0) & (v >= 0)
    v = v[valid_mask]
    w = w[valid_mask]

    n = len(v)
    if n <= 1:
        return 0.0

    total_weight = np.sum(w)
    weighted_mean = np.sum(v * w) / total_weight

    if np.isclose(weighted_mean, 0.0) or np.isclose(np.max(v), np.min(v)):
        return 0.0

    # Sort by value
    order = np.argsort(v)
    v_sorted = v[order]
    w_sorted = w[order]

    cum_w = np.cumsum(w_sorted)
    cum_vw = np.cumsum(v_sorted * w_sorted)

    total_vw = cum_vw[-1]
    if total_vw <= 0:
        return 0.0

    # Trapezoidal integration for Gini from Lorenz curve
    # Lorenz curve: L(F_i) = cum_vw_i / total_vw where F_i = cum_w_i / total_weight
    # Area under curve B = sum 0.5 * (L_{i-1} + L_i) * (F_i - F_{i-1})
    # Gini = 1 - 2*B
    f = np.concatenate([[0.0], cum_w / total_weight])
    l_curve = np.concatenate([[0.0], cum_vw / total_vw])
    auc = np.sum(0.5 * (l_curve[:-1] + l_curve[1:]) * (f[1:] - f[:-1]))

    gini = float(1.0 - 2.0 * auc)
    return max(0.0, min(1.0, gini))


def compute_lorenz_curve(
    values: np.ndarray,
    weights: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """Compute the population-weighted Lorenz curve coordinates (F, L).

    Returns
    -------
    tuple[np.ndarray, np.ndarray]
        (cumulative_population_share, cumulative_accessibility_share).
    """
    v = np.asarray(values, dtype=float)
    w = np.asarray(weights, dtype=float)

    valid_mask = ~np.isnan(v) & ~np.isnan(w) & (w > 0)
    v = v[valid_mask]
    w = w[valid_mask]

    order = np.argsort(v)
    v_sorted = v[order]
    w_sorted = w[order]

    cum_w = np.concatenate([[0.0], np.cumsum(w_sorted)])
    cum_vw = np.concatenate([[0.0], np.cumsum(v_sorted * w_sorted)])

    total_w = cum_w[-1]
    total_vw = cum_vw[-1]

    f_pop = cum_w / total_w
    l_acc = cum_vw / total_vw if total_vw > 0 else f_pop
    return f_pop, l_acc


def compute_group_disparity(
    values: np.ndarray,
    poverty_rates: np.ndarray,
    weights: np.ndarray,
    n_quantiles: int = 5,
) -> dict[str, float]:
    """Compute disparity contrast between the highest and lowest poverty-rate quintiles.

    Delta_A = bar{A}_{H, P} - bar{A}_{L, P}
    where H is top quintile (highest poverty) and L is bottom quintile (lowest poverty).

    Parameters
    ----------
    values : np.ndarray
        Amenity metric (e.g. accessibility score A_i or walking distance d_i).
    poverty_rates : np.ndarray
        Tract poverty rates q_i.
    weights : np.ndarray
        Tract population counts P_i.
    n_quantiles : int
        Number of quantile groups (default 5 for quintiles).

    Returns
    -------
    dict[str, float]
        Dictionary with high-group mean, low-group mean, absolute disparity,
        and group sample sizes.
    """
    v = np.asarray(values, dtype=float)
    q = np.asarray(poverty_rates, dtype=float)
    w = np.asarray(weights, dtype=float)

    valid = ~np.isnan(v) & ~np.isnan(q) & ~np.isnan(w) & (w > 0)
    v, q, w = v[valid], q[valid], w[valid]

    # Rank-based quantile binning across tracts
    # Using pandas qcut or numpy percentile
    q_low_thresh = np.percentile(q, 100.0 / n_quantiles)
    q_high_thresh = np.percentile(q, 100.0 * (n_quantiles - 1) / n_quantiles)

    low_mask = q <= q_low_thresh
    high_mask = q >= q_high_thresh

    mean_low = population_weighted_mean(v[low_mask], w[low_mask])
    mean_high = population_weighted_mean(v[high_mask], w[high_mask])
    disparity = mean_high - mean_low

    return {
        "mean_high_poverty_q5": mean_high,
        "mean_low_poverty_q1": mean_low,
        "disparity_delta": disparity,
        "n_tracts_q1": int(np.sum(low_mask)),
        "n_tracts_q5": int(np.sum(high_mask)),
        "pop_q1": float(np.sum(w[low_mask])),
        "pop_q5": float(np.sum(w[high_mask])),
    }


def spatial_disadvantage_indicator(
    poverty_rates: np.ndarray,
    access_scores: np.ndarray,
) -> np.ndarray:
    """Compute analyst-constructed spatial disadvantage prioritization score: S_i = q_i * (1 - A_i).

    Properties:
    - Bounded in [0, 1] since 0 <= q_i <= 1 and 0 <= A_i <= 1 => 0 <= (1 - A_i) <= 1.
    - S_i = 1 occurs only if a neighborhood has 100% poverty rate (q_i = 1) and zero access (A_i = 0).
    - S_i = 0 if either poverty rate is 0 or accessibility is maximal (1.0).

    Note: This is an exploratory prioritization index, not a certified universal index of injustice.
    """
    q = np.asarray(poverty_rates, dtype=float)
    a = np.asarray(access_scores, dtype=float)

    if q.shape != a.shape:
        raise ValueError("Shape mismatch between poverty rates and access scores.")

    s = q * (1.0 - a)
    return np.clip(s, 0.0, 1.0)


def simulate_optimal_facility_addition(
    candidate_coords: np.ndarray,
    origin_coords: np.ndarray,
    current_distances: np.ndarray,
    population: np.ndarray,
    poverty_rates: np.ndarray,
    tau: float = 1000.0,
    equity_weight: float = 0.5,
) -> dict[str, Any]:
    """Simulate an illustrative optimal placement of ONE additional facility.

    Objective:
        max_{c in C} sum_i P_i (1 + w_e * q_i) * [ A_i^{(+c)} - A_i ]
    where A_i^{(+c)} = exp(-min(d_i, d(o_i, c)) / tau).

    Parameters
    ----------
    candidate_coords : np.ndarray
        Array of (x, y) coordinates for eligible candidate locations. Shape (M, 2).
    origin_coords : np.ndarray
        Array of (x, y) coordinates for tract origins. Shape (N, 2).
    current_distances : np.ndarray
        Current shortest distance to existing facilities. Shape (N,).
    population : np.ndarray
        Tract population counts P_i. Shape (N,).
    poverty_rates : np.ndarray
        Tract poverty rates q_i. Shape (N,).
    tau : float
        Analytical scale parameter.
    equity_weight : float
        Relative weighting for high-poverty areas (w_e >= 0).

    Returns
    -------
    dict[str, Any]
        Dictionary with optimal candidate index, coordinate, total access gain,
        and simulated new accessibility array.
    """
    from scipy.spatial.distance import cdist

    # Distance from all origins to all candidates: (N, M)
    dist_to_candidates = cdist(origin_coords, candidate_coords)

    current_access = np.exp(-current_distances / tau)
    weights = population * (1.0 + equity_weight * np.nan_to_num(poverty_rates, nan=0.0))

    best_idx = -1
    best_gain = -1.0
    best_new_access = None

    for c_idx in range(candidate_coords.shape[0]):
        cand_dist = dist_to_candidates[:, c_idx]
        new_dist = np.minimum(current_distances, cand_dist)
        new_access = np.exp(-new_dist / tau)
        gain = float(np.sum(weights * (new_access - current_access)))

        if gain > best_gain:
            best_gain = gain
            best_idx = c_idx
            best_new_access = new_access

    return {
        "best_candidate_idx": best_idx,
        "best_candidate_coord": candidate_coords[best_idx].tolist() if best_idx >= 0 else None,
        "total_weighted_gain": best_gain,
        "new_access": best_new_access,
    }

