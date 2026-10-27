# Verification log — Quantitative Residual-Risk Validation for SOTIF

Checked on 27 October 2026. ISO 21448 was checked against ISO 21448:2022(E), first edition 2022-06, with page numbers as printed (PDF page = printed page + 8 in the copy used). The other sources were checked twice. The first pass extracted locations; the second asked for verbatim quotes with the section heading. The two local PDFs (Schaller et al., Reich) were checked by full-text search with page mapping.

## Corrections made

| # | Was | Now | Evidence |
|---|---|---|---|
| 1 | Joint confidence 1 − (α₁ + α₂): "ISO 21448 p. 165" (taken from Betschinske et al.) | ISO 21448 C.6.3.2, Example 1 and footnote 1, **p. 156** | Printed p. 156; Betschinske et al. cite "[9, p. 165]", which does not match the printed pagination |
| 2 | Positive risk balance attributed to ISO/TS 5083 | Also one of the four rationales of **ISO 21448 6.5** (GAMAB/GAME, PRB, ALARP, MEM) | 6.5, pp. 30–31 |
| 3 | "Vehicle-level SOTIF strategy" used for the test plan (doc 07, report §8.1) | Renamed **vehicle-level V&V strategy (Clause 9)**. ISO 21448 defines the VLSS as a set of vehicle-level *requirements*, verified by the Clause 9 strategy | 3.34, p. 10; D.1, p. 159 |
| 4 | Notation trap: "Putze et al.'s rendering: α = confidence" | ISO 21448 itself uses α = confidence in Formula (C.7) (p. 137) and confidence = 1 − α in C.6.3.2 (p. 156). The standard is internally inconsistent | C.3 p. 137; C.6.3.2 p. 156 |
| 5 | τ given with R_HB "as in Annex C" | Formula (C.7) is written with **A_H**; the standard applies it to R_HB in its C.2.1 example (2 × 10⁻⁴/h, 5,000 h → 63 %) | C.3 p. 137; C.2.1 p. 127 |
| 6 | Definition 3.25 cited as p. 9 | **p. 8** | printed p. 8 |
| 7 | OpenLABEL frames/streams/ontologies cited to 2.3.2/2.3.6/2.3.3 | Definitions are in **Sec. 2.3**; the subsections elaborate | concept paper |
| 8 | Saturation example (300 types) fully observed at 200,000 draws | Long tail (1,000 types, Zipf 1.8): 731 observed, Chao1 902, Good–Turing 1.06 × 10⁻³ vs true 1.14 × 10⁻³ | recomputed |

## ISO 21448:2022 — statements verified (printed pages)

| Statement in report | Location | Result |
|---|---|---|
| SOTIF = absence of unreasonable risk due to hazards from functional insufficiencies | 3.25, p. 8 | ✓ |
| Acceptance criterion definition | 3.1, p. 2 | ✓ |
| Validation target = value to argue acceptance criterion met; more than one may be needed | 3.33 + Note 3, p. 10 | ✓ |
| Four scenario areas; sizes = number of scenarios, not risk; not measurable | 4.2.2, Figs 5–6, Notes 2–3, pp. 12–14 | ✓ |
| Acceptance criteria per hazardous behaviour; rationales GAMAB/GAME, PRB, ALARP, MEM | 6.5, pp. 30–31 | ✓ |
| V&V strategy incl. validation targets; sufficient coverage of scenario space | 9.1 a)–b), p. 42 | ✓ |
| ODD boundaries/outside ODD part of coverage argument | 9.2 + Note, p. 43 | ✓ |
| Known hazardous scenarios not unreasonable if … | 10.7, pp. 49–50 | ✓ |
| Unknown: residual risk meets acceptance criteria with sufficient confidence | 11.1, p. 50 | ✓ (verbatim) |
| Table 11 methods incl. fleet test, random scenario simulation, sensitivity analysis, scenario exploration (O, footnote e) | 11.3, Table 11, p. 51 | ✓ |
| New unknowns arise with algorithm/ODD/OEDR/policy changes | 11.3 Note 1, p. 52 | ✓ |
| Evaluation asks for coverage of known and argument for unknown | 12.3 c), p. 54 | ✓ |
| Field monitoring process defined before release | 13.1, p. 55 | ✓ |
| On-board monitoring (min distance, near-triggering, take-over, MRC), DSSAD/EDR; context evolution | 13.3, pp. 56–57 | ✓ |
| Annex C structure (C.2, C.3, C.5, C.6) | C.1, pp. 125–126 | ✓ |
| Simulation accuracy is part of the safety argument; physical + simulation testing | C.1, p. 125 | ✓ |
| Acceptance criteria usually very small, e.g. 10⁻⁸/h; A_H derived with safety margin; each HB linked to its own criterion | C.2.1, p. 126 | ✓ |
| Formula (C.1), (C.2); P_C|E = not controllable; P_S|C after unsuccessful control | C.2.1, pp. 126–127 | ✓ |
| Note 4 (consistency with ISO 26262 HARA), Note 5 (independence simplification) | C.2.1, p. 127 | ✓ |
| Example: A_H = 10⁻⁸/h → R_HB = 2 × 10⁻⁴/h; 5,000 h → 63 % | C.2.1, Formula (C.3), p. 127 | ✓ (arithmetic re-checked: −ln(0.37)/2e-4 ≈ 4,970 h) |
| AEB unintended braking > 340 ms, rear-end; Monte Carlo over trailing distance and reaction time | C.2.2.3, Figs C.1–C.2, pp. 129–130 | ✓ |
| Collision probability higher at lower speeds (short trailing distance) | C.2.2.3, Fig. C.3, pp. 130–131 | ✓ |
| Traffic-statistics approach can prove impractical for fully automated vehicles | C.2.2.6, p. 134 | ✓ |
| Iterative constrained-random V&V converts area 3 into area 2 until sufficient coverage | C.3, Fig. C.4, p. 135 | ✓ |
| Stopping rule and criterion for restarting distance counter specified prior to testing | C.3, p. 136 | ✓ |
| τ = −ln(1 − α)/A_H, α = confidence, Poisson; α ≈ 0.63 → τ = 1/A_H; τ can be impractical | C.3, Formula (C.7), Notes 1–2, p. 137 | ✓ |
| Parameter distributions from naturalistic data, KDE (ref [34] de Gelder & Paardekooper 2017) | C.5, Figs C.9–C.11, pp. 146–148 | ✓ |
| Importance sampling biased to riskier areas; risk estimated from simulation results | C.5, Figs C.12–C.14, pp. 149–151 | ✓ |
| ACC lead-braking example parameterised by v_end, t_brake, Δv | C.5, Figs C.9–C.10, pp. 146–147 | ✓ |
| Partition of usage variable, focus on severe modality | C.6.1, p. 153 | ✓ |
| Sufficient conditions at component level | C.6.2, p. 153; C.6.3.2, pp. 154–156 | ✓ |
| "Sensor and algorithms are fixed during testing and real-world use" | C.6.3.2, p. 154 | ✓ |
| Joint confidence 1 − (α₁ + α₂) | C.6.3.2, Example 1 + footnote 1, p. 156 | ✓ (corrected from p. 165) |
| Redundancy and independence | C.6.3.3, pp. 156–158 | ✓ |
| VLSS = vehicle-level requirements; verified per Clause 9 | 3.34, p. 10; D.1, p. 159 | ✓ |
| Formula (C.7) source: Littlewood & Wright 1997 | Bibliography [31] | ✓ |

## Other sources — pinpoints verified verbatim

| Source | Locations confirmed |
|---|---|
| Putze et al. 2023 (arXiv:2304.10170) | IV-B(a) Eq. (1) and τ/Poisson sentence; IV-B(b) conditioning P_S|C,E,HB, "omits this aggregation", Eqs. (2)–(3), "not sufficient to derive a single validation target"; IV-B(c) truck example; IV-A(b) mileage infeasible [22] |
| Betschinske et al. 2025 (arXiv:2506.10363) | I (ISO/TS 5083 p. 146 quote); III-B item 2 (RARs); III-C item 5 Eqs. (3)–(5), p. 137 reference; III-C item 6 (NHST extension); V Eqs. (6)–(9), (14)–(15), Bayesian priors; VII residual FOT dependence |
| Kalra & Paddock 2016 (RAND RR-1478) | p. 2 (1.09/100M miles); p. 3 Eq. 2, 275M miles, 12.5 years; p. 8 11 billion miles, 518 years; p. 10 Table 1 |
| Schaller et al. 2026 | §1.1 pp. 2–3; §1.2 p. 3; §2.1 pp. 8–10; §2.2 p. 10; §4 p. 11; §5.1 pp. 14–15 (10⁻⁹/h; novel I/O behaviour); §6.2 pp. 16–17; §6.3 p. 17; §7 p. 18; §8.2 p. 19 |
| Reich 2026 (printed pages) | §1.3 pp. 3–5 (SEM p. 4, runtime models p. 5); §1.4 p. 6; §2.5.7 p. 31; §4.1 p. 49; §4.3 p. 77; §5.2.5 p. 131 |
| Glasmacher et al. 2024 | III-A (definitions, binary vs quantifiable); III-C (counter-hypothesis); III-D Table I (incl. sensitivity analysis); IV-C (59,253 base scenarios, Fig. 5, "unforeseen scenarios…"); V (dev-ops) |
| de Gelder et al. 2024 (arXiv:2409.01139) | II (Hauer et al.); III Type I/II; III-A Eq. (1); III-B–D Eqs. (2)–(4); IV-B CoverageTag(10) = 1; IV-C ~75 %; V Table III; V–VI completeness future work |
| Guo et al. 2023 | III-A, III-B.1–3, III-C; IV (116 examined of 215,090; CARLA all three categories) |
| Ratiu et al. 2024 | §2 (SPI definition, 16.2.2.6.2 lagging-only, leading/lagging, claim violated without SPI); §3.1 (under-specified estimate); §3.3 (speed, geofences, grounding) |
| Koopman 2022 slides | 6 (lagging), 7 (leading), 10 (k frames, clearance), 12 (KPI vs SPI, UL 4600 Ch. 16) |
| ASAM OpenLABEL concept paper | 1.3 (PAS 1883, OpenODD); 2.3 (frames, streams, ontologies); 2.3.1; 2.3.4 (RDF); 2.3.7 & 3.1 (coordinate systems); 5.1–5.2 |
| Zhao et al. 2016/17 | Abstract (cross-entropy, 2,000–20,000 acceleration) |
| Owen 2013 | Ch. 9 importance sampling, Ch. 10 advanced variance reduction |
| TNO 2024 (ISO 34504) | quotes on tags, examples rather than instructions |

## Still not verified at location level (marked in the report)

ISO/TS 5083, UL 4600 (via Betschinske et al. and Ratiu et al.); ISO 34502, 34503, 15622; Garwood 1936; Clopper & Pearson 1934; Good 1953; Chao 1984; Lindskog et al. 2003; Embrechts et al. 2003; Au & Beck 2001; Rubinstein & Kroese 2016; Hauer et al. 2019 (only via de Gelder et al. 2024); book chapters other than Owen Ch. 9–10, Nelsen Sec. 2.3/Ch. 5 and Coles Ch. 4 (from the books' standard tables of contents).

## Equation audit (27 October 2026)

Every equation was checked numerically with `tools/check_equations.py`; the results are in report Sec. 10, Table 9.

| Equation | Result |
|---|---|
| Evidence allocation | **Was wrong, fixed.** B_j ∝ √G_j is optimal only for equal k_j. The correct rule is B_j ∝ √(λ_k,j·G_j). In the example it needs 564,084 h, against 567,814 h under the old rule. Fixed in the workbook (Validation Targets, new column M), doc 01 and the report (Eq. 9). |
| Annex C decomposition | Correct under conditional-independence assumptions; a toy case with mismatched factors was 22 % off. |
| Zero-failure τ | Correct (coverage simulated: 0.049 vs 0.05). The confidence refers to R_HB, not A_H, when the factors are estimated; the confidence split is now stated. |
| χ² identity, union bound, copula density, ρ = sin(πτ/2), t-copula λ_U, Clopper–Pearson, Jeffreys, flat-prior identity | Correct. |
| ESS | Correct formula, but misleading for rare events. The report now asks for the relative SE of p̂. |
| Granularity bound | Correct only with TV = ½·L¹; the definition was added. |
| Missing mass | A point estimate that had been used like a bound; the Berend–Kontorovich Theorem 1 upper bound was added. |

Post-2022 alternatives cited, each verified at abstract or theorem level: Feng et al. 2023 (*Nature* 615:620–627); Kusano et al. 2024 and 2025 (Waymo aligned benchmarks); Ramdas et al. 2023 (safe anytime-valid inference); Moss et al. 2023/24 (Bayesian safety validation); Delecki et al. 2024 (state-dependent IS); Berend & Kontorovich (missing mass, Theorem 1).
