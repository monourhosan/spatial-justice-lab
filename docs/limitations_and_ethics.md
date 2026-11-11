# Methodological Limitations and Ethical Framework

This document examines the methodological constraints, statistical hazards, and ethical considerations surrounding quantitative spatial accessibility research.

---

## 1. Methodological Constraints and Statistical Caveats

### 1.1 The Ecological Fallacy
Census tracts are aggregate geographic statistical units containing between 1,200 and 8,000 residents. Computing an aggregate tract poverty rate $q_i = B_i / U_i$ does not describe any specific individual:
- High-poverty census tracts contain middle-class and affluent households.
- Low-poverty census tracts contain individuals experiencing acute financial distress.
- A finding that high-poverty census tracts in Chicago have physical proximity to library branches comparable to low-poverty tracts does **not** mean low-income Chicagoans face zero barriers to public services.

### 1.2 The Modifiable Areal Unit Problem (MAUP)
Spatial analysis of aggregated data is fundamentally sensitive to the scale and zonation of geographic boundaries:
- **Scale Effect:** Aggregating data from census blocks to census tracts or community areas smooths variance and alters correlation coefficients.
- **Zonation Effect:** Alternative administrative boundaries (such as Chicago's 77 Community Areas or 50 City Council Wards) may yield different spatial boundaries for socioeconomic groups.
- Census tracts were selected because they represent the finest statistical geography for which detailed American Community Survey (ACS) 5-year poverty universes are reliably estimated.

### 1.3 Absence of Causal Identification
This study is observational and associational. The regression coefficient $\beta_1$ from:

$$
\log(1 + d_i) = \beta_0 + \beta_1 q_i + \beta_2 \log(1 + \text{density}_i) + \beta_3 \log(\text{income}_i) + \epsilon_i
$$

evaluates cross-sectional correlation, not causal impact. The lack of an observed spatial penalty ($\beta_1 \approx 0, p = 0.75$) reflects a century of intentional municipal library planning and civic investment by the Chicago Public Library system, which deliberately placed branch libraries across residential neighborhoods. It cannot be inferred that changing a neighborhood's poverty rate would causally alter library placement.

---

## 2. Spatial Accessibility vs. Substantive Spatial Justice

A central conceptual finding of this study is that **spatial access is not identical to spatial justice**:

1. **Facility Quality and Capacity:** Physical proximity to a branch building does not measure collection size, broadband speed, bilingual staffing, programming budgets, or building maintenance.
2. **Operating Hours and Temporal Justice:** A library branch located 500 meters from a household provides zero utility if its operating hours do not accommodate working shifts or weekend availability.
3. **Micro-Scale Mobility Barriers:** Network distance models calculate centerline street lengths. They do not encode broken pavement, lack of curb cuts, dangerous multilane road crossings, steep railway viaduct underpasses, or winter snow accumulation that can make a 400-meter walk impossible for parents with strollers or wheelchair users.
4. **Social and Psychological Safety:** Physical accessibility ignores perceived neighborhood safety, gang territory boundaries, discriminatory policing, and institutional unwelcomingness that prevent community members from utilizing proximate public spaces.

---

## 3. Ethical Use of Spatial Disadvantage Indices

In Section 4.5 of the methodology, we derived the exploratory spatial disadvantage prioritization indicator:

$$
S_i = q_i (1 - A_i), \qquad 0 \le S_i \le 1.
$$

**Ethical Guidelines for Use:**
- **Prioritization Tool, Not Universal Index:** $S_i$ is an analyst-constructed scoring mechanism designed to help municipal planners identify areas with both high poverty and long travel distances. It must not be marketed as a certified index of "injustice."
- **Preventing Stigmatization:** Quantitative indices combining poverty and service gaps must never be used to label neighborhoods as "blighted" or to justify disinvestment, predatory redevelopment, or school closures.
- **Participatory Validation:** Any municipal planning decision based on quantitative accessibility models must be paired with direct community engagement and participatory budgeting.

---

## 4. Relationship to Morshed (ed.), *Spatial (In)Justice* (Wiley, 2024)

This project was conceptually motivated by Adnan Zillur Morshed (ed.), *Spatial (In)Justice: How Does It Manifest in the Built Environment?* (John Wiley & Sons, 2024).

We explicitly reiterate:
- **Conceptual Motivation, Not Proof:** This computational research operationalizes one specific falsifiable empirical claim inspired by the volume. It does not constitute a mathematical or empirical "proof" or "refutation" of the book's overarching ethical, architectural, and postcolonial essays.
- **Reporting Null Results Faithfully:** Science requires reporting findings honestly when observational data do not match intuitive expectations. In Chicago, public libraries show near-zero correlation with neighborhood poverty ($\rho = +0.020, p = 0.58$), highlighting the success of municipal branch distribution policies while emphasizing that the true frontier of spatial justice lies in service quality, funding equity, and inclusive social infrastructure.
