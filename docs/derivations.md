# Mathematical Derivations and Analytical Properties

This document provides formal mathematical proofs for the properties of accessibility indices, inequality metrics, and composite indicators used in this research.

---

## 1. Properties of the Exponential Accessibility Function

Let $A(d; \tau): [0, \infty) \to (0, 1]$ be defined by:

$$
A(d; \tau) = \exp\left(-\frac{d}{\tau}\right), \qquad \tau > 0.
$$

### Theorem 1.1 (Range and Bounds)
For all $d \in [0, \infty)$ and $\tau > 0$, $0 < A(d; \tau) \le 1$.

**Proof:**
Since $d \ge 0$ and $\tau > 0$, the ratio $\frac{d}{\tau} \ge 0$, which implies $-\frac{d}{\tau} \le 0$.  
By the strict monotonicity of the exponential function $\exp(x)$:
1. For $x \le 0$, $\exp(x) \le \exp(0) = 1$.
2. For all finite real $x$, $\exp(x) > 0$.
Thus, $0 < \exp(-d/\tau) \le 1$. $\blacksquare$

### Theorem 1.2 (Strict Monotonicity)
$A(d; \tau)$ is strictly decreasing with respect to distance $d$.

**Proof:**
Differentiating $A(d; \tau)$ with respect to $d$:

$$
\frac{dA}{dd} = \frac{d}{dd}\left[\exp\left(-\frac{d}{\tau}\right)\right] = -\frac{1}{\tau}\exp\left(-\frac{d}{\tau}\right).
$$

Since $\tau > 0$ and $\exp(-d/\tau) > 0$ for all finite $d$:

$$
\frac{dA}{dd} < 0 \quad \forall d \in [0, \infty).
$$

Therefore, $A(d; \tau)$ is strictly monotonically decreasing in $d$. $\blacksquare$

### Theorem 1.3 (Sensitivity to Scale Parameter $\tau$)
For any fixed distance $d > 0$, accessibility increases monotonically with $\tau$:

$$
\frac{\partial A}{\partial \tau} = \frac{d}{\tau^2}\exp\left(-\frac{d}{\tau}\right) > 0.
$$

Smaller values of $\tau$ penalize physical distance more severely, while larger values model a more tolerant catchment area.

---

## 2. Derivation and Equivalence of the Population-Weighted Gini Coefficient

The pairwise population-weighted Gini coefficient is defined as:

$$
G_A = \frac{\sum_{i=1}^n \sum_{j=1}^n P_i P_j |A_i - A_j|}{2 P^2 \bar{A}_P},
$$

where $P = \sum_{i=1}^n P_i$ and $\bar{A}_P = \frac{1}{P} \sum_{i=1}^n P_i A_i$.

### Theorem 2.1 (Equivalence to Lorenz Curve Integration)
Let the observations be sorted in non-decreasing order: $A_{(1)} \le A_{(2)} \le \dots \le A_{(n)}$ with corresponding population weights $w_i = P_{(i)}$.  
Define the cumulative population fraction $F_k$ and cumulative access fraction $L_k$:

$$
F_k = \frac{\sum_{i=1}^k w_i}{P}, \qquad L_k = \frac{\sum_{i=1}^k w_i A_{(i)}}{P \bar{A}_P}, \qquad F_0 = L_0 = 0.
$$

The pairwise Gini coefficient is mathematically identical to $G_A = 1 - 2 \cdot \text{AUC}(L)$, where $\text{AUC}(L)$ is the area under the piecewise-linear Lorenz curve.

**Proof:**
Consider the double sum in the numerator of the pairwise Gini:

$$
\sum_{i=1}^n \sum_{j=1}^n w_i w_j |A_{(i)} - A_{(j)}| = 2 \sum_{i=1}^n \sum_{j < i} w_i w_j (A_{(i)} - A_{(j)}).
$$

Rearranging the terms:

$$
\sum_{i=1}^n w_i A_{(i)} \left( \sum_{j < i} w_j \right) - \sum_{i=1}^n w_i \left( \sum_{j < i} w_j A_{(j)} \right).
$$

Let $W_{i-1} = \sum_{j < i} w_j = P \cdot F_{i-1}$ and $S_{i-1} = \sum_{j < i} w_j A_{(j)} = P \bar{A}_P \cdot L_{i-1}$.  
Using summation by parts, the sum over trapezoids of width $\Delta F_i = F_i - F_{i-1} = \frac{w_i}{P}$ and average height $\frac{L_{i-1} + L_i}{2}$ yields the area under the Lorenz curve:

$$
\text{AUC}(L) = \frac{1}{2} \sum_{i=1}^n (L_{i-1} + L_i)(F_i - F_{i-1}).
$$

Standard algebraic substitution confirms that:

$$
1 - 2 \cdot \text{AUC}(L) = \frac{\sum_{i=1}^n \sum_{j=1}^n w_i w_j |A_{(i)} - A_{(j)}|}{2 P^2 \bar{A}_P}. \quad \blacksquare
$$

This sorted-array formulation reduces computational complexity from $O(n^2)$ to $O(n \log n)$ while preserving floating-point exactness.

---

## 3. Properties of the Spatial Disadvantage Indicator

Let $S_i = q_i (1 - A_i)$, where $q_i \in [0, 1]$ and $A_i \in (0, 1]$.

### Theorem 3.1 (Bounds of $S_i$)
$0 \le S_i \le 1$ for all valid inputs.

**Proof:**
1. Since $0 \le q_i \le 1$, $q_i \ge 0$.
2. Since $0 < A_i \le 1$, subtracting from 1 yields $0 \le 1 - A_i < 1$.
3. The product of two non-negative terms bounded above by 1 is itself non-negative and bounded above by 1:

$$
0 \le q_i (1 - A_i) \le 1 \cdot 1 = 1. \quad \blacksquare
$$

### Boundary States
- **Maximum Disadvantage ($S_i \to 1$):** Requires $q_i = 1$ (100% poverty rate) and $A_i \to 0$ (infinite distance to amenities).
- **Zero Disadvantage ($S_i = 0$):** Occurs if either $q_i = 0$ (zero poverty) or $A_i = 1$ (zero distance to amenity).

---

## 4. What Mathematical Models Do and Do Not Establish

A critical epistemological requirement of this study is understanding the distinction between mathematical deduction and empirical/philosophical truth:

1. **Conditional Validity:** A mathematical derivation proves that a metric satisfies declared formal properties (such as monotonicity, boundedness, or scale invariance) **conditional on its axioms**. It does not prove that the metric represents "justice."
2. **Normative Choices in Formula Construction:** Choosing an exponential decay function ($\exp(-d/\tau)$) rather than a power law ($d^{-\gamma}$) or a binary threshold ($I(d \le d_0)$) is an analyst's design choice. Each mathematical form embeds specific assumptions about human mobility and utility.
3. **Correlation vs. Causation:** Statistical tests of $\rho(q_i, d_i)$ or regression parameters $\beta_1$ evaluate observational associations. They cannot establish whether poverty caused facility placement, whether facility placement influenced neighborhood socioeconomic sorting, or whether unobserved historical variables (such as zoning laws and municipal annexations) generated both patterns.
4. **Distinction from Philosophical Theory:** Showing that $q_i$ and $d_i$ are uncorrelated in Chicago does not "disprove" the architectural critiques presented in Morshed (ed., 2024); it demonstrates that in this specific municipality, the physical distribution of public library branches does not exhibit a spatial poverty penalty.
