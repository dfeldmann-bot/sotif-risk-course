# Gaussian copula for scenario parameters

> Rendered version with typeset formulas and plots: [`03-gaussian-copula.html`](03-gaussian-copula.html) (clone and open in a browser, or view in the published course).

Live version, with editable correlation matrix, Cholesky factor in formulas and a sampling demo: sheet *Gaussian Copula* in [`tools/unintended_braking_risk_example.xlsx`](../tools/unintended_braking_risk_example.xlsx). Code: `sample_theta()` and `log_density()` in [`tools/ub_sim.py`](../tools/ub_sim.py).

## What it is

A copula is a joint distribution on [0,1]^d with uniform marginals. **Sklar's theorem:** any joint CDF can be written

```
F(x₁,…,x_d) = C(F₁(x₁),…,F_d(x_d))
```

The Gaussian copula is C_R(u) = Φ_R(Φ⁻¹(u₁),…,Φ⁻¹(u_d)), with Φ_R the multivariate normal CDF with correlation matrix R.

## Why it is used for scenarios

Each parameter has its own natural marginal: uniform speed within a band, lognormal reaction time, uniform deceleration. The parameters are not independent, though. The copula separates two questions:

- which values each parameter takes (the marginals);
- how the parameters move together (R).

## Sampling

1. ε ~ N(0, I); Z = L·ε, where R = L·Lᵀ (Cholesky).
2. U_i = Φ(Z_i): uniform on [0,1], but correlated.
3. X_i = F_i⁻¹(U_i): apply each marginal's inverse CDF.

## Density (needed for importance-sampling weights)

```
c_R(u) = |R|^(−½) · exp(−½ zᵀ (R⁻¹ − I) z),   z = Φ⁻¹(u)
f(x)   = c_R(F₁(x₁),…,F_d(x_d)) · Π f_i(x_i)
```

The concrete-scenario weights w = f(θ)/q(θ) evaluate this for both the real-world model f and the proposal q. In the example, E_q[w] = 0.996 (should be 1), and the IS estimate matches 100,000 plain runs.

## Fitting R from field data

- Transform each parameter to pseudo-observations u = rank/(n+1), then z = Φ⁻¹(u). R is the correlation matrix of z (normal scores).
- Pairwise alternative: estimate Kendall's τ and convert with **ρ = sin(πτ/2)**.
- Rank-based fits do not depend on the marginals.

## Validity

R must be symmetric positive definite: det(R) > 0 and the Cholesky factor exists. Correlations estimated pairwise can violate this. If so, project to the nearest correlation matrix.

## Main limitation

**Zero tail dependence.** Joint extremes, such as a very late reaction combined with very weak braking, become asymptotically independent. If real data show such joint extremes more often, the Gaussian copula under-estimates exactly the critical corner.

- Check with tail-dependence plots or empirical tail-dependence coefficients.
- Alternatives: the **t-copula** (symmetric tail dependence) and **vine copulas** (flexible pairwise structure in high dimension).
- All copula formulas on this page were checked numerically (`tools/check_equations.py`; report Sec. 10).

## Effect in the example

The four coupled parameters are ego speed, follower time headway, follower reaction time and follower deceleration. The correlations are illustrative: ρ(v,h) = +0.25, ρ(h,T_r) = −0.30, ρ(T_r,a_f) = −0.40.

Treating them as independent **under-estimates P(collision | HB) by a factor of 1.2–3**, depending on speed band and headway class. The dependence assumption therefore drives the risk number directly, so it needs its own field evidence and its own SPI (see [02-field-data-and-spis.md](02-field-data-and-spis.md)).
