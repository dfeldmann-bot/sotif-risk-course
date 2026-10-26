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
| `docs/01-scenario-based-risk.md` | From scenario evaluations to residual risk: estimator, importance weights, relation to validation targets, parameterisation, sources of each conditional probability |
| `docs/02-field-data-and-spis.md` | What to collect in field testing, statistics to compute, leading/lagging SPIs with an example SPI register |
| `docs/03-gaussian-copula.md` | Gaussian copula for scenario parameters: sampling, density for IS weights, fitting, limits |
| `docs/04-how-the-concrete-scenarios-were-generated.md` | Exact method behind the 1,000 made-up concrete scenarios: distributions f and q, copula sampling, kinematic model, importance weights, checks |
| `MISSION.md`, `RESOURCES.md`, `NOTES.md` | Learning goals, curated sources, teaching notes |

## Running the tools

```bash
cd tools
python3 make_equations_html.py --A_H 1e-8 --C 0.99 --k 1 -o my_targets.html   # stdlib only
python3 build_workbook.py                                                     # needs openpyxl
python3 build_ub_example.py                                                   # needs numpy, openpyxl
```

The workbooks are written by openpyxl without cached values. Excel recalculates them when opened; for LibreOffice, use *Data → Calculate → Recalculate Hard*.

## Important

**All numbers in the examples are synthetic and illustrative.** They demonstrate the calculation chain and describe no real system. The ISO 21448 Annex C formulas are quoted as rendered by Putze et al. (2023) and Betschinske et al. (2025); check them against a licensed copy of the standard.

## Key sources

- ISO 21448:2022, Clauses 6, 9, Annex C
- Putze et al. (2023), *On Quantification for SOTIF Validation of Automated Driving Systems*, arXiv:2304.10170
- Betschinske et al. (2025), *Towards more efficient quantitative safety validation of residual risk…*, arXiv:2506.10363
- Kalra & Paddock (2016), *Driving to Safety*, RAND RR-1478
- Schaller et al. (2026), *Discover Artificial Intelligence* 6:1172
- de Gelder (2022), *Safety assessment of automated vehicles using real-world driving scenarios*, PhD thesis, TU Delft
