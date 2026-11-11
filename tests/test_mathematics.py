"""Unit tests for core mathematical formulas and properties."""

import numpy as np
import pytest

from spatial_justice.mathematics import (
    compute_access_score,
    compute_group_disparity,
    compute_lorenz_curve,
    compute_multi_amenity_score,
    compute_poverty_rate,
    population_weighted_gini,
    population_weighted_mean,
    spatial_disadvantage_indicator,
)


def test_poverty_rate_basic():
    b = np.array([10.0, 50.0, 0.0])
    u = np.array([100.0, 100.0, 50.0])
    q = compute_poverty_rate(b, u)
    assert np.allclose(q, [0.1, 0.5, 0.0])


def test_poverty_rate_zero_universe():
    b = np.array([0.0, 10.0])
    u = np.array([0.0, 100.0])
    q = compute_poverty_rate(b, u)
    assert np.isnan(q[0])
    assert q[1] == 0.1


def test_poverty_rate_validation_guards():
    # Negative counts
    with pytest.raises(ValueError, match="cannot be negative"):
        compute_poverty_rate(np.array([-5.0]), np.array([100.0]))

    # b > u
    with pytest.raises(ValueError, match="exceeds universe"):
        compute_poverty_rate(np.array([150.0]), np.array([100.0]))


def test_accessibility_score_properties():
    distances = np.array([0.0, 500.0, 1000.0, 2000.0, 5000.0])
    tau = 1000.0
    scores = compute_access_score(distances, tau=tau)

    # 1. Origin property: A(0) = 1
    assert scores[0] == 1.0

    # 2. Strict bounds: 0 < A <= 1
    assert np.all((scores > 0.0) & (scores <= 1.0))

    # 3. Monotonic decrease
    assert np.all(np.diff(scores) < 0)

    # 4. Known value: A(tau) = exp(-1) = 0.36787944117
    assert np.isclose(scores[2], np.exp(-1.0))

    # 5. Sensitivity to tau: smaller tau drops off faster
    scores_500 = compute_access_score(distances, tau=500.0)
    scores_2000 = compute_access_score(distances, tau=2000.0)
    assert scores_500[1] < scores[1] < scores_2000[1]


def test_population_weighted_mean():
    values = np.array([1.0, 2.0, 3.0])
    weights = np.array([10.0, 20.0, 70.0])
    # Expected: (1*10 + 2*20 + 3*70) / 100 = (10 + 40 + 210) / 100 = 2.6
    wm = population_weighted_mean(values, weights)
    assert np.isclose(wm, 2.6)

    # Invariance to weight scaling
    wm_scaled = population_weighted_mean(values, weights * 5.0)
    assert np.isclose(wm_scaled, 2.6)


def test_population_weighted_gini():
    # Case 1: Complete equality -> Gini = 0
    equal_vals = np.array([0.5, 0.5, 0.5, 0.5])
    weights = np.array([100.0, 200.0, 300.0, 400.0])
    assert np.isclose(population_weighted_gini(equal_vals, weights), 0.0)

    # Case 2: Hand-calculated 2-group unequal case
    # Group 1: v=0, w=50; Group 2: v=10, w=50
    # Mean = 5. Pairwise difference:
    # 50*50*|0-0| + 50*50*|0-10| + 50*50*|10-0| + 50*50*|10-10| = 2500*10 + 2500*10 = 50000
    # Denominator: 2 * (100)^2 * 5 = 2 * 10000 * 5 = 100000
    # Gini = 50000 / 100000 = 0.5
    v_test = np.array([0.0, 10.0])
    w_test = np.array([50.0, 50.0])
    assert np.isclose(population_weighted_gini(v_test, w_test), 0.5)

    # Case 3: Pairwise vs Sorted implementation consistency on random array
    rng = np.random.default_rng(42)
    rand_v = rng.uniform(0.1, 1.0, size=50)
    rand_w = rng.uniform(100, 5000, size=50)

    # Direct pairwise calculation:
    p = np.sum(rand_w)
    mean_v = np.sum(rand_v * rand_w) / p
    diff_matrix = np.abs(rand_v[:, None] - rand_v[None, :])
    weight_matrix = rand_w[:, None] * rand_w[None, :]
    pairwise_gini = np.sum(diff_matrix * weight_matrix) / (2.0 * (p**2) * mean_v)

    fast_gini = population_weighted_gini(rand_v, rand_w)
    assert np.isclose(fast_gini, pairwise_gini, atol=1e-3)


def test_group_disparity():
    # High poverty should have worse access in synthetic design
    # Tracts 0-19: low poverty q=0.05, access=0.9
    # Tracts 20-79: middle poverty
    # Tracts 80-99: high poverty q=0.40, access=0.3
    q = np.linspace(0.01, 0.50, 100)
    a = 1.0 - 1.5 * q  # inverse relationship
    pop = np.full(100, fill_value=1000.0)

    disp = compute_group_disparity(a, q, pop, n_quantiles=5)
    assert disp["mean_low_poverty_q1"] > disp["mean_high_poverty_q5"]
    assert disp["disparity_delta"] < 0  # Worse access in high poverty
    assert disp["n_tracts_q1"] == 20
    assert disp["n_tracts_q5"] == 20


def test_spatial_disadvantage_indicator():
    q = np.array([0.0, 0.5, 1.0, 0.5])
    a = np.array([0.0, 1.0, 0.0, 0.5])
    # S = q * (1 - a)
    # 0*(1-0) = 0
    # 0.5*(1-1) = 0
    # 1.0*(1-0) = 1.0
    # 0.5*(1-0.5) = 0.25
    s = spatial_disadvantage_indicator(q, a)
    assert np.allclose(s, [0.0, 0.0, 1.0, 0.25])


def test_lorenz_curve():
    vals = np.array([10.0, 20.0, 30.0, 40.0])
    weights = np.array([1.0, 1.0, 1.0, 1.0])
    f, l_c = compute_lorenz_curve(vals, weights)
    assert f[0] == 0.0 and l_c[0] == 0.0
    assert f[-1] == 1.0 and l_c[-1] == 1.0
    assert np.all(np.diff(f) > 0)
    assert np.all(np.diff(l_c) >= 0)


def test_multi_amenity_score():
    dist_dict = {
        "libraries": np.array([0.0, 1000.0]),
        "parks": np.array([500.0, 500.0]),
    }
    taus = {"libraries": 1000.0, "parks": 500.0}
    weights = {"libraries": 0.6, "parks": 0.4}

    score = compute_multi_amenity_score(dist_dict, taus, weights)
    # Item 0: 0.6 * exp(-0/1000) + 0.4 * exp(-500/500) = 0.6*1 + 0.4*exp(-1)
    expected_0 = 0.6 * 1.0 + 0.4 * np.exp(-1.0)
    assert np.isclose(score[0], expected_0)

