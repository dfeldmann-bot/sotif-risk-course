# Mission: Quantitative risk calculation and validation under SOTIF (ISO 21448)

## Why
David is a SOTIF engineer working on an L4 system at MOTOR AI. He needs to build, and be able to defend, the quantitative part of the residual-risk argument: acceptance criteria → validation targets → evidence. That includes his scenario database, which should yield total risk and each scenario's weight, and possibly runtime risk models (SINADRA-style) as a source of permissiveness and evidence.

## Success looks like
- Derive a validation target from an acceptance criterion and state every assumption it rests on (Poisson, representativeness, aggregation, confidence semantics).
- Decompose a global acceptance criterion across hazardous behaviours, triggering conditions and scenarios, with the aggregation bound written down.
- Compute total residual risk and per-scenario contributions from a scenario DB (exposure × conditional harm), including dependent parameters (copulas) and rare-event estimation (importance sampling).
- Explain how runtime risk models (SINADRA CBCTs / Bayesian networks, monitor ensembles) feed the residual-risk argument, and where they cannot.
- Defend or attack each of the above in front of an assessor (TÜV or peer reviewer) without hand-waving.

## Constraints
- Already expert in ISO 26262 / ISO 21448 at clause level, HARA and the general concepts. Physics PhD, so the maths can be dense; the gaps are in applied statistics and SOTIF-specific quantification.
- Short sessions. Course files are kept in the claude.ai project "sinadra".
- Anchor documents: Reich, *SINADRA* (PhD thesis, RPTU 2026); Schaller et al., *Addressing SOTIF with a runtime monitor ensemble…* (Discover AI 2026).

## Out of scope
- ISO 26262 random hardware metrics (PMHF, SPFM/LFM).
- Cybersecurity (ISO/SAE 21434).
- Perception-model training techniques beyond what is needed for risk evidence.
