# Literature review: acceptance criteria, validation targets and risk estimation (2023–2026)

*Analysed 2026-10-30 from full texts unless marked "abstract only". Section and page numbers refer to the versions read. Feasibility at scale: see `11-feasibility-at-scale.html`.*

## Budget split and validation targets

### Werling, Faller, Betz, Straub (2025). Safety Integrity Framework for Automated Driving (SIFAD). arXiv:2503.20544 (57 pp., preprint; applied to BMW Personal Pilot L3 per Sec. 7)
- RAC per injury level I1+ (AIS ≥ 1), I2+ (AIS ≥ 3), I3 (AIS ≥ 5) with safety factor k_s > 1 against human drivers (Sec. 2, Table 1, Eq. 2). Note: Ex. 2.2 calls I2+ "slight injuries and higher", inconsistent with Table 1.
- Two operating modes (Sec. 3.2): discrete λ_i,s = λ_s·p_b·p_c·p_i (Eq. 3), evidence per demand; continuous λ_i,s = p_s·λ_b·p_c·p_i (Eq. 4), evidence per hour. ISO 21448 Formula (C.2) covers only the continuous case.
- Provisional budget per hazard scenario as fraction of the RAC, shifted as performance becomes known (Sec. 3.3, Remark 3.7, Fig. 7). Three options per hazard: accept, modify the product definition, or formulate a top-level safety requirement (Fig. 6).
- Ex. 3.3: λ_s = 2·10⁻²/h, p_c = 1, p_i = 0.1, budget 10⁻⁹/h → p_b ≤ 5·10⁻⁷ → redundancy required.
- Redundancy (2oo3) reduces data ~100× under independence (Ex. 1.3); scenario is a common cause, so channel performance is conditioned on the scenario (Remark 6.2, Ex. 6.1–6.3).
- Bayesian networks over scenario, sensors, collision and injury; ancestral Monte Carlo (Sec. 6.5.2). Ex. 6.18: P(I2+|HS) = 5.6·10⁻⁵ ± 1.1·10⁻⁵ from 10⁵ samples → 1.1·10⁻⁶/h, 10× over budget → sensitivity analysis → design change (Ex. 6.19). IS or splitting recommended for SiL.
- Uses posterior means (n_f+1)/(n+2) and (n_f+1)/T (Sec. 6.4), not upper bounds; for a validation claim the upper bound is stricter.
- Sec. 8: ISO 26262's implicit RAC is the same for every hazard regardless of their number; with PRB only the sum counts → individual budgets per scenario.

### Putze, Westhofen, Koopmann, Böde, Neurohr (2023). On Quantification for SOTIF Validation of Automated Driving Systems. arXiv:2304.10170
- Critique of ISO 21448 Annex C.2: assumes one triple (triggering condition, hazardous behaviour, hazardous event) per harm and system-independent probabilities (Sec. IV-B).
- Bonferroni upper bound over all triples: P(H, S) ≤ Σ_{E,B,T} P(T)·P(B|T)·P(E|B,T)·P(H|E,B,T)·P(S|H,E,B,T) (Ineq. 2–3); inclusion–exclusion if too loose.
- "It is not sufficient to derive a single validation target"; every summand needs its own upper bound.
- Exposure P(E|B) depends on ODD and driving strategy (ice-plate example), so it must be justified for the system.

### Hofmeister, Kinalzyk (AVL Software and Functions, ca. 2023). Acceptance Criteria, Validation Targets and Performance Targets in an ISO 21448 conform development process (thematic paper; copy supplied by David)
- Global → hazard-based → scenario-class acceptance criteria; sums must hold at each level; one scenario class can belong to several hazards (Sec. 2.2, Fig. 1).
- Statistical and behavioural criteria at each level (Tables 1–3).
- One validation target per scenario class: test space, sub-spaces by test environment, coverage of unknowns by endurance data, test-bench qualification, confidence level (Sec. 3, Fig. 3).
- Too many scenario classes make budgets too small to test (Sec. 2.2). Performance targets as maturity gates below feature level (Sec. 4). No allocation rule.

### Betschinske, Schrimpf, Peters, Klonecki, Karch, Lippert (2025). Towards more efficient quantitative safety validation of residual risk. arXiv:2506.10363
- Generic five-component model of the ISO 21448 argument and AEB base model: τ = −ln(α)/A_H, k = 0 (Sec. III). 67 % → 99 % confidence multiplies distance by ~4.6.
- Ten reduction approaches assessed on quantifiability, threats to validity, missing links, black-box compatibility (Table I). Decomposition of the acceptance criterion and of the hazardous behaviour have no major missing links; sequential testing and Bayesian methods are conditional; high-yield route profiles (FOT with importance sampling) "remain hypothetical"; scenario-based testing has "no direct quantitative link" to mileage.
- Conclusion: no approach fully replaces FOT; "a residual dependence on FOT is likely to remain" (Sec. VII).

## Severity and rare-event estimation

### Gyllenhammar, Åsljung, Khorsand Vakilzadeh, Rodrigues de Campos (2025). Efficient Injury Risk Assessment for ADS Using Subset Simulation. SAFECOMP 2025, LNCS pp. 82–96
- Subset simulation with p₀ = 0.1, modified Metropolis MCMC; limit state g = (1 + τ_Δv) − (min(BTN,1) + Δv) (Eq. 3). All samples reused to estimate MAIS3+ and MAIS5+ simultaneously (McMurry injury model).
- Degraded ACC (30 m range) in cut-ins; 12,443 real cut-ins, 15-parameter GMM.
- P(MAIS3+) = 2.1·10⁻⁵ vs MC 6.6·10⁻⁶; P(MAIS5+) = 2.2·10⁻⁶ vs 5.3·10⁻⁷; ~10⁵ vs 1.93·10⁸ samples. Biased high 3–4×. Frontal only; no acceptance criterion.

### de Gelder, Buermann, Op den Camp (2025). Comparing Normalizing Flows with KDE in Estimating Risk of ADS. arXiv:2507.22429
- 2,916 highD cut-ins, 4 parameters, fuzzy safety model; MC then IS with KDE proposal (Fig. 1).
- Flows fit better (held-out log-likelihood) above 30 % of data; KDE gives ~40× higher collision probability (Sec. III-C); no ground truth. Proposal kept KDE so that q is not thinner than R·p in the tails.

### de Gelder, Op den Camp (2024). Scenario-based assessment of ADS: How (not) to parameterize scenarios? IEEE IAVVC 2024, arXiv:2409.01117
- UN R157 cut-in, cut-out and lead-vehicle-decelerating scenarios (3,620 / 8,190 / 4,820 simulations), four driver models; parameterized vs recorded scenarios compared by recall, precision, F1.
- Parameterization changes outcomes; the best choice depends on scenario type, system and pass criterion; R157's instant lane change produces many false failures.

### Qian, Xu, Xing, Guo (2026). Test case sampling optimization for safety validation of ADS. Nature Communications 17:3114
- Kernel test case sampling (representativeness + coverage) selects 118 cases from SHRP2 (55,920 normal segments + crashes); 77 beyond the 99th percentile, all 6 beyond 99.99th.
- Weighted accident rate Γ₁Γ₂·Σλ_jI_j/Σλ_jD_j (Eq. 3); human-as-SUT check 1.18 [0.44, 3.14]; failures in high-weight cases dominate (Fig. 8).

### Wang (2022). MAIS(05/08) Injury Probability Curves as Functions of Delta V. NHTSA DOT HS 813 219
- Logistic coefficients for MAIS1+ to fatal, all / frontal / rear-end crashes, Δv in mph (Table 1-1, p. 2). Do not extrapolate rear-end above 40 mph (Sec. 4.3, p. 25).

## Perception evidence per triggering condition

### Patel, Jung (2026). Uncertainty Evaluation ... Applicability of Performance Targets Across Triggering Conditions in ML-Based LiDAR Object Detection. arXiv:2610.35092
- Performance target on the false acceptance proportion met by an uncertainty threshold (Learn then Test) holds only for data like its selection data.
- Applicability test per condition: applicable / not applicable / not determined (Table 5), with measures incl. ODD restriction and reallocation at vehicle level.
- Independent unit is the recorded sequence; minimum units n ≥ ln(1/δ)/ε, ≈ 3/ε (Sec. 3.5, Eq. 5). KITTI and nuScenes too small for any target limit when counted in sequences.

## Acceptance criteria and release

### Kröger (2025). How safe should automated vehicles be? Next Research 2:100238 (abstract only)
- Tolerable ~3·10⁻⁹ fatalities/h and ~4·10⁻⁸ fatalities or serious injuries/h; equal protection of occupants and other road users.

### Paterson et al. / Waymo (2025). Determining Absence of Unreasonable Risk. arXiv:2505.09880 (abstract only)
- Twelve release acceptance criteria and governance; no numerical targets.

## Not yet read in full
- Wang, Zhao, Yu, Zhang (2025), arXiv:2501.10097 — perception requirement decomposition with Shapley allocation (summary only; automated review flagged unmet targets).
- Op den Camp, de Gelder (2025), arXiv:2507.22433 — NATM operationalization (abstract only).
- Delecki et al. (2024), Feng et al. (2023), Moss et al. (2023) — rare-event methods (abstracts).
