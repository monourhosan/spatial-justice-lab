# Empirical Methodology: Computational Spatial Analysis

This document provides a technical walkthrough of the data processing pipeline, network routing algorithms, econometric modeling, and spatial diagnostic procedures.

---

## 1. Data Pipeline Architecture

The computational system is organized into modular Python stages executed sequentially:

```
[Raw Public APIs] 
      │
      ▼
1. Acquisition & Secure Caching (data/raw/)
      │
      ▼
2. Schema Standardization & Demographic Cleaning
      │
      ▼
3. Spatial Reprojection & Boundary Containment (EPSG:26971)
      │
      ▼
4. Graph Construction & Multi-Source Dijkstra Routing
      │
      ▼
5. Mathematical Indexing (A_i, G_A, Delta_A, S_i)
      │
      ▼
6. Statistical Estimation (Spearman, OLS HC1, Moran's I, MOE Sensitivity)
      │
      ▼
7. Publication Cartography & Structured Reporting (results/)
```

---

## 2. Spatial Projection and Geometric Alignment

All spatial geometries are projected from geographic coordinates (WGS 84, EPSG:4326) to the metric projected coordinate system:
**NAD83 / Illinois East (EPSG:26971)**.

### Metric SI Units
- Linear distances: meters ($m$)
- Land areas: square meters ($m^2$) and square kilometers ($\text{km}^2$)
- Population densities: residents per square kilometer ($\text{persons/km}^2$)

### Tract Representative Origins vs. Centroids
To prevent origin points from falling outside tracts with concave, crescent, or non-convex geometries (common along waterways and railway corridors), origin coordinates $o_i$ are generated using `geometry.representative_point()`. A representative point is mathematically guaranteed to intersect the interior of the polygon. Sensitivity evaluations also test polygon centroids (`geometry.centroid`).

---

## 3. Network Routing via Multi-Source Dijkstra

### Graph Planarization and Connectivity
1. Street centerlines covering the municipal footprint plus a 500-meter buffer are extracted, excluding non-pedestrian limited-access freeways.
2. Intersecting line segments are noded via planar geometric intersection (`shapely.node`), ensuring that all physical intersections share identical node coordinates.
3. Node coordinates are indexed in a spatial `cKDTree` for sub-millisecond coordinate snapping.

### Reverse Multi-Source Dijkstra Algorithm
Let $\mathcal{F} = \{\pi(f_1), \dots, \pi(f_m)\} \subset V$ represent the set of graph nodes corresponding to all $m = 82$ library branches.  
Rather than running $n$ individual point-to-point Dijkstra queries (which scales as $O(n \cdot (|V| + |E| \log |V|))$), we execute a **multi-source Dijkstra search** rooted simultaneously at all facility nodes $\mathcal{F}$ on the undirected walkable street graph:

$$
\text{dist\_map}(v) = \min_{u \in \mathcal{F}} d_G(u, v) \quad \forall v \in V.
$$

This single pass scales as $O((|V| + |E|) \log |V|)$ and determines the exact shortest walking distance to the nearest library for all 88,549 nodes across the entire city in under 2 seconds.

For tract origin $o_i$ snapped to node $\pi(o_i)$, total walking distance is:

$$
d_i = \|o_i - \pi(o_i)\|_2 + \text{dist\_map}(\pi(o_i)).
$$

If a tract origin is located in an isolated graph component disconnected from all libraries (observed in 2 border tracts across the entire municipality), a Euclidean distance with calibrated urban circuity factor (1.3) is applied as a documented fallback.

---

## 4. Econometric and Spatial Autocorrelation Modeling

### Nonparametric Correlation
To test hypothesis $H_0$ without imposing linear parametric assumptions, the Spearman rank correlation coefficient $\rho(q_i, d_i)$ is computed. Empirical 95% confidence intervals are estimated via 1,000 bootstrap resamples.

### Heteroskedasticity-Robust OLS Regression
To test conditional associations while controlling for urban compactness and income:

$$
\log(1 + d_i) = \beta_0 + \beta_1 q_i + \beta_2 \log(1 + \text{density}_i) + \beta_3 \log(\text{income}_i) + \epsilon_i.
$$

Standard errors are estimated using White's heteroskedasticity-consistent covariance matrix (HC1 degrees-of-freedom adjustment):

$$
V_{\text{HC1}} = \frac{n}{n - k} (X^T X)^{-1} \left( \sum_{i=1}^n e_i^2 x_i x_i^T \right) (X^T X)^{-1}.
$$

### Global Moran's I Residual Diagnostic
To evaluate whether regression residuals violate the classical I.I.D. assumption due to spatial dependence, Global Moran's I is computed using a 5-nearest-neighbor spatial weights matrix $W$ with row standardization ($w_{ij} = 1/5$ if $j \in \mathcal{N}_5(i)$, 0 otherwise):

$$
I = \frac{n}{\sum_i \sum_j w_{ij}} \frac{\sum_i \sum_j w_{ij} (e_i - \bar{e})(e_j - \bar{e})}{\sum_i (e_i - \bar{e})^2}.
$$

Statistical significance is assessed via a 999-iteration random spatial permutation test.

---

## 5. Margin of Error (MOE) Sensitivity Simulation

Because the American Community Survey relies on sample survey estimates, each demographic variable carries an associated margin of error. Using the published 90% confidence margins of error ($M_B, M_U$), standard errors are derived as $\sigma = MOE / 1.645$.

In each of 100 Monte Carlo perturbation iterations:
1. $B_i^{(b)} \sim \max(0, \mathcal{N}(B_i, \sigma_{B, i}^2))$
2. $U_i^{(b)} \sim \max(1, \mathcal{N}(U_i, \sigma_{U, i}^2))$
3. $B_i^{(b)}$ is capped at $U_i^{(b)}$
4. Recomputed $\rho^{(b)}$ and $\Delta_A^{(b)}$ are evaluated to confirm that sampling uncertainty does not alter substantive conclusions.
