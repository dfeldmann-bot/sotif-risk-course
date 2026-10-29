# SOTIF Risk Course

A self-paced course on quantitative risk calculation and validation under ISO 21448 (SOTIF), from acceptance criteria through validation targets to scenario-based residual-risk estimation.

## Contents

| Path | What it is |
|---|---|
| `index.html` | Course overview and syllabus (8 lessons planned) |
| `lessons/` | Interactive lessons (open in a browser). Lesson 1: acceptance criterion → validation target |
| `reference/` | Printable reference sheets (validation-target formulas, χ² factor table, assumption checklist) |
| `assets/` | Shared stylesheet, quiz engine, validation-target calculator |
| `tools/build_workbook.py` → `tools/sotif_validation_targets.xlsx` | Every lesson 1 calculation as live Excel formulas |
| `tools/make_equations_html.py` | Renders all validation-target equations (MathJax) with worked numbers; takes your inputs as CLI flags |
| `tools/ub_sim.py` + `tools/build_ub_example.py` → `tools/unintended_braking_risk_example.xlsx` | Worked example: one validation target (MAIS2+ rear-end injury from unintended braking) over 100 logical scenarios and 1,000 importance-sampled concrete scenarios (Gaussian-copula parameters): exposure × HB rate × P(collision\|HB) × P(injury), with point, Bonferroni and Bayesian bounds, per-cell evidence targets, and a live copula sheet |
| `docs/*.html` | **Rendered docs with formulas and plots** (open in a browser): 01–04 background, `05-unintended-braking-report.html` (visual report of the 1,000-scenario workbook), `06-scaling-to-acc-and-robotaxi.html` (outlook). `07-scenario-database-and-completeness.html`: L4 vehicle-level SOTIF strategy, scenario database and data pipeline, automatic scenario identification, ODD-tag granularity, completeness arguments, OpenLABEL vs ISO 34504. Rebuild with `python3 tools/build_docs_html.py` |
| `docs/08-risk-budget-split.md` (+ `.pdf`, `08-budget-tree.png`) | Methodology for splitting the acceptance criterion into validation targets: QRN budget condition, reserves, MECE incident types, allocation rules from the literature, minimum-evidence-cost rule B_j ∝ √(c_j·λ_k,j·G_j), multi-class convex program, worked example |
| `docs/09-risk-budget-map.html` | Visual explainer: severity-class acceptance criteria shared by hazardous events, split into one validation target per hazardous behaviour (HB → HE → AC map, binding class, solved example) |
| `docs/01-scenario-based-risk.md` | From scenario evaluations to residual risk: estimator, importance weights, relation to validation targets, parameterisation, sources of each conditional probability |
| `docs/02-field-data-and-spis.md` | What to collect in field testing, statistics to compute, leading/lagging SPIs with an example SPI register |
| `docs/03-gaussian-copula.md` | Gaussian copula for scenario parameters: sampling, density for IS weights, fitting, limits |
| `docs/04-how-the-concrete-scenarios-were-generated.md` | Exact method behind the 1,000 made-up concrete scenarios: distributions f and q, copula sampling, kinematic model, importance weights, checks |
| `report/sotif_residual_risk_report.pdf` (+ `.tex`, `figures/`, `_latex.zip`) | 33-page LaTeX report: the full residual-risk argument with pinpoint citations (clause, section, page). Figures and numbers from `tools/gen_report_figs.py` |
| `report/VERIFICATION.md` | Audit log: every ISO 21448 citation checked against ISO 21448:2022(E), corrections made, equation audit against post-2022 literature, and references whose location is still unverified |
| `tools/check_equations.py` | 15 numeric checks of the core equations (χ² factor, Poisson/Jeffreys bounds, allocation rule, copula identities, IS estimator, missing-mass bound); reads the workbook totals |
| `MISSION.md`, `RESOURCES.md`, `NOTES.md` | Learning goals, curated sources, teaching notes |

## Running the tools

```bash
cd tools
python3 make_equations_html.py --A_H 1e-8 --C 0.99 --k 1 -o my_targets.html   # stdlib only
python3 build_workbook.py                                                     # needs openpyxl
python3 build_ub_example.py                                                   # needs numpy, openpyxl
python3 build_docs_html.py                                                    # docs/*.html, needs numpy, matplotlib
python3 check_equations.py                                                    # numeric equation checks
python3 gen_report_figs.py && (cd ../report && xelatex sotif_residual_risk_report.tex)
```

The workbooks are written by openpyxl without cached values. Excel recalculates them when opened; for LibreOffice, use *Data → Calculate → Recalculate Hard*.

## Important

**All numbers in the examples are synthetic and illustrative.** Equation corrections (allocation rule B_j ∝ √(λ_k,j·G_j), ESS vs relative SE, confidence transfer) are logged in `report/VERIFICATION.md`. They demonstrate the calculation chain and describe no real system. ISO 21448 references were checked against ISO 21448:2022(E) (first edition, 2022-06; printed page numbers). ISO/TS 5083 and UL 4600 references are taken from the secondary sources named with them.

## Key sources

- ISO 21448:2022(E), 6.5, 9.1, 11, 13.3, Annex C (C.2.1 Formula C.1 p. 127; C.3 Formula C.7 p. 137; C.5 pp. 145–152)
- Putze et al. (2023), *On Quantification for SOTIF Validation of Automated Driving Systems*, arXiv:2304.10170
- Betschinske et al. (2025), *Towards more efficient quantitative safety validation of residual risk…*, arXiv:2506.10363
- Kalra & Paddock (2016), *Driving to Safety*, RAND RR-1478
- Schaller et al. (2026), *Discover Artificial Intelligence* 6:1172
- Post-2022 methods: Ramdas et al. (2023) anytime-valid inference, arXiv:2210.01948; Feng et al. (2023) *Nature* 615:620; Delecki et al. (2024) arXiv:2412.02154; Moss et al. arXiv:2305.02449; Kusano et al. (2025) arXiv:2505.01515
- de Gelder (2022), *Safety assessment of automated vehicles using real-world driving scenarios*, PhD thesis, TU Delft
