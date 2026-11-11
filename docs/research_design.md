# Research Design: Spatial Equity and Public Amenity Access

## 1. Intellectual Motivation and Conceptual Starting Point

This empirical study is conceptually inspired by the edited volume:
**Adnan Zillur Morshed (ed.), *Spatial (In)Justice: How Does It Manifest in the Built Environment?*, John Wiley & Sons, 2024 (ISBN: 978-1394294664).**

The volume examines how architecture, urban planning, infrastructure, and built spatial form organize power, privilege, and human opportunity, emphasizing the experiences of marginalized communities and the ethical obligations of spatial practitioners.

To engage rigorously with this theoretical literature, this project operationalizes and empirically evaluates a central, testable proposition derived from spatial justice theory:

> **Core Hypothesis:** Neighborhoods with greater socioeconomic disadvantage exhibit poorer spatial access to essential public amenities, even when those amenities are critical for equitable civic life.

---

## 2. Study Area and Target Amenity Selection

### Why Chicago, Illinois?
Chicago was selected not because of an expected or predetermined outcome, but due to several essential data-quality and methodological criteria:
1. **High-Resolution Municipal Open Data:** The City of Chicago maintains an active, public Socrata open data portal providing verified point locations and operating metadata for municipal facilities.
2. **Standardized Census Geographies:** Cook County census tracts are well-documented by the U.S. Census Bureau with complete 5-year American Community Survey (ACS) detailed demographic tables.
3. **Established Pedestrian Infrastructure:** Chicago's classic urban grid street layout enables accurate, network-based pedestrian distance computations without arbitrary geometric distortions.

### Why Public Libraries?
Public libraries were designated as the primary amenity because:
1. **Universal Democratic Goods:** Unlike private commercial services or fee-based municipal amenities, public libraries provide free, universal educational, technological, and civic resources.
2. **Explicit Municipal Mandate:** The Chicago Public Library (CPL) system is explicitly tasked with providing city-wide neighborhood service delivery.
3. **Geographic Verifiability:** Unlike large public parks, which may lack defined entrances, library branches are well-defined point destinations where patron access occurs through documented physical doors.

---

## 3. Geographic Units and Containment Rules

- **Spatial Unit:** 2020 Census Tracts (vintages aligned with 2019–2023 ACS estimates).
- **Origin Points ($o_i$):** Tract representative points (`geometry.representative_point()`), which guarantee that origin coordinates lie strictly within the interior of the tract polygon, avoiding errors where polygon centroids fall outside irregularly shaped or crescent tracts.
- **Municipal Containment:** Primary analysis includes tracts whose representative point falls within the Chicago municipal corporate boundary ($n = 781$ total tracts, $n = 778$ populated tracts with valid demographic data).
- **Sensitivity Check:** Secondary analysis evaluates boundary intersection with $\ge 10\%$ area overlap to ensure findings are robust to border tract inclusion rules.

---

## 4. Preregistered Hypotheses

Prior to inspecting empirical results, the following falsifiable hypotheses were declared:

1. **$H_0$ (Null Association):** There is no monotonic tract-level association between tract poverty rate ($q_i$) and nearest-library walking distance ($d_i$) ($\rho = 0$).
2. **$H_1a$ (Directional Distance Disparity):** Higher-poverty census tracts tend to have systematically longer walking distances to the nearest library ($\rho > 0$).
3. **$H_1b$ (Directional Access Disparity):** Higher-poverty census tracts tend to have lower modeled accessibility scores ($\rho(q, A) < 0$).
4. **$H_2$ (Quintile Disparity Contrast):** The population-weighted mean accessibility in the highest-poverty quintile is strictly lower than in the lowest-poverty quintile ($\Delta_A < 0$).

---

## 5. Scope and Limitations of Case-Study Generalization

A critical principle of empirical urban science is that **a single-city case study cannot establish a global law**:
- Chicago possesses a unique 150-year history of civic investment, progressive library branch construction programs, and municipal neighborhood planning.
- Findings observed in Chicago cannot be assumed to apply automatically to other urban contexts (such as sunbelt sprawling metropolitan areas or cities in the Global South like Dhaka, Bangladesh), where rapid informal urbanization, infrastructure deficits, and municipal governance models differ substantially.
- The pipeline architecture developed here is modular and reusable, allowing future researchers to execute identical empirical tests in other cities where compatible open data exist.
