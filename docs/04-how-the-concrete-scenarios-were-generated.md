# How the 1,000 concrete scenarios were generated

> Rendered version with typeset formulas and plots: [`04-how-the-concrete-scenarios-were-generated.html`](04-how-the-concrete-scenarios-were-generated.html) (clone and open in a browser, or view in the published course).

This documents exactly what [`tools/ub_sim.py`](../tools/ub_sim.py) does to produce the sheet *Concrete Scenarios* in [`tools/unintended_braking_risk_example.xlsx`](../tools/unintended_braking_risk_example.xlsx).

**Everything is made up.** No field data, no real system, no real simulator. The distributions and correlations are illustrative choices. The method is meant to be reused; the numbers are not.

## Overview

```
for each of the 100 logical scenarios ℓ (trigger × speed band × headway class):
    1. draw 2,000 concrete parameter sets from the real-world model f_ℓ   → plain Monte Carlo  (P(coll|HB) column)
    2. draw    10 concrete parameter sets from a proposal q_ℓ            → importance sampling (Concrete Scenarios sheet)
    3. simulate every parameter set with a 1-D kinematic model          → collision yes/no, Δv
    4. for the 10 IS runs: weight w = f_ℓ(θ) / q_ℓ(θ)                   → exact density ratio, incl. copula
```

100 logical scenarios × 10 = **1,000 concrete scenarios**. The 2,000-run plain Monte Carlo (200,000 runs in total) is used as the reference the 1,000 IS runs are compared against.

Reproducible: `numpy.random.default_rng(2026)`. The order of draws is: Poisson event counts for the 20 evidence cells first, then per logical scenario the 2,000 f-runs followed by the 10 q-runs.

## Step 0: logical scenario = which ranges apply

Each logical scenario fixes three things:

| Factor | Values | Effect on the concrete scenario |
|---|---|---|
| Trigger context (5) | clear road, overhead structure, low sun, spray, roadside clutter | none: the trigger only changes the HB rate λ, not the kinematics after an HB |
| Ego speed band (4) | 20–35, 35–55, 55–75, 75–95 km/h | range of the ego speed v_e |
| Follower headway class (5) | 3–6 s ("no follower within 3 s"), 2–3, 1.5–2, 1–1.5, 0.5–1 s | range of the follower time headway h |

So P(collision | HB) depends only on speed band × headway class (20 distinct kinematic settings). The five trigger contexts reuse them with independent random draws.

## Step 1: the parameter vector θ

Seven parameters per concrete scenario:

| Parameter | Symbol | Real-world model f (marginal) | Proposal q (marginal) | Coupled by copula? |
|---|---|---|---|---|
| Ego speed | v_e | Uniform over the speed band | same as f | yes |
| Follower time headway | h | Uniform over the headway class | linear density 2(1−s) on the class (s = position 0…1), i.e. skewed to **short** headways | yes |
| Follower reaction time (from ego brake onset) | T_r | Lognormal, median 1.1 s, log-sd 0.30 | Lognormal, median **1.5 s**, log-sd 0.35 (later reactions) | yes |
| Follower deceleration | a_f | Uniform 3.5–8.0 m/s² | same as f | yes |
| Phantom-brake duration | t_b | Lognormal, median 0.8 s, log-sd 0.50 | Lognormal, median **1.3 s**, log-sd 0.50 (longer brakes) | no (independent) |
| Phantom-brake deceleration | a_e | Uniform 2.5–6.0 m/s² | same as f | no |
| Follower speed offset | v_f − v_e | Normal, mean 0, sd 0.5 m/s | same as f | no |

Derived: initial gap = h · v_f (bumper to bumper).

Why q differs from f: collisions after a phantom brake are rare when the follower is far behind or reacts quickly. The proposal pushes samples toward the critical corner (short headway, late reaction, long phantom brake) so that 10 runs per scenario still produce collisions. The weights then undo the bias.

## Step 2: Gaussian copula sampling

The four coupled parameters (v_e, h, T_r, a_f) are drawn through a Gaussian copula with the illustrative correlation matrix

```
        v_e    h     T_r    a_f
v_e   1.00  0.25  0.00   0.00
h     0.25  1.00 −0.30   0.00
T_r   0.00 −0.30  1.00  −0.40
a_f   0.00  0.00 −0.40   1.00
```

Story behind the signs (assumed, not measured): faster traffic keeps slightly larger time gaps; close followers are more alert; late reactors also brake less hard.

Per draw:

1. ε ~ N(0, I₄); Z = L·ε, with L the Cholesky factor of R (R = L·Lᵀ).
2. U_i = Φ(Z_i), uniform on [0,1] and correlated.
3. Inverse marginal CDF, using f's marginals for the plain runs and q's for the IS runs:
   - v_e = v_lo + U₁ (v_hi − v_lo)
   - h = h_lo + s (h_hi − h_lo), with s = U₂ under f, and s = 1 − √(1 − U₂) under q (inverse CDF of the density 2(1−s))
   - T_r = exp(μ + σ Φ⁻¹(U₃)), with (μ, σ) = (ln 1.1, 0.30) under f and (ln 1.5, 0.35) under q
   - a_f = 3.5 + U₄ · 4.5
4. t_b, a_e and the follower speed offset are drawn independently from their marginals.

Under q the **same copula R** is applied on q's marginals. q is therefore a different joint distribution from f, which is why the weight must include the copula density, not only the marginal ratios.

## Step 3: kinematic simulation

One-dimensional, explicit Euler, dt = 0.01 s, horizon 12 s. Time starts at the phantom-brake onset.

```
ego:      decelerates at a_e while t < t_b and v_e > 0; afterwards holds its speed (no re-acceleration)
follower: constant speed until t ≥ T_r; then decelerates at a_f until its speed equals the ego's
          (it does not brake below the ego's speed)
gap:      gap ← gap − (v_f − v_e)·dt
contact:  first time gap ≤ 0 → collision = 1, Δv = (v_f − v_e) at that instant, in km/h
```

Injury: P(MAIS2+ | Δv) = 1 / (1 + exp(−(Δv − 45)/7)), with Δv in km/h. This curve is illustrative. Real curves are fitted to accident data (e.g. GIDAS). In the workbook the curve parameters are inputs (sheet *Inputs*, rows 12–13), and column Q of *Concrete Scenarios* recomputes it live.

Known simplifications: no lateral escape, no follower jerk or brake build-up, no reaction to the ego's brake release, a single follower, no road gradient or friction variation.

## Step 4: importance weights

For each IS run:

```
w = f_ℓ(θ) / q_ℓ(θ)

log f(θ) = log c_R(z_f) + Σ log f_i(θ_i)
log q(θ) = log c_R(z_q) + Σ log q_i(θ_i)

log c_R(z) = −½ log det R − ½ zᵀ (R⁻¹ − I) z,     z_i = Φ⁻¹(F_i(θ_i))  with F_i = f's or q's marginal CDF
```

Terms that are identical under f and q (v_e, a_f, a_e, follower offset) cancel in the ratio. They are included in the code for completeness.

The logical-scenario estimate from its 10 concrete runs is

```
Ê[collision · P(MAIS2+)] = (1/10) Σ_i w_i · 1{collision_i} · P(MAIS2+ | Δv_i)
```

and the effective sample size is (Σw)² / Σw². Both are live formulas in sheet *Scenarios*, columns Y–AC.

## Step 5: checks performed

| Check | Result | Meaning |
|---|---|---|
| E_q[w] on 200,000 proposal draws (35–55 km/h, 1–1.5 s) | 0.996 | should be 1, so the weights are correctly normalised |
| IS estimate vs. 100,000 plain f-runs, same setting | 0.0161 vs. 0.0157 | unbiased |
| Mean weight over the 1,000 concrete scenarios | 0.98 | consistent with 1 |
| Total risk from 1,000 IS runs vs. 200,000 plain runs | 1.5 × 10⁻⁸ vs. 2.1 × 10⁻⁸ /h (ratio 0.73) | same order from 200× fewer runs |
| Median effective sample size per logical scenario | 4.3 of 10 | the proposal is useful but uneven; weights range from 0.0005 to 67 |
| Collisions among the 1,000 runs | 117 | plain sampling from f at 10 runs per scenario would mostly see 0 |

## What else was made up

- **HB event counts:** drawn as Poisson(true λ × replay hours) from assumed "true" rates per trigger context. These rates are shown in grey in the workbook as synthetic ground truth.
- **Exposure shares** for trigger context, speed band and headway class, combined as a product. This assumes independence between the three factors.
- **Replay hours** per evidence cell.

## How to use the method with real data

1. Replace the marginals of f with distributions fitted to your scenario instances, and R with normal-score or Kendall-τ estimates (see [03-gaussian-copula.md](03-gaussian-copula.md)).
2. Replace `simulate()` with calls to your simulator. Log θ, the outcome and q(θ) for every run.
3. Choose q from a pilot run, by shifting the marginals toward observed failure regions (or with cross-entropy optimisation). Monitor the ESS: if a few weights dominate, q is too far from f.
4. Keep the pure-f Monte Carlo baseline on a few scenarios as a regression check for the weights.
