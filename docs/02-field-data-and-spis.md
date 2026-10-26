# Field data, statistics and safety performance indicators (SPIs)

What to record during field testing and operation, what to compute from it, and how to turn it into leading and lagging SPIs. The examples use the unintended-braking target from [`tools/unintended_braking_risk_example.xlsx`](../tools/unintended_braking_risk_example.xlsx).

## 1. Data to collect, organised by the risk equation

R = Σ share × HB rate × P(collision | HB) × P(injury)

| Feeds | Data | How |
|---|---|---|
| **Denominators / exposure** | Operating hours and km, time-stamped, with ODD tags: road type, speed, weather, light, traffic density, follower presence and headway | Continuous low-rate signals plus map and weather lookups |
| **Scenario distributions** | Every occurrence of each scenario type with its parameters (gap, closing speed, the follower's reaction and deceleration after ego braking…) | Scenario tagger over the logs. This is the only source for fitting marginals and copula. |
| **HB rate** | Every brake request with its cause: confirmed object / false positive / unexplained. Also **near-HBs**: FP detections that tracking or arbitration suppressed. | Event-triggered raw-sensor ring buffer (±10 s) |
| **Perception error model** | Misses and false positives against labelled ground truth, by object class, range, occlusion and weather, including persistence in frames | Labelled sample, oversampled at triggering conditions |
| **Outcomes** | Contacts and collisions with Δv; police and insurance reports; injuries. Near misses as continuous surrogates: min TTC, PET, DRAC, rear TTC after ego braking | Rear radar/camera, IMU, incident process |
| **System and other responses** | Minimal-risk manoeuvres, remote-assistance requests, disengagements, runtime-monitor flags, ODD exits | System logs |
| **Provenance** | Software/model hash, configuration, map version, calibration state, maintenance | Attached to every hour of data. Needed to check the frozen-software assumption. |

## 2. Statistics to compute

- **Rates with confidence bounds** per ODD stratum and software version: λ_U = ½ χ²_{2(k+1)}(C) / T. With zero events, λ_U ≈ 3/T at 95%.
- **Scenario frequencies and parameter distributions:** ν = count/hours with a Poisson/Gamma interval; marginals plus copula. For the copula: Kendall τ per pair → ρ = sin(πτ/2), a positive-definiteness check and a tail-dependence check.
- **Conditional probabilities:** HB per triggering-condition occurrence (binomial, Clopper–Pearson); collision given HB from near-miss surrogates.
- **Extreme value analysis** on min TTC or similar proximity metrics: extrapolate near-miss frequency to crash frequency (Åsljung et al.; reviewed in Betschinske et al. 2025).
- **Discovery rate of unknown scenarios** (Clause 11): the rate of occurrences that fit no scenario type. Good–Turing estimate of the probability that the next scenario is new ≈ n₁/N (types seen exactly once ÷ all occurrences).
- **Representativeness:** divergence between the tested and target ODD distributions per stratum (χ², Wasserstein).
- **Change detection:** CUSUM or sequential tests on rates; rate ratios between software versions (exact conditional Poisson test).

## 3. SPIs

**UL 4600:** an SPI is *"a metric supported by evidence that uses a threshold comparison to condition a claim in a safety case"*, and *"relying solely on lagging indicators is not acceptable"* (quoted in Ratiu et al. 2024).

**Koopman:** a KPI asks *how well do we drive*; an SPI asks *how often are we potentially unsafe*.

- **Lagging SPIs** measure losses and near-losses that have already happened.
- **Leading SPIs** measure precursors before a loss.
- **Safety-case SPIs** check whether the assumptions still hold.

Every SPI needs four things:

1. the safety-case claim it conditions;
2. the metric and its data source;
3. a threshold derived from the risk budget, not chosen by feel;
4. the response when it is breached: update the safety case, restrict operations (speed, geofence), update the system, or ground the fleet (Ratiu et al. 2024).

### Example SPI register: unintended braking

| Type | SPI | Claim it conditions | Threshold |
|---|---|---|---|
| Lagging | Rear-end collisions with ego struck, per h, by severity | Overall validation target | A_H |
| Lagging | Injury collisions per h | Same | A_H |
| Leading | Unexplained brake requests per 1,000 h, per trigger context | HB rate ≤ target per context | λ target from the *Validation Targets* sheet |
| Leading | Suppressed FP brake detections per 1,000 h | Margin before HB | Trend alarm (e.g. doubling) |
| Leading | Rear TTC < 1.5 s within 3 s after ego braking | P(collision \| HB) as modelled | Simulation prediction per stratum |
| Safety case | Share of time with a follower < 1 s | Exposure assumption (7% in the example) | χ² test vs. assumed shares |
| Safety case | Kendall τ (follower headway, reaction) | Copula assumption | CI must contain the assumed ρ |
| Safety case | Rate of unclassifiable scenarios / triggering conditions not in the taxonomy | Unknown-trigger reserve ε holds | Good–Turing estimate × severity ≤ ε·A_H |
| Safety case | Sensor calibration loss; operation on a software version that wasn't validated | Frozen-software / sensor assumptions | 0 tolerated |

### Why lagging SPIs alone cannot steer

At A_H = 10⁻⁷/h, a fleet that exactly meets the target expects **one injury collision per 10 million hours**. A lagging SPI fires long after the risk has been incurred.

Leading SPIs occur 10³–10⁶ times more often. They detect drift within weeks, and each is tied to one term of the risk equation, so a breach says *which* term moved. SOTIF perception insufficiencies belong in leading SPIs at the perception level, e.g. a pedestrian missed for more than N consecutive frames (Koopman).

## References

- ANSI/UL 4600, Chapter 16 (SPIs).
- Ratiu, Rohlinger, Stolte, Wagner (2024). *Towards an Argument Pattern for the Use of Safety Performance Indicators.* arXiv:2410.00578.
- Koopman, *SPI vs KPI*, CMU lecture notes: https://users.ece.cmu.edu/~koopman/lectures/L124_SPI_vs_KPI.pdf
- Betschinske et al. (2025), arXiv:2506.10363.
- Schaller et al. (2026), *Discover Artificial Intelligence* 6:1172 (runtime monitors as leading evidence).
- ISO 21448:2022, Clause 13 (operation phase).
