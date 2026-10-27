# SOTIF Risk Quantification & Validation Resources

## Knowledge

- Standard: ISO 21448:2022 *Road vehicles — Safety of the intended functionality*, Clause 6 (acceptance criteria), Clause 9 (V&V strategy, validation targets), Annex C.2–C.6 (validation-target derivation, worked examples). https://www.iso.org/standard/77490.html
  The normative source. Use for: the exact wording of acceptance criteria, validation targets and the Annex C formulas. Available through the company standards licence.
- Standard: ISO/TS 5083:2025 *Safety for automated driving systems — Design, verification and validation*. Preview: https://webstore.ansi.org/preview-pages/ISO/preview_ISO+TS+5083-2025.pdf
  The ADS-level complement to 21448 (positive risk balance, L3+). Use for: how L4 acceptance criteria are framed beyond SOTIF.
- [Putze, Westhofen, Koopmann, Böde, Neurohr (DLR), "On Quantification for SOTIF Validation of Automated Driving Systems", arXiv:2304.10170 (2023)](https://arxiv.org/abs/2304.10170)
  Rigorous critique of Annex C.2: notation, missing aggregation, system-dependence of field-data factors; Bonferroni bound over (trigger, behaviour, event) triples. Use for: lessons 1 and 3.
- [Betschinske et al., "Towards more efficient quantitative safety validation of residual risk for assisted and automated driving", arXiv:2506.10363 (2025)](https://arxiv.org/abs/2506.10363)
  Survey of every route for reducing the validation effort (decomposition, SPRT, Bayesian, importance sampling, EVA, SBT), with the Annex C base model written out as a hypothesis test. Use for: lessons 1–3, 6.
- [Kalra & Paddock, *Driving to Safety*, RAND RR-1478-RC (2016)](https://www.rand.org/pubs/research_reports/RR1478.html)
  The canonical "275 million failure-free miles" calculation. Use for: the feasibility argument against pure mileage testing.
- [Wachenfeld & Winner, "The Release of Autonomous Vehicles", in Maurer et al. (eds.), *Autonomous Driving* (Springer, open access, 2016)](https://doi.org/10.1007/978-3-662-48847-8)
  The "approval trap" argument and the distance needed relative to human benchmarks. Use for: background for lessons 1–2.
- [Warg et al., "The Quantitative Risk Norm — A Proposed Tailoring of HARA for ADS", DSN-W 2020](https://www.es.mdu.se/publications/5963-The_Quantitative_Risk_Norm___A_Proposed_Tailoring_of_HARA_for_ADS)
  Acceptance criteria as frequency budgets per incident type. Use for: lesson 3 (allocation).
- [de Gelder et al. (TNO / TU Delft), scenario-based quantitative risk estimation with importance sampling](https://publications.tno.nl/publication/34640947/oPUmb7/gelder-2022-safety.pdf)
  Data-driven scenario parameter distributions and risk estimates. Use for: lessons 4–6.
- Reich, *SINADRA: Situation-Aware Dynamic Risk Assessment for Safe and Permissive Autonomous Systems*, Dr.-Ing. thesis, RPTU Kaiserslautern-Landau / Fraunhofer IESE (2026). Attached by David.
  SEM → CBCT → BN chain; §2.5 survey of risk-based runtime approaches (QRN, µODDs, DRM); §5.2.5 intent-weighted risk aggregation. Use for: lesson 7.
- [Schaller et al., "Addressing SOTIF with a runtime monitor ensemble for AI-based perception systems", *Discover Artificial Intelligence* 6:1172 (2026)](https://doi.org/10.1007/s44163-026-02186-z)
  Maps a monitor ensemble onto SOTIF clauses 6–13; monitors as proxy evidence when 10⁻⁹/h targets are untestable. Use for: lessons 1 (motivation) and 7.

### Added 2026-10-27 (post-2022 methods; verification)
- ISO 21448:2022(E), now used directly (licensed copy). Pinpoint pages in `report/VERIFICATION.md` (printed page = PDF page − 8).
- Ramdas, Grünwald, Vovk, Shafer (2023). *Game-theoretic statistics and safe anytime-valid inference*. Statistical Science 38(4). arXiv:2210.01948. Use for: continuous field monitoring with valid error control at any stopping time.
- Feng et al. (2023). *Dense reinforcement learning for safety validation of autonomous vehicles*. Nature 615:620–627. Use for: accelerated testing of rare events.
- Delecki, Katz, Kochenderfer (2024). State-dependent importance sampling proposals. arXiv:2412.02154. Use for: adaptive IS in sequential scenarios.
- Moss et al. (2023/24). *Bayesian safety validation for failure probability estimation of black-box systems*. arXiv:2305.02449.
- Kusano et al. (2024; 2025). Waymo rider-only crash rates vs aligned human benchmarks. arXiv:2312.12675; arXiv:2505.01515. Use for: lagging SPIs and acceptance criteria.
- Berend & Kontorovich. *On the concentration of the missing mass*. arXiv:1210.3248. Use for: upper bound on the probability of unseen scenario types.
- Glasmacher et al., completeness argumentation for scenario catalogues; de Gelder et al. (2024), scenario coverage metrics; ASAM OpenLABEL 1.0; ISO 34504:2024 scenario tags. Use for: doc 07.

## Wisdom (Communities)

- [Safety-Critical Systems Club (SCSC), Safety of Autonomous Systems Working Group](https://scsc.uk)
  UK practitioner community with active autonomy WGs and seminars. Use for: critiques of safety arguments.
- [The systemsafety mailing list (Bielefeld)](https://lists.techfak.uni-bielefeld.de/mailman/listinfo/systemsafety)
  Long-running, blunt expert list (Ladkin, Koopman, Thomas and others). Use for: stress-testing statistical claims.
- DIN NA 052 mirror committee for ISO TC22/SC32/WG8 (SOTIF / ISO/TS 5083 work)
  Use for: hearing how the next edition of 21448 is likely to treat quantification.
- Conferences: SAFECOMP + WAISE workshop; IEEE IV.

## Gaps
- ~~No free text of the Annex C worked examples~~: resolved, licensed ISO 21448:2022(E) supplied 2026-10-26.
- Copula-based scenario modelling in the AV context: a good tutorial-grade source is still needed (search before lesson 5). Interim: Joe (2014), *Dependence Modeling with Copulas*; doc 03.
