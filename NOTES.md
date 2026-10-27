# Notes

- Prefers being challenged over being reassured; wants claims verified with sources, no hedged generalities.
- Physics PhD: the maths can be written compactly. Spend effort on the assumptions behind the maths, not on the algebra.
- Storage: the workspace is synced to the claude.ai project "sinadra" (docs under `course/`). Lessons are published as one multi-file artifact, "SOTIF Risk Course".
- Interview (2026-10-20) selected every outcome and every gap area. Primary outcome: the residual-risk argument. The curriculum order follows the chain of that argument.

- 2026-10-27: Asked how the validation-target split is decided. Wrote docs/08 methodology (QRN, SIFAD, Putze, AMJ 25.1309, MIL-HDBK-338, cost-optimal allocation). Cost term c_j not yet in the workbook.
- 2026-10-27: All docs updated to the verified state and pushed. ISO citations checked against ISO 21448:2022(E); equation audit against post-2022 literature found one real error (allocation rule, now B_j ∝ √(λ_k,j·G_j), total 564,084 h) plus two presentation gaps (Kish ESS ≠ precision; confidence on R_HB does not transfer to A_H unless factors are known). David prefers current (post-2022) methods over the standard's text where they differ.
- 2026-10-26: LaTeX report (33 pp.) with pinpoint citations; docs 05–07 (UB visual report, ACC/robotaxi outlook, L4 scenario DB, ODD-tag granularity, completeness, OpenLABEL vs ISO 34504).
- 2026-10-26: Covered informally (docs/01–03): scenario-based risk estimator, IS weights, Gaussian copula, field data and SPIs. Not yet tested by quiz, so no learning record.
- 2026-10-20: David's HARA structure is 24 HB → 160 HE, with ~16,000 logical scenarios assigned per HE (or in total? unconfirmed), and n concrete scenarios each. His open question is how to derive risk over all of them. Lesson 4 (scenario-weighted risk) is pulled forward and should use this structure as the running example.

## Curriculum map (draft — revise as learning records accumulate)
1. Acceptance criterion → validation target (Poisson, zero-failure, k failures, confidence semantics) ← lesson 0001
2. What a mileage target does not prove: fixed-design testing, test-fix-retest, sequential testing (SPRT), Bayesian priors
3. Decomposition: A_H → R_HB (Annex C.2) and its flaws; Bonferroni aggregation over triggering-condition/behaviour/event triples
4. Scenario-weighted risk: exposure × P(harm | scenario); per-scenario contribution; scenario DB schema for it
5. Dependence: copulas for correlated scenario parameters; Monte Carlo
6. Rare events: importance sampling, cross-entropy, extreme value analysis
7. Runtime risk: SINADRA SEM → CBCT → BN; risk implausibility hypotheses; how runtime models feed or fail to feed the SOTIF argument (Schaller monitor ensemble)
8. Assessor drills: attacking and defending quantitative claims
