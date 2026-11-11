# Mathematical Model of Spatial Accessibility and Disparity

This document outlines the formal mathematical formulations, operational definitions, parameter declarations, and analytical assumptions underlying the spatial justice modeling system.

---

## 1. Indexing and Geographic Primitives

Let the study area be partitioned into $n$ contiguous spatial census units (tracts) indexed by $i \in \{1, 2, \dots, n\}$, and let public amenities (library branches) be indexed by $j \in \mathcal{L} = \{1, 2, \dots, m\}$.

- $o_i \in \mathbb{R}^2$: Representative origin point for tract $i$ in a projected metric coordinate reference system (EPSG:26971, NAD83 / Illinois East meters). By default, $o_i$ is generated via `representative_point()`, ensuring it falls strictly within the polygon boundary of tract $i$.
- $f_j \in \mathbb{R}^2$: Geocoded geographic location of facility $j \in \mathcal{L}$.
- $G = (V, E, w)$: A walkable pedestrian street and path network graph where $V$ denotes intersections/endpoints, $E \subseteq V \times V$ denotes walkable segments, and $w: E \to \mathbb{R}^+$ denotes physical edge lengths in meters.
- $P_i \ge 0$: ACS estimate of total population in tract $i$. Total population is $P = \sum_{i=1}^n P_i$.
- $U_i \ge 0$: ACS poverty status determination universe in tract $i$.
- $B_i \ge 0$: ACS count of persons classified below the federal poverty threshold in tract $i$, where $0 \le B_i \le U_i$.

---

## 2. Mathematical Formulations

### Equation 1: Tract Poverty Rate

The socioeconomic disadvantage of tract $i$ is operationalized through the proportion of residents living below the federal poverty threshold:

$$
q_i = \frac{B_i}{U_i}, \qquad U_i > 0, \quad 0 \le q_i \le 1.
$$

**Boundary condition:** If $U_i = 0$ (e.g., in unpopulated industrial zones, rail yards, airports, or municipal water bodies), $q_i$ is undefined and recorded as `NaN`.

### Equation 2: Shortest-Path Network Distance to Nearest Facility

Let $d_G(u, v)$ represent the shortest path distance in meters between graph nodes $u, v \in V$ on graph $G$. Let $\pi(p) \in V$ be the nearest graph node to point $p \in \mathbb{R}^2$. The walking distance from tract origin $o_i$ to facility $f_j$ is:

$$
d_G(o_i, f_j) = \|o_i - \pi(o_i)\|_2 + \text{dist}_G(\pi(o_i), \pi(f_j)) + \|f_j - \pi(f_j)\|_2.
$$

The distance to the *closest* eligible public library is defined as:

$$
d_i = \min_{j \in \mathcal{L}} d_G(o_i, f_j).
$$

Units are expressed in physical meters ($m$). Optionally, estimated walking travel time in minutes is computed assuming an average unimpeded walking speed of $v_{\text{walk}} = 1.2 \text{ m/s}$ ($4.32 \text{ km/h}$):

$$
t_i = \frac{d_i}{60 \cdot v_{\text{walk}}}.
$$

### Equation 3: Bounded Exponential Accessibility Score

To convert unbounded physical distance ($d_i \in [0, \infty)$) into a normalized accessibility index reflecting pedestrian spatial decay, we define the exponential decay score:

$$
A_i(\tau) = \exp\left(-\frac{d_i}{\tau}\right), \qquad \tau > 0, \quad d_i \ge 0.
$$

**Analytical Properties:**
1. **Bounded:** $0 < A_i(\tau) \le 1$ for all finite $d_i \ge 0$.
2. **Origin Normalization:** $A_i(0) = 1$.
3. **Strict Monotonicity:** $\frac{\partial A_i}{\partial d_i} = -\frac{1}{\tau}\exp\left(-\frac{d_i}{\tau}\right) < 0$.
4. **Asymptotic Decay:** $\lim_{d_i \to \infty} A_i(\tau) = 0$.
5. **Scale Parameter $\tau$:** Declared prior to analysis. The default is $\tau = 1,000 \text{ m}$ (representing an approximate 12–15 minute walk), with sensitivity evaluations at $\tau = 500 \text{ m}$ and $\tau = 2,000 \text{ m}$.

### Equation 4: Multi-Amenity Composite Accessibility (Secondary Metric)

When multiple amenity types $k \in \{1, \dots, K\}$ are evaluated (e.g., libraries and parks), composite accessibility is defined by a convex linear combination:

$$
A_i^{(\text{multi})} = \sum_{k=1}^K w_k \exp\left(-\frac{d_{ik}}{\tau_k}\right), \qquad w_k \ge 0, \quad \sum_{k=1}^K w_k = 1.
$$

*Value Judgment Note:* Weights $w_k$ reflect normative prioritization of amenities rather than objective physical laws.

### Equation 5: Population-Weighted Mean Accessibility

To evaluate overall municipal service delivery weighted by resident distribution:

$$
\bar{A}_P = \frac{1}{P} \sum_{i=1}^n P_i A_i, \qquad P = \sum_{i=1}^n P_i.
$$

### Equation 6: Population-Weighted Gini Coefficient of Accessibility

Distributional inequality of modeled accessibility across residents is quantified by the population-weighted Gini coefficient:

$$
G_A = \frac{\sum_{i=1}^n \sum_{k=1}^n P_i P_k |A_i - A_k|}{2 P^2 \bar{A}_P}.
$$

For computational efficiency on large $n$, sorting tracts by accessibility $A_{(1)} \le A_{(2)} \le \dots \le A_{(n)}$ allows computation via the cumulative Lorenz curve area:

$$
G_A = 1 - 2 \int_0^1 L(F) \, dF.
$$

### Equation 7: Poverty-Gradient Quintile Disparity

Let $H$ and $L$ represent the sets of census tracts comprising the highest-poverty quintile (Q5) and lowest-poverty quintile (Q1), respectively. The population-weighted access disparity is:

$$
\Delta_A = \frac{\sum_{i \in H} P_i A_i}{\sum_{i \in H} P_i} - \frac{\sum_{i \in L} P_i A_i}{\sum_{i \in L} P_i}.
$$

- $\Delta_A < 0$: Indicates lower modeled access in high-poverty neighborhoods.
- $\Delta_A > 0$: Indicates higher modeled access in high-poverty neighborhoods.
- $\Delta_A \approx 0$: Indicates demographic parity in modeled physical access.

### Equation 8: Spatial Disadvantage Prioritization Score (Descriptive Only)

As an exploratory indicator for municipal service prioritization:

$$
S_i = q_i (1 - A_i), \qquad 0 \le S_i \le 1.
$$

- $S_i = 1$ if and only if tract poverty rate is 100% ($q_i = 1$) and accessibility is 0 ($A_i = 0$).
- $S_i = 0$ if either poverty is 0 ($q_i = 0$) or access is maximal ($A_i = 1$).

### Equation 9: Associational Econometric Model

To examine conditional associations while controlling for urban density and income:

$$
\log(1 + d_i) = \beta_0 + \beta_1 q_i + \beta_2 \log(1 + \text{density}_i) + \beta_3 \log(\text{income}_i) + \epsilon_i,
$$

where $\text{density}_i = P_i / \text{area\_km2}_i$ and covariance is estimated using White's heteroskedasticity-consistent estimator (HC1):

$$
V_{\text{HC1}} = \frac{n}{n - k} (X^T X)^{-1} \left( \sum_{i=1}^n e_i^2 x_i x_i^T \right) (X^T X)^{-1}.
$$

---

## 3. Variable Dictionary and Code Cross-Reference

| Formula Symbol | Description | Units | Source Field | Python Function / Module |
|---|---|---|---|---|
| $B_i$ | Persons below poverty | Count | `B17001_002E` | `cleaning.clean_census_demographics` |
| $U_i$ | Poverty universe | Count | `B17001_001E` | `cleaning.clean_census_demographics` |
| $q_i$ | Tract poverty rate | $[0, 1]$ | Computed | `mathematics.compute_poverty_rate` |
| $P_i$ | Total population | Count | `B01003_001E` | `cleaning.clean_census_demographics` |
| $o_i$ | Tract representative origin | Projected coords | TIGER geometry | `geography.prepare_chicago_tracts` |
| $f_j$ | Library branch facility | Projected coords | Socrata `location` | `cleaning.clean_chicago_libraries` |
| $d_i$ | Shortest walking distance | Meters | Street Graph $G$ | `routing.compute_facility_distances` |
| $A_i(\tau)$ | Exponential access score | $(0, 1]$ | Computed | `mathematics.compute_access_score` |
| $\bar{A}_P$ | Pop-weighted mean access | $(0, 1]$ | Computed | `mathematics.population_weighted_mean` |
| $G_A$ | Pop-weighted Gini | $[0, 1]$ | Computed | `mathematics.population_weighted_gini` |
| $\Delta_A$ | Quintile disparity contrast | $[-1, 1]$ | Computed | `mathematics.compute_group_disparity` |
| $S_i$ | Spatial disadvantage score | $[0, 1]$ | Computed | `mathematics.spatial_disadvantage_indicator` |
| $\beta_j$ | OLS regression coefficients | Various | Estimated | `statistics.fit_robust_ols` |
| $I$ | Global Moran's I | $[-1, 1]$ | Residuals $\epsilon_i$ | `statistics.compute_spatial_autocorrelation` |
