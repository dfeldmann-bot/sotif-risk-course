# Scenario-based residual risk under SOTIF

> Rendered version with typeset formulas and plots: [`01-scenario-based-risk.html`](01-scenario-based-risk.html) (clone and open in a browser, or view in the published course).

How to turn the evaluation of many scenarios (critical and non-critical) into a residual-risk number, and how that number relates to validation targets.

Worked example: [`tools/unintended_braking_risk_example.xlsx`](../tools/unintended_braking_risk_example.xlsx) (built by `tools/build_ub_example.py`, synthetic data).

## 1. Direction of the calculation

A HARA is built system-outward: hazardous behaviour (HB) → hazardous event (HE) → scenarios. Probability flows the other way. **The world produces situations at some rate; the system responds with an HB or not.** For computing risk, the scenario is the random variable and the HB is an outcome conditioned on it.

- Store the mapping as **scenario → {possible HB, HE}**, not HE → scenarios. One world situation can lead to several HEs depending on the system's response.
- Logical scenarios must form a **partition of the ODD** (mutually exclusive, exhaustive). Overlapping scenarios double-count exposure; then only the conservative Bonferroni bound (Putze et al. 2023, Eq. 2) holds.
- Large combinatorial counts (e.g. 16,000 logical scenarios per HE) are usually products of ODD factors (manoeuvre × road × weather × light × speed band). Those factors belong in the parameter vector θ, with a distribution, not in separate logical scenarios.

## 2. The estimator

For severity class s:

```
R_s = Σ_ℓ ν_ℓ · p_ℓ,s
p_ℓ,s = ∫ P(HB | θ, ℓ) · P(S ≥ s | HB, θ, ℓ) · f_ℓ(θ) dθ
```

| Symbol | Meaning | Source |
|---|---|---|
| ν_ℓ | exposure: occurrences (or time share) of logical scenario ℓ per operating hour | field data |
| f_ℓ(θ) | joint distribution of concrete parameters (marginals + copula) | field data |
| P(HB \| θ) | system response | simulation (SiL/HiL), anchored by proving ground |
| P(S \| HB, θ) | collision kinematics → injury risk curve | simulation + accident data (e.g. GIDAS) |

Estimated from N concrete runs drawn from a test distribution q_ℓ:

```
p̂_ℓ,s = (1/N) Σ_i w_i · h_i,    w_i = f_ℓ(θ_i) / q_ℓ(θ_i)
```

h_i is the run outcome (0/1 harm, or P(S ≥ s | Δv_i)). Contribution of scenario ℓ: c_ℓ = ν_ℓ · p̂_ℓ,s / R_s.

### Consequences for test campaigns

- **Counting critical runs is not a risk estimate.** In a toy cut-in model, a uniform grid design flags 5.4% of runs as critical while the true probability per cut-in is 4.9 × 10⁻⁵. Only the weights w_i connect the runs to the real world.
- **Non-critical runs are evidence.** They form the bulk of the sum.
- **Falsification / criticality search** finds triggering conditions (Clause 10 → Clause 8 fixes). It does not estimate risk unless the sampling distribution q is known. Keep the two campaigns separate.
- **Importance sampling** shifts q toward the critical region and corrects with w (ISO 21448:2022, C.5, Figs C.12–C.14, pp. 149–151). Report the effective sample size (Σw)²/Σw² *and* the relative standard error sd(w·h)/(√N·p̂) with every estimate: Kish's ESS depends only on the weights, so for rare events it does not measure precision (report Sec. 10). In the example, 1,000 IS runs reproduce the 200,000-run plain Monte Carlo estimate to within a factor of 0.73.

### Relation to Annex C

ISO 21448:2022 writes A_H = R_HB · P_E|HB · P_C|E · P_S|C, where P_C|E is the probability of *not* controlling (C.2.1, Formula (C.1), p. 127). Those factors are the scenario-averages of the integral above. The standard's own AEB example (C.2.2, pp. 127–134) already uses a Monte Carlo simulation over trailing distance and reaction time, and C.5 (pp. 145–152) describes fitting parameter distributions from naturalistic data and importance sampling. The scenario approach keeps the θ-dependence that Annex C averages away. That makes it more efficient, and also data-hungrier.

## 3. Relation to validation targets

The field-only approach has one target, the failure-free exposure τ = −ln(1−C)/R_HB (lesson 1). The scenario approach replaces it with one claim and several evidence targets:

```
Σ_ℓ ν_ℓᵁ · p_ℓ,sᵁ + R_unknownᵁ ≤ A_s   at confidence C
```

U marks upper confidence bounds; split the confidence budget across terms (Bonferroni: Σ(1 − C_i) ≤ 1 − C) or propagate a joint posterior.

| Term | Validation target | Measured in |
|---|---|---|
| ν_ℓᵁ | enough naturalistic data per scenario class (Poisson bound on scenario counts) | hours of ODD data |
| f_ℓ | estimation error of the fitted distribution below a threshold | number of scenario instances |
| p_ℓᵁ | upper bound per scenario; plain MC with 0 failures needs N = 3/p* runs (rule of three), so IS is not optional | runs, effective sample size |
| simulation credibility | real-vs-simulated agreement for the same θ within a stated bound | proving-ground / replay runs |
| R_unknownᵁ | field driving with no unexplained HB (lesson 1 τ, restricted to what the taxonomy misses) | hours / km |

Scenario-based testing **shrinks** field testing but does not remove it: coverage and the unknown-scenario term need real-world data (Betschinske et al. 2025).

### Lessons from the unintended-braking example

- **Zero events ≠ zero risk.** Contexts with 0 observed HB get 0% in the point estimate but dominate the evidence requirement.
- **With 0–4 events per cell, point-estimate attribution is mostly Poisson noise.**
- **Bonferroni over 120 estimated terms fails where a Bayesian posterior passes.** The choice of inference method, and the defensibility of its prior, decides the evidence plan.
- **Optimal evidence allocation:** minimising total test hours Σ λ_k,j·G_j/B_j subject to Σ B_j = budget gives **B_j ∝ √(λ_k,j·G_j)** (G_j = harm weight of cell j; λ_k,j = ½χ²_2(k_j+1)(C_b) differs per cell). An earlier version used B_j ∝ √G_j, which is optimal only if all cells have the same number of events (report Sec. 10).
- **Screening by bound:** a scenario cannot contribute more than ν_ℓ · 1. Reserve a fraction ε of A_H; scenarios whose summed exposure bounds fit inside it need no simulation.

## 4. Parameterising a logical scenario

1. **Scenario type + parameters** (ISO 34502 logical/concrete), e.g. cut-in: initial gap, closing speed, lateral speed, cut-in duration, ego speed; plus outcome-relevant ODD conditions (friction, visibility, occlusion).
2. **Keep θ small** (3–6 dimensions). Use a sensitivity analysis on a coarse design; fix the rest at conservative values or treat them as noise.
3. **Mine instances** from drive logs with a scenario tagger. Each detection gives one θ sample and one count toward ν.
4. **Fit f_ℓ(θ):** marginals + copula ([03-gaussian-copula.md](03-gaussian-copula.md)) or KDE (de Gelder 2022).
5. **Exposure:** ν̂_ℓ = count / hours, with a Poisson or Gamma interval.
6. **Partition check:** no instance may belong to two logical scenarios.

## 5. Where each conditional probability comes from

| Quantity | Primary source | Caveat |
|---|---|---|
| ν_ℓ, f_ℓ(θ) | own fleet logs; public naturalistic datasets only if they match the ODD; accident databases for tails | system-dependent: e.g. cut-in gaps depend on the ego's following policy (Putze et al.) |
| P(HB \| θ) | simulation; perception via a **perception error model** (miss/FP rates vs. range, occlusion, weather) learned from labelled field data | sim-to-real gap must be quantified |
| P(C̄ \| E) | for L4, only other road users' evasion: reactive agent models, or 1 (conservative) | any claimed controllability is an assumption to justify |
| P(S \| HB, θ) | simulated Δv / impact angle → injury risk curve (e.g. P(MAIS3+ \| Δv)) | carry the curve's confidence band |

**Field testing** provides exposure, parameter distributions, perception error models, simulation validation and the unknown-scenario residual. **Simulation** provides the system response over θ.

## References

- ISO 21448:2022(E): 6.5 (pp. 30–31), 9.1 (p. 42), 11 (pp. 50–52), C.2.1 (pp. 126–127), C.2.2 (pp. 127–134), C.3 (pp. 134–137), C.5 (pp. 145–152), C.6 (pp. 153–158). ISO 34502:2022.
- Delecki, Katz, Kochenderfer (2024), state-dependent IS proposals, arXiv:2412.02154; Feng et al. (2023), dense RL for safety validation, *Nature* 615:620–627; Moss et al. (2023/24), Bayesian safety validation, arXiv:2305.02449 (post-2022 alternatives; see report Sec. 10).
- Putze et al. (2023), arXiv:2304.10170.
- Betschinske et al. (2025), arXiv:2506.10363.
- de Gelder (2022), PhD thesis, TU Delft.
- Zhao et al. (2017), accelerated evaluation with importance sampling, arXiv:1605.04965; arXiv:1610.09450.
- Waymo, omni-directional injury risk model: https://waymo.com/research/an-omni-directional-model-of-injury-risk-in-planar/
