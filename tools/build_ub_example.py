"""
build_ub_example.py — writes unintended_braking_risk_example.xlsx
Worked example: one validation target (MAIS2+ rear-end injury caused by unintended braking)
evaluated over 100 logical scenarios. Evidence is synthetic (see ub_sim.py).
All risk numbers in the workbook are live Excel formulas; only the evidence (hours, event
counts, simulation counts, mean injury probability) and the Bayesian posterior quantile are values.
"""
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.comments import Comment
from openpyxl.formatting.rule import CellIsRule
import ub_sim

OUT = "/home/claude/sotif-risk/tools/unintended_braking_risk_example.xlsx"
F = "Arial"
BLUE, BLACK, GREEN, GREY = Font(name=F, color="0000FF"), Font(name=F), Font(name=F, color="008000"), Font(name=F, color="808080", italic=True)
BOLD, TITLE = Font(name=F, bold=True), Font(name=F, bold=True, size=14)
HEAD = Font(name=F, bold=True, color="FFFFFF")
YEL, HEADFILL = PatternFill("solid", fgColor="FFFF00"), PatternFill("solid", fgColor="0E6B63")
RED_FILL, GREEN_FILL = PatternFill("solid", fgColor="F4CCCC"), PatternFill("solid", fgColor="D9EAD3")
BOX = Border(bottom=Side(style="thin", color="BFBFBF"))
SCI, PCT, INT = "0.00E+00", "0.0%", "#,##0"

cells, scen, concrete = ub_sim.generate()
cop_eff = ub_sim.copula_effect()
NC = len(concrete); CL = 5 + NC  # last row of Concrete sheet
bayes_q95, bayes_mean = ub_sim.bayes_quantile(cells, scen)

wb = Workbook()


def put(ws, ref, val, font=BLACK, fmt=None, fill=None, note=None, wrap=False):
    c = ws[ref]; c.value = val; c.font = font; c.border = BOX
    if fmt: c.number_format = fmt
    if fill: c.fill = fill
    if note: c.comment = Comment(note, "Example")
    if wrap: c.alignment = Alignment(wrap_text=True, vertical="top")
    return c


def header(ws, row, labels, widths=None):
    for i, l in enumerate(labels):
        c = ws.cell(row=row, column=1 + i, value=l)
        c.font = HEAD; c.fill = HEADFILL; c.alignment = Alignment(wrap_text=True, vertical="center")
    ws.row_dimensions[row].height = 45
    if widths:
        for i, w in enumerate(widths):
            ws.column_dimensions[chr(65 + i) if i < 26 else "A" + chr(65 + i - 26)].width = w


def title(ws, t, sub):
    ws["A1"] = t; ws["A1"].font = TITLE
    ws["A2"] = sub; ws["A2"].font = Font(name=F, italic=True, color="595959")


# =============== Overview ===============
ov = wb.active; ov.title = "Overview"
title(ov, "Unintended braking — scenario-based residual-risk example",
      "SYNTHETIC, ILLUSTRATIVE NUMBERS. Shows the calculation chain, not any real system.")
lines = [
    ("Validation target", "Rate of MAIS2+ injuries from rear-end collisions caused by unintended (phantom) braking of the ego vehicle ≤ A_H per operating hour, at confidence C."),
    ("Hazardous behaviour (HB)", "Ego brakes without a valid reason (perception false positive → planner brake request)."),
    ("Hazardous event (HE)", "HB while a following vehicle is close enough that it cannot avoid a rear-end collision."),
    ("ODD partition", "100 logical scenarios = 5 trigger contexts × 4 speed bands × 5 follower-headway classes. They are mutually exclusive and their time shares sum to 1 (checked on Summary)."),
    ("Risk equation", "R = Σ_l share_l · λ_HB(trigger, speed) · P(collision | HB, l) · E[P(MAIS2+ | Δv) | collision, l]"),
    ("Where each term comes from", "share_l: fleet operations logs (context tagging) · λ_HB: open-loop replay of targeted logs through perception+planner, counting unintended brake requests · P(collision|HB): kinematic Monte Carlo of the follower's response · P(MAIS2+|Δv): injury risk curve (illustrative; real curves are fit to accident data)."),
    ("Key modelling assumption", "λ_HB depends on trigger context and speed, not on whether a follower is present (forward perception does not see the follower). So 20 evidence cells serve 100 scenarios."),
    ("Three ways to judge the target", "(1) Point estimate — not acceptable as evidence. (2) Bonferroni: simultaneous upper bounds on every estimated term, multiplied — rigorous but very conservative. (3) Bayesian posterior 95% quantile of R (Jeffreys priors) — computed in ub_sim.py."),
    ("Concrete scenarios", "1,000 made-up concrete scenarios (10 per logical scenario). Parameters drawn from an importance-sampling proposal q (later reactions, longer phantom brakes, shorter headways) through a Gaussian copula; each carries the exact weight w = f(θ)/q(θ) so the 10 runs estimate the real-world probability."),
    ("Parameter dependence", "Ego speed, follower time headway, follower reaction time and follower deceleration are coupled by a Gaussian copula (see sheet 'Gaussian Copula'): each keeps its own marginal distribution, the correlation matrix R sets how they move together."),
    ("Sheets", "Inputs → HB Evidence (20 cells) → Scenarios (100 logical) → Concrete Scenarios (1,000) → Gaussian Copula → Summary → Validation Targets."),
    ("Colour code", "Blue on yellow = input/assumption · blue = evidence value (from data or simulation) · black = formula · green = link to another sheet · grey italic = synthetic ground truth, for comparison only (unknown in reality)."),
]
for i, (k, v) in enumerate(lines):
    put(ov, f"A{4+i}", k, BOLD); put(ov, f"B{4+i}", v, wrap=True)
ov.column_dimensions["A"].width = 30; ov.column_dimensions["B"].width = 120
put(ov, "A16", "Verdict (from Summary)", BOLD)
put(ov, "A17", "Point estimate"); put(ov, "B17", "=Summary!D14", GREEN)
put(ov, "A18", "Bonferroni upper bound"); put(ov, "B18", "=Summary!D15", GREEN)
put(ov, "A19", "Bayesian 95% quantile"); put(ov, "B19", "=Summary!D16", GREEN)

# =============== Inputs ===============
inp = wb.create_sheet("Inputs")
title(inp, "Inputs and assumptions", "Edit blue-on-yellow cells. Everything else recalculates.")
header(inp, 4, ["Parameter", "Value", "Note"], [46, 14, 100])
params = [
    ("Acceptance criterion A_H [MAIS2+ injuries / h]", 1e-7, SCI, "Illustrative. In practice from Clause 6 (e.g. GAMAB vs. human rear-end injury rate in the same ODD)."),
    ("Confidence C", 0.95, "0.00", "Applies to the overall claim."),
    ("Reserve for unknown triggers ε (share of A_H)", 0.10, PCT, "Budget held back for HB from triggering conditions not in the taxonomy (Clause 11); bounded by field driving."),
    ("Number of evidence cells (λ bounds)", "=COUNTA('HB Evidence'!A6:A25)", "0", "Formula"),
    ("Number of scenarios (collision-probability bounds)", "=COUNTA(Scenarios!A6:A105)", "0", "Formula"),
    ("Per-bound confidence C_b (Bonferroni)", "=1-(1-B6)/(B8+B9)", "0.000000", "Simultaneous bounds: Σ(1−C_b) = 1−C over all estimated terms."),
    ("Known-scenario budget (1−ε)·A_H", "=(1-B7)*B5", SCI, "Formula"),
    ("Injury curve: Δv at 50% MAIS2+ [km/h]", ub_sim.INJ_MID, "0.0", "Illustrative logistic P(MAIS2+|Δv) = 1/(1+exp(−(Δv−Δv50)/s)). Drives the Concrete Scenarios sheet live; the 2,000-run column in Scenarios was computed with the build-time value."),
    ("Injury curve: scale s [km/h]", ub_sim.INJ_SCALE, "0.0", "Illustrative."),
]
for i, (p, v, fmt, n) in enumerate(params):
    r = 5 + i
    is_in = not (isinstance(v, str) and v.startswith("="))
    put(inp, f"A{r}", p); put(inp, f"B{r}", v, BLUE if is_in else BLACK, fmt, YEL if is_in else None); put(inp, f"C{r}", n)

r0 = 14
put(inp, f"A{r0}", "Trigger context", BOLD); put(inp, f"B{r0}", "Time share", BOLD); put(inp, f"C{r0}", "Source", BOLD)
for i, (n, s, _) in enumerate(ub_sim.TRIGGERS):
    put(inp, f"A{r0+1+i}", n); put(inp, f"B{r0+1+i}", s, BLUE, PCT, YEL); put(inp, f"C{r0+1+i}", "Synthetic. Real: map + weather + sun-angle tagging of fleet operation logs.")
put(inp, f"A{r0+6}", "Sum (must be 100%)", BOLD); put(inp, f"B{r0+6}", f"=SUM(B{r0+1}:B{r0+5})", BLACK, PCT)
r1 = r0 + 8
put(inp, f"A{r1}", "Ego speed band", BOLD); put(inp, f"B{r1}", "Time share", BOLD)
for i, (n, s, _, _) in enumerate(ub_sim.SPEEDS):
    put(inp, f"A{r1+1+i}", n); put(inp, f"B{r1+1+i}", s, BLUE, PCT, YEL); put(inp, f"C{r1+1+i}", "Synthetic.")
put(inp, f"A{r1+5}", "Sum (must be 100%)", BOLD); put(inp, f"B{r1+5}", f"=SUM(B{r1+1}:B{r1+4})", BLACK, PCT)
r2 = r1 + 7
put(inp, f"A{r2}", "Follower headway class", BOLD); put(inp, f"B{r2}", "Time share", BOLD)
for i, (n, s, _) in enumerate(ub_sim.HEADWAYS):
    put(inp, f"A{r2+1+i}", n); put(inp, f"B{r2+1+i}", s, BLUE, PCT, YEL); put(inp, f"C{r2+1+i}", "Synthetic. Real: rear radar / camera tracks in fleet logs.")
put(inp, f"A{r2+6}", "Sum (must be 100%)", BOLD); put(inp, f"B{r2+6}", f"=SUM(B{r2+1}:B{r2+5})", BLACK, PCT)
put(inp, f"A{r2+8}", "Independence assumption", BOLD)
put(inp, f"B{r2+8}", "Scenario share = product of the three factor shares. In reality the factors are correlated (e.g. spray and speed, headway and speed) — measure joint shares directly or model the dependence (copula).", wrap=True)
inp.merge_cells(f"B{r2+8}:C{r2+8}")
TRIG_RNG, SPEED_RNG, HW_RNG = (f"Inputs!$A${r0+1}:$A${r0+5}", f"Inputs!$B${r0+1}:$B${r0+5}"), \
    (f"Inputs!$A${r1+1}:$A${r1+4}", f"Inputs!$B${r1+1}:$B${r1+4}"), (f"Inputs!$A${r2+1}:$A${r2+5}", f"Inputs!$B${r2+1}:$B${r2+5}")

# =============== HB Evidence ===============
ev = wb.create_sheet("HB Evidence")
title(ev, "Hazardous-behaviour rate per trigger context × speed band",
      "Open-loop replay of targeted logs through perception + planner. k = unintended brake requests observed in h hours.")
header(ev, 5, ["Cell", "Trigger context", "Speed band", "Replay hours h", "Events k", "λ̂ = k/h [1/h]",
               "λ upper, single 95% [1/h]", "λ upper, Bonferroni C_b [1/h]", "True λ (synthetic) [1/h]",
               "Harm weight G (upper) [h⁻¹ per λ]", "Point risk of cell [1/h]"],
           [7, 34, 12, 12, 9, 13, 16, 16, 15, 17, 15])
for i, c in enumerate(cells):
    r = 6 + i
    put(ev, f"A{r}", c["cell"]); put(ev, f"B{r}", c["trigger"]); put(ev, f"C{r}", c["speed"])
    put(ev, f"D{r}", c["hours"], BLUE, INT, note="Synthetic replay hours; trigger contexts deliberately over-sampled by route choice.")
    put(ev, f"E{r}", c["k"], BLUE, "0", note="Synthetic: drawn as Poisson(true λ · h).")
    put(ev, f"F{r}", f"=E{r}/D{r}", BLACK, SCI)
    put(ev, f"G{r}", f"=CHIINV(1-Inputs!$B$6,2*(E{r}+1))/2/D{r}", BLACK, SCI)
    put(ev, f"H{r}", f"=CHIINV(1-Inputs!$B$10,2*(E{r}+1))/2/D{r}", BLACK, SCI)
    put(ev, f"I{r}", c["true_lam"], GREY, SCI)
    # G_cell = Σ over scenarios in cell of share·p_U·inj  (upper harm per unit HB rate)
    put(ev, f"J{r}", f"=SUMIF(Scenarios!$E$6:$E$105,A{r},Scenarios!$V$6:$V$105)", BLACK, SCI)
    put(ev, f"K{r}", f"=SUMIF(Scenarios!$E$6:$E$105,A{r},Scenarios!$R$6:$R$105)", BLACK, SCI)
put(ev, "C27", "Totals", BOLD); put(ev, "D27", "=SUM(D6:D25)", BLACK, INT); put(ev, "E27", "=SUM(E6:E25)", BLACK, "0")
put(ev, "A29", "λ upper = ½·χ²_{2(k+1)}(C)/h — the lesson 1 formula, applied per cell. Zero events in h hours still gives a bound of ≈3/h at 95%.", GREY)

# =============== Scenarios ===============
sc = wb.create_sheet("Scenarios")
title(sc, "100 logical scenarios", "One row per element of the ODD partition. Contribution = share · λ · P(collision|HB) · E[P(MAIS2+)|collision].")
cols = ["ID", "Trigger context", "Speed band", "Follower headway", "Evidence cell",
        "Share trigger", "Share speed", "Share headway", "Scenario share",
        "λ̂ [1/h]", "λ upper (C_b) [1/h]", "Sim runs N", "Collisions c", "P̂(coll|HB)", "P upper (C_b)",
        "E[P(MAIS2+)|coll]", "Mean Δv at contact [km/h]", "Point contribution [1/h]", "Upper contribution [1/h]",
        "Share of point risk", "Screening bound share·λ_U [1/h]", "Harm weight share·P_U·inj",
        "True λ (synthetic) [1/h]", "Contribution with true λ [1/h]",
        "Σ w of 10 concrete", "Effective sample size (Σw)²/Σw²", "Collisions among 10 concrete",
        "IS estimate E[coll·P(MAIS2+)]", "IS point contribution [1/h]"]
header(sc, 5, cols, [6, 30, 11, 20, 8, 9, 9, 9, 10, 11, 11, 8, 9, 10, 10, 10, 10, 12, 12, 9, 12, 12, 12, 12, 10, 12, 10, 12, 12])
for i, s in enumerate(scen):
    r = 6 + i
    put(sc, f"A{r}", s["id"]); put(sc, f"B{r}", s["trigger"]); put(sc, f"C{r}", s["speed"]); put(sc, f"D{r}", s["headway"]); put(sc, f"E{r}", s["cell"])
    put(sc, f"F{r}", f"=INDEX({TRIG_RNG[1]},MATCH(B{r},{TRIG_RNG[0]},0))", GREEN, PCT)
    put(sc, f"G{r}", f"=INDEX({SPEED_RNG[1]},MATCH(C{r},{SPEED_RNG[0]},0))", GREEN, PCT)
    put(sc, f"H{r}", f"=INDEX({HW_RNG[1]},MATCH(D{r},{HW_RNG[0]},0))", GREEN, PCT)
    put(sc, f"I{r}", f"=F{r}*G{r}*H{r}", BLACK, "0.000%")
    put(sc, f"J{r}", f"=INDEX('HB Evidence'!$F$6:$F$25,MATCH(E{r},'HB Evidence'!$A$6:$A$25,0))", GREEN, SCI)
    put(sc, f"K{r}", f"=INDEX('HB Evidence'!$H$6:$H$25,MATCH(E{r},'HB Evidence'!$A$6:$A$25,0))", GREEN, SCI)
    put(sc, f"L{r}", s["runs"], BLUE, INT)
    put(sc, f"M{r}", s["coll"], BLUE, INT, note="Kinematic Monte Carlo (ub_sim.py), conditioned on an HB occurring.")
    put(sc, f"N{r}", f"=M{r}/L{r}", BLACK, "0.0000")
    put(sc, f"O{r}", f"=IF(M{r}=L{r},1,BETAINV(Inputs!$B$10,M{r}+1,L{r}-M{r}))", BLACK, "0.0000")
    put(sc, f"P{r}", round(s["inj"], 6), BLUE, "0.0000", note="Mean of illustrative injury curve over simulated collisions.")
    put(sc, f"Q{r}", round(s["dv_mean"], 2), BLUE, "0.0")
    put(sc, f"R{r}", f"=I{r}*J{r}*N{r}*P{r}", BLACK, SCI)
    put(sc, f"S{r}", f"=I{r}*K{r}*O{r}*P{r}", BLACK, SCI)
    put(sc, f"T{r}", f"=IF(Summary!$B$6>0,R{r}/Summary!$B$6,0)", BLACK, PCT)
    put(sc, f"U{r}", f"=I{r}*K{r}", BLACK, SCI)
    put(sc, f"V{r}", f"=I{r}*O{r}*P{r}", BLACK, SCI)
    put(sc, f"W{r}", f"=INDEX('HB Evidence'!$I$6:$I$25,MATCH(E{r},'HB Evidence'!$A$6:$A$25,0))", GREY, SCI)
    put(sc, f"X{r}", f"=I{r}*W{r}*N{r}*P{r}", GREY, SCI)
    CS = "'Concrete Scenarios'!"
    put(sc, f"Y{r}", f"=SUMIF({CS}$B$6:$B${CL},A{r},{CS}$N$6:$N${CL})", GREEN, "0.000")
    put(sc, f"Z{r}", f"=IF(SUMIF({CS}$B$6:$B${CL},A{r},{CS}$T$6:$T${CL})>0,Y{r}^2/SUMIF({CS}$B$6:$B${CL},A{r},{CS}$T$6:$T${CL}),0)", BLACK, "0.0")
    put(sc, f"AA{r}", f"=SUMIF({CS}$B$6:$B${CL},A{r},{CS}$O$6:$O${CL})", GREEN, "0")
    put(sc, f"AB{r}", f"=SUMIF({CS}$B$6:$B${CL},A{r},{CS}$S$6:$S${CL})/COUNTIF({CS}$B$6:$B${CL},A{r})", GREEN, SCI)
    put(sc, f"AC{r}", f"=I{r}*J{r}*AB{r}", BLACK, SCI)
sc.freeze_panes = "F6"
put(sc, "A107", "Clopper–Pearson upper bound: P_U = BETAINV(C_b; c+1; N−c). With c = 0 and N = 2000 this is ≈ 7.8/2000 at C_b — the rule of three again, with a Bonferroni-sized confidence.", GREY)

# =============== Summary ===============
sm = wb.create_sheet("Summary")
title(sm, "Summary — does the validation target hold?", "All values recalculate from Inputs, HB Evidence and Scenarios.")
header(sm, 4, ["Quantity", "Value", "Unit", "Verdict / note"], [52, 16, 10, 80])
rows = [
    ("Scenario shares sum (partition check)", "=SUM(Scenarios!I6:I105)", PCT, "-", "Must be 100%: logical scenarios are mutually exclusive and exhaustive within the ODD."),
    ("Point estimate R̂", "=SUM(Scenarios!R6:R105)", SCI, "1/h", "Not evidence by itself — no confidence."),
    ("Bonferroni upper bound R_U", "=SUM(Scenarios!S6:S105)", SCI, "1/h", "All 120 estimated terms bounded simultaneously at C_b; products of upper bounds → conservative."),
    ("Bayesian posterior 95% quantile", bayes_q95, SCI, "1/h", "From ub_sim.py: 200,000 posterior draws, Gamma(k+½, h) for λ, Beta(c+½, N−c+½) for P(coll). Value, not formula."),
    ("Bayesian posterior mean", bayes_mean, SCI, "1/h", "From ub_sim.py."),
    ("Acceptance criterion A_H", "=Inputs!B5", SCI, "1/h", ""),
    ("Budget for known scenarios (1−ε)·A_H", "=Inputs!B11", SCI, "1/h", "The remaining ε·A_H is reserved for unknown triggers (row 21)."),
]
for i, (q, v, fmt, u, n) in enumerate(rows):
    r = 5 + i
    put(sm, f"A{r}", q); put(sm, f"B{r}", v, BLUE if not str(v).startswith("=") else (GREEN if "!" in str(v) else BLACK), fmt)
    put(sm, f"C{r}", u); put(sm, f"D{r}", n)
put(sm, "A13", "Verdicts against the known-scenario budget", BOLD)
put(sm, "A14", "Point estimate"); put(sm, "B14", "=B6/B11", BLACK, "0.00", note="Ratio to budget")
put(sm, "D14", '=IF(B6<=B11,"meets budget (point only — not a valid claim)","exceeds budget")')
put(sm, "A15", "Bonferroni upper bound"); put(sm, "B15", "=B7/B11", BLACK, "0.00")
put(sm, "D15", '=IF(B7<=B11,"PASS at confidence C","FAIL — evidence insufficient, see Validation Targets")')
put(sm, "A16", "Bayesian 95% quantile"); put(sm, "B16", "=B8/B11", BLACK, "0.00")
put(sm, "D16", '=IF(B8<=B11,"PASS at 95% posterior (prior must be justified to the assessor)","FAIL")')

put(sm, "A18", "Link to the Annex C / lesson 1 view", BOLD)
put(sm, "A19", "Average P(harm | HB) = R̂ / Σ share·λ̂"); put(sm, "B19", "=B6/SUMPRODUCT(Scenarios!I6:I105,Scenarios!J6:J105)", BLACK, SCI)
put(sm, "D19", "This is the scenario-averaged product P(E|HB)·P(C̄|E)·P(S|C̄) of Annex C.2.")
put(sm, "A20", "Tolerable overall HB rate R_HB = budget / avg P(harm|HB)"); put(sm, "B20", "=B11/B19", BLACK, SCI); put(sm, "C20", "1/h")
put(sm, "A21", "Field-only alternative: failure-free hours τ = −ln(1−C)/R_HB"); put(sm, "B21", "=-LN(1-Inputs!B6)/B20", BLACK, INT); put(sm, "C21", "h")
put(sm, "D21", "Lesson 1 approach: drive representative hours with zero unintended brakes. Compare with the replay hours in HB Evidence.")
put(sm, "A22", "Unknown-trigger reserve: field hours with no unexplained HB"); put(sm, "B22", "=-LN(1-Inputs!B6)/(Inputs!B7*Inputs!B5/B19)", BLACK, INT); put(sm, "C22", "h")
put(sm, "D22", "Every HB in this field driving must map to a known trigger; an unexplained one counts against ε·A_H.")
put(sm, "A23", "Replay hours used so far"); put(sm, "B23", "='HB Evidence'!D27", GREEN, INT); put(sm, "C23", "h")

put(sm, "A25", "Point risk by trigger context", BOLD); put(sm, "B25", "R̂ [1/h]", BOLD); put(sm, "C25", "Share", BOLD); put(sm, "D25", "Share if λ were known (synthetic truth)", BOLD)
for i, (n, _, _) in enumerate(ub_sim.TRIGGERS):
    r = 26 + i
    put(sm, f"A{r}", n); put(sm, f"B{r}", f"=SUMIF(Scenarios!$B$6:$B$105,A{r},Scenarios!$R$6:$R$105)", BLACK, SCI); put(sm, f"C{r}", f"=B{r}/$B$6", BLACK, PCT)
    put(sm, f"D{r}", f"=SUMIF(Scenarios!$B$6:$B$105,A{r},Scenarios!$X$6:$X$105)/SUM(Scenarios!$X$6:$X$105)", GREY, PCT)
put(sm, "A32", "Point risk by follower headway", BOLD); put(sm, "B32", "R̂ [1/h]", BOLD); put(sm, "C32", "Share", BOLD); put(sm, "D32", "Share if λ were known (synthetic truth)", BOLD)
for i, (n, _, _) in enumerate(ub_sim.HEADWAYS):
    r = 33 + i
    put(sm, f"A{r}", n); put(sm, f"B{r}", f"=SUMIF(Scenarios!$D$6:$D$105,A{r},Scenarios!$R$6:$R$105)", BLACK, SCI); put(sm, f"C{r}", f"=B{r}/$B$6", BLACK, PCT)
    put(sm, f"D{r}", f"=SUMIF(Scenarios!$D$6:$D$105,A{r},Scenarios!$X$6:$X$105)/SUM(Scenarios!$X$6:$X$105)", GREY, PCT)
put(sm, "A39", "Point risk by speed band", BOLD); put(sm, "B39", "R̂ [1/h]", BOLD); put(sm, "C39", "Share", BOLD); put(sm, "D39", "Share if λ were known (synthetic truth)", BOLD)
for i, (n, _, _, _) in enumerate(ub_sim.SPEEDS):
    r = 40 + i
    put(sm, f"A{r}", n); put(sm, f"B{r}", f"=SUMIF(Scenarios!$C$6:$C$105,A{r},Scenarios!$R$6:$R$105)", BLACK, SCI); put(sm, f"C{r}", f"=B{r}/$B$6", BLACK, PCT)
    put(sm, f"D{r}", f"=SUMIF(Scenarios!$C$6:$C$105,A{r},Scenarios!$X$6:$X$105)/SUM(Scenarios!$X$6:$X$105)", GREY, PCT)
put(sm, "A45", "Screening: scenarios whose bound share·λ_U ≤ 0.1% of budget (safe to skip simulation)"); put(sm, "B45", "=COUNTIF(Scenarios!U6:U105,\"<=\"&B11*0.001)", BLACK, "0")
put(sm, "A48", "Reality check (synthetic truth — unknowable in practice)", BOLD)
put(sm, "A49", "Risk if λ were known exactly"); put(sm, "B49", "=SUM(Scenarios!X6:X105)", GREY, SCI); put(sm, "C49", "1/h")
put(sm, "A50", "True overall HB rate Σ share·λ"); put(sm, "B50", "=SUMPRODUCT(Scenarios!I6:I105,Scenarios!W6:W105)", GREY, SCI); put(sm, "C50", "1/h")
put(sm, "A51", "P(field-only zero-failure test of row 21 passes)"); put(sm, "B51", "=EXP(-B50*B21)", GREY, PCT)
put(sm, "D51", "The field-only target looks cheap, but at the true HB rate it is close to a coin flip; a k > 0 plan costs more hours (lesson 1). It also needs avg P(harm|HB), which only the scenario model provides.")
put(sm, "A53", "Same calculation from the 1,000 concrete scenarios only", BOLD)
put(sm, "A54", "Point estimate R̂ from 1,000 importance-sampled concrete runs"); put(sm, "B54", "=SUM(Scenarios!AC6:AC105)", BLACK, SCI); put(sm, "C54", "1/h")
put(sm, "D54", "Uses λ̂ from HB Evidence and the weighted concrete outcomes: Σ share·λ̂·(1/10)Σ w·1{coll}·P(MAIS2+).")
put(sm, "A55", "Ratio to the 200,000-run plain Monte Carlo estimate (row 6)"); put(sm, "B55", "=B54/B6", BLACK, "0.00")
put(sm, "D55", "Same order of magnitude from 200× fewer simulations — that is what importance sampling buys. Plain MC with 10 runs per scenario would almost always see zero collisions.")
put(sm, "A56", "Collisions among the 1,000 concrete scenarios"); put(sm, "B56", "=SUM('Concrete Scenarios'!O6:O%d)" % (5 + len(concrete)), GREEN, "0")
put(sm, "A57", "Median effective sample size per logical scenario (of 10)"); put(sm, "B57", "=MEDIAN(Scenarios!Z6:Z105)", BLACK, "0.0")
put(sm, "D57", "Low ESS means a few heavy weights dominate: the proposal q is too far from f for that scenario. Report ESS with every IS estimate.")
put(sm, "A46", "Sum of their screening bounds"); put(sm, "B46", "=SUMIF(Scenarios!U6:U105,\"<=\"&B11*0.001)", BLACK, SCI); put(sm, "C46", "1/h")

# =============== Concrete Scenarios ===============
cs = wb.create_sheet("Concrete Scenarios")
title(cs, "1,000 concrete scenarios (made up) — 10 per logical scenario",
      "Parameters drawn from the importance-sampling proposal q via the Gaussian copula; w = f(θ)/q(θ) re-weights each run to the real-world model f.")
header(cs, 5, ["Concrete ID", "Logical ID", "Trigger context", "Speed band", "Follower headway",
               "Ego speed v_e [km/h]", "Follower speed v_f [km/h]", "Time headway h [s]", "Gap [m]",
               "Phantom decel a_e [m/s²]", "Phantom duration t_b [s]", "Follower reaction T_r [s]", "Follower decel a_f [m/s²]",
               "IS weight w = f/q", "Collision (1/0)", "Δv at contact [km/h]", "P(MAIS2+ | Δv)",
               "w · collision", "w · collision · P(MAIS2+)", "w²"],
       [9, 8, 30, 11, 20, 10, 10, 10, 9, 10, 10, 10, 10, 11, 9, 10, 10, 10, 12, 10])
for i, c in enumerate(concrete):
    r = 6 + i
    put(cs, f"A{r}", c["cid"]); put(cs, f"B{r}", c["lid"]); put(cs, f"C{r}", c["trigger"]); put(cs, f"D{r}", c["speed"]); put(cs, f"E{r}", c["headway"])
    put(cs, f"F{r}", round(c["v"], 2), BLUE, "0.0"); put(cs, f"G{r}", round(c["vf"], 2), BLUE, "0.0"); put(cs, f"H{r}", round(c["h"], 3), BLUE, "0.00")
    put(cs, f"I{r}", f"=H{r}*G{r}/3.6", BLACK, "0.0")
    put(cs, f"J{r}", round(c["a_e"], 2), BLUE, "0.00"); put(cs, f"K{r}", round(c["t_b"], 3), BLUE, "0.00")
    put(cs, f"L{r}", round(c["t_r"], 3), BLUE, "0.00"); put(cs, f"M{r}", round(c["a_f"], 2), BLUE, "0.00")
    put(cs, f"N{r}", c["w"], BLUE, "0.0000", note="Exact density ratio f/q incl. Gaussian-copula densities (ub_sim.log_density).") if i == 0 else put(cs, f"N{r}", c["w"], BLUE, "0.0000")
    put(cs, f"O{r}", c["hit"], BLUE, "0", note="Outcome of the kinematic simulation (ub_sim.simulate).") if i == 0 else put(cs, f"O{r}", c["hit"], BLUE, "0")
    put(cs, f"P{r}", round(c["dv"], 2), BLUE, "0.0")
    put(cs, f"Q{r}", f"=IF(O{r}=1,1/(1+EXP(-(P{r}-Inputs!$B$12)/Inputs!$B$13)),0)", BLACK, "0.0000")
    put(cs, f"R{r}", f"=N{r}*O{r}", BLACK, "0.0000")
    put(cs, f"S{r}", f"=N{r}*Q{r}", BLACK, "0.000000")
    put(cs, f"T{r}", f"=N{r}^2", BLACK, "0.0000")
cs.freeze_panes = "F6"
put(cs, f"A{CL+2}", "Totals", BOLD); put(cs, f"N{CL+2}", f"=SUM(N6:N{CL})", BLACK, "0.0"); put(cs, f"O{CL+2}", f"=SUM(O6:O{CL})", BLACK, "0")
put(cs, f"A{CL+3}", "Check: mean weight should be ≈ 1 (E_q[w] = 1). Strong deviations mean the proposal misses part of f's support.", GREY)
put(cs, f"N{CL+3}", f"=AVERAGE(N6:N{CL})", BLACK, "0.000")

# =============== Gaussian Copula ===============
gc = wb.create_sheet("Gaussian Copula")
title(gc, "Gaussian copula — how the scenario parameters are coupled", "Explanation, live correlation matrix and Cholesky factor, a live 200-sample demo, and the effect on P(collision | HB).")
gc.column_dimensions["A"].width = 28
for col in "BCDEFGHIJKLMNOPQ":
    gc.column_dimensions[col].width = 12
expl = [
    ("What it is", "A copula is a joint distribution on [0,1]^d with uniform marginals. Sklar's theorem: any joint CDF can be written F(x₁…x_d) = C(F₁(x₁),…,F_d(x_d)). The Gaussian copula is C_R(u) = Φ_R(Φ⁻¹(u₁),…,Φ⁻¹(u_d)), with Φ_R the multivariate normal CDF with correlation matrix R."),
    ("Why for scenarios", "Each scenario parameter has its own natural marginal (uniform speed within a band, lognormal reaction time, uniform deceleration…), but parameters are not independent. The copula separates the two questions: which values does each parameter take (marginals) and how do they move together (R)."),
    ("Sampling (3 steps)", "1) ε ~ N(0, I), Z = L·ε with R = L·Lᵀ (Cholesky).  2) U_i = Φ(Z_i) — now uniform on [0,1] but correlated.  3) X_i = F_i⁻¹(U_i) — apply each marginal's inverse CDF. Live demo below (rows 66+)."),
    ("Density (needed for IS weights)", "c_R(u) = |R|^(−½) · exp(−½ zᵀ(R⁻¹ − I)z), z = Φ⁻¹(u). Joint density f(x) = c_R(F(x)) · Π f_i(x_i). The concrete-scenario weights w = f(θ)/q(θ) use this formula for both f and the proposal q."),
    ("Fitting R from data", "Transform each parameter to pseudo-observations u = rank/(n+1), then z = Φ⁻¹(u); R = correlation matrix of z (normal scores). Alternative per pair: estimate Kendall's τ and use ρ = sin(πτ/2) (row 33). Rank-based fits are invariant to the marginals."),
    ("Validity check", "R must be symmetric positive definite: det(R) > 0 and the Cholesky factor exists (all diagonal entries of L real and > 0). Pairwise-estimated correlations can violate this — then project to the nearest correlation matrix."),
    ("Main limitation", "Zero tail dependence: joint extremes (very late reaction AND very weak braking) become asymptotically independent. If real data show joint extremes more often, the Gaussian copula under-estimates exactly the critical corner. Check with tail-dependence plots; use a t-copula (symmetric tail dependence) or vine copulas (flexible pairwise structure in high dimension)."),
    ("In this example", "R below is ILLUSTRATIVE, not measured. It couples ego speed, follower time headway, follower reaction time and follower deceleration; phantom-brake decel/duration and follower speed offset are independent. The Python simulation used the R values at build time; editing R here drives only the live demo and its correlation check."),
]
for i, (k, v) in enumerate(expl):
    r = 4 + i
    put(gc, f"A{r}", k, BOLD); put(gc, f"B{r}", v, wrap=True)
    gc.merge_cells(f"B{r}:Q{r}"); gc.row_dimensions[r].height = 48

put(gc, "A19", "Correlation matrix R (edit the yellow upper triangle)", BOLD)
names = ["v_e", "h", "T_r", "a_f"]
for j, n in enumerate(names):
    put(gc, f"{chr(66+j)}20", n, BOLD); put(gc, f"A{21+j}", f"{n} — {ub_sim.COPULA_VARS[j]}", BOLD)
for i in range(4):
    for j in range(4):
        ref = f"{chr(66+j)}{21+i}"
        if i == j:
            put(gc, ref, 1, BLACK, "0.00")
        elif j > i:
            put(gc, ref, float(ub_sim.R[i, j]), BLUE, "0.00", YEL)
        else:
            put(gc, ref, f"={chr(66+i)}{21+j}", BLACK, "0.00")
put(gc, "G21", "det(R)", BOLD); put(gc, "H21", "=MDETERM(B21:E24)", BLACK, "0.0000")
put(gc, "G22", "Valid?", BOLD); put(gc, "H22", '=IF(AND(H21>0,ISNUMBER(E30)),"positive definite","NOT positive definite")')

put(gc, "A26", "Cholesky factor L (R = L·Lᵀ), formulas", BOLD)
for j, n in enumerate(names):
    put(gc, f"{chr(66+j)}26", n, BOLD)
Lf = {
    (0, 0): "=SQRT(B21)", (0, 1): "=0", (0, 2): "=0", (0, 3): "=0",
    (1, 0): "=B22/B27", (1, 1): "=SQRT(C22-B28^2)", (1, 2): "=0", (1, 3): "=0",
    (2, 0): "=B23/B27", (2, 1): "=(C23-B29*B28)/C28", (2, 2): "=SQRT(D23-B29^2-C29^2)", (2, 3): "=0",
    (3, 0): "=B24/B27", (3, 1): "=(C24-B30*B28)/C28", (3, 2): "=(D24-B30*B29-C30*C29)/D29", (3, 3): "=SQRT(E24-B30^2-C30^2-D30^2)",
}
for (i, j), f in Lf.items():
    put(gc, f"{chr(66+j)}{27+i}", f, BLACK, "0.0000")
    if j == 0:
        put(gc, f"A{27+i}", names[i], BOLD)

put(gc, "A32", "Kendall τ → Gaussian-copula ρ", BOLD)
put(gc, "A33", "Kendall τ (example)"); put(gc, "B33", -0.20, BLUE, "0.00", YEL)
put(gc, "C33", "ρ = sin(π·τ/2) ="); put(gc, "E33", "=SIN(PI()*B33/2)", BLACK, "0.000")

put(gc, "A35", "Effect of the copula on P(collision | HB) — 20,000 runs each (ub_sim.copula_effect)", BOLD)
for j, hname in enumerate(["Speed band", "Follower headway", "P(coll|HB), Gaussian copula", "P(coll|HB), independent", "Ratio copula / independent", "Runs each"]):
    c = gc.cell(row=36, column=1 + j, value=hname); c.font = HEAD; c.fill = HEADFILL; c.alignment = Alignment(wrap_text=True)
gc.row_dimensions[36].height = 32
for i, e in enumerate(cop_eff):
    r = 37 + i
    put(gc, f"A{r}", e["speed"]); put(gc, f"B{r}", e["headway"])
    put(gc, f"C{r}", e["p_cop"], BLUE, "0.0000"); put(gc, f"D{r}", e["p_ind"], BLUE, "0.0000")
    put(gc, f"E{r}", f"=IF(D{r}>0,C{r}/D{r},\"–\")", BLACK, "0.00"); put(gc, f"F{r}", e["n"], BLUE, INT)
put(gc, "A58", "Reading: with these signs, close followers react faster (h–T_r < 0) but slow reactors also brake weakly (T_r–a_f < 0). Ignoring dependence changes P(collision) by the factor in column E — an error that goes straight into the risk sum.", GREY)

put(gc, "A60", "Live sampling demo — logical scenario parameters (edit yellow)", BOLD)
demo_in = [("Speed band low [km/h]", 35), ("Speed band high [km/h]", 55), ("Headway class low [s]", 1.0), ("Headway class high [s]", 1.5),
           ("T_r log-median [s]", 1.1), ("T_r log-sd", 0.30), ("a_f low [m/s²]", 3.5), ("a_f high [m/s²]", 8.0)]
for i, (k, v) in enumerate(demo_in):
    col = chr(66 + 2 * (i % 4)); row = 61 + i // 4
    put(gc, f"{col}{row}", k); put(gc, f"{chr(ord(col)+1)}{row}", v, BLUE, "0.00", YEL)
# B61/C61 v_lo, D61/E61 v_hi, F61/G61 h_lo, H61/I61 h_hi ; B62/C62 trmed, D62/E62 trsd, F62/G62 af_lo, H62/I62 af_hi
demo_hdr = ["#", "ε₁", "ε₂", "ε₃", "ε₄", "Z₁ (v_e)", "Z₂ (h)", "Z₃ (T_r)", "Z₄ (a_f)", "U₁", "U₂", "U₃", "U₄",
            "v_e [km/h]", "h [s]", "T_r [s]", "a_f [m/s²]"]
for j, hname in enumerate(demo_hdr):
    c = gc.cell(row=65, column=1 + j, value=hname); c.font = HEAD; c.fill = HEADFILL
eps = ub_sim.demo_normals()
for i in range(len(eps)):
    r = 66 + i
    put(gc, f"A{r}", i + 1)
    for j in range(4):
        put(gc, f"{chr(66+j)}{r}", round(float(eps[i, j]), 5), BLUE, "0.000")
    for j in range(4):
        put(gc, f"{chr(70+j)}{r}", f"=SUMPRODUCT($B${27+j}:$E${27+j},B{r}:E{r})", BLACK, "0.000")
        put(gc, f"{chr(74+j)}{r}", f"=NORMSDIST({chr(70+j)}{r})", BLACK, "0.000")
    put(gc, f"N{r}", f"=$C$61+J{r}*($E$61-$C$61)", BLACK, "0.0")
    put(gc, f"O{r}", f"=$G$61+K{r}*($I$61-$G$61)", BLACK, "0.00")
    put(gc, f"P{r}", f"=LOGINV(L{r},LN($C$62),$E$62)", BLACK, "0.00")
    put(gc, f"Q{r}", f"=$G$62+M{r}*($I$62-$G$62)", BLACK, "0.00")
DL = 65 + len(eps)
put(gc, "A63", "Sample correlation check (200 draws): target ρ vs. sample correlation of Z", BOLD)
pairs = [(0, 1), (1, 2), (2, 3), (0, 2), (0, 3), (1, 3)]
for k, (a, b) in enumerate(pairs):
    col = chr(66 + 2 * k)
    put(gc, f"{col}64", f"{names[a]}–{names[b]}: target", GREY)
    put(gc, f"{chr(ord(col)+1)}64", f"={chr(66+b)}{21+a}", BLACK, "0.00")
put(gc, f"A{DL+2}", "Sample correlation", BOLD)
for k, (a, b) in enumerate(pairs):
    col = chr(66 + 2 * k)
    put(gc, f"{col}{DL+2}", f"{names[a]}–{names[b]}", GREY)
    put(gc, f"{chr(ord(col)+1)}{DL+2}", f"=CORREL({chr(70+a)}66:{chr(70+a)}{DL},{chr(70+b)}66:{chr(70+b)}{DL})", BLACK, "0.00")
put(gc, f"A{DL+3}", "Rank (Spearman) correlation of the final parameters equals that of U; Pearson correlation of X can differ because the marginals are nonlinear.", GREY)

# =============== Validation Targets ===============
vt = wb.create_sheet("Validation Targets")
title(vt, "Validation targets per evidence cell", "How many replay hours each cell needs so the Bonferroni bound fits the budget.")
put(vt, "A3", "Optimal allocation: minimise total hours Σ λ_k·G_j/B_j subject to Σ B_j = budget ⇒ B_j ∝ √G_j (Lagrange multiplier). Required hours assume no further events (observed k kept).", GREY)
header(vt, 5, ["Cell", "Trigger context", "Speed band", "Harm weight G_j", "Events k so far", "Hours so far",
               "Budget B_j (optimal, ∝ √G)", "λ target = B_j/G_j [1/h]", "Required hours (optimal)", "Additional hours",
               "Budget B_j (equal split)", "Required hours (equal)"],
           [7, 34, 12, 13, 9, 11, 14, 14, 14, 13, 14, 14])
for i in range(20):
    r, er = 6 + i, 6 + i
    put(vt, f"A{r}", f"='HB Evidence'!A{er}", GREEN); put(vt, f"B{r}", f"='HB Evidence'!B{er}", GREEN); put(vt, f"C{r}", f"='HB Evidence'!C{er}", GREEN)
    put(vt, f"D{r}", f"='HB Evidence'!J{er}", GREEN, SCI); put(vt, f"E{r}", f"='HB Evidence'!E{er}", GREEN, "0"); put(vt, f"F{r}", f"='HB Evidence'!D{er}", GREEN, INT)
    put(vt, f"G{r}", f"=Inputs!$B$11*SQRT(D{r})/SUMPRODUCT(SQRT($D$6:$D$25))", BLACK, SCI)
    put(vt, f"H{r}", f"=G{r}/D{r}", BLACK, SCI)
    put(vt, f"I{r}", f"=CHIINV(1-Inputs!$B$10,2*(E{r}+1))/2/H{r}", BLACK, INT)
    put(vt, f"J{r}", f"=MAX(0,I{r}-F{r})", BLACK, INT)
    put(vt, f"K{r}", "=Inputs!$B$11/20", BLACK, SCI)
    put(vt, f"L{r}", f"=CHIINV(1-Inputs!$B$10,2*(E{r}+1))/2/(K{r}/D{r})", BLACK, INT)
put(vt, "C27", "Totals", BOLD)
for col in "FIJL":
    put(vt, f"{col}27", f"=SUM({col}6:{col}25)", BLACK, INT)
put(vt, "A29", "Caveats", BOLD)
caveats = [
    "G_j uses the Bonferroni upper collision probability, so it also shrinks as you add simulation runs — the two evidence types trade off.",
    "Required hours assume the observed k stays fixed; new events raise the requirement. Plan with margin and fix the plan before testing (lesson 1).",
    "Replay hours only count if the replayed software equals the release candidate and replay (open loop) reproduces the brake decision faithfully.",
    "The Bayesian route (Summary row 8) needs far less evidence but must defend its prior; Jeffreys is the usual 'minimally informative' choice.",
]
for i, t in enumerate(caveats):
    put(vt, f"A{30+i}", f"{i+1}. {t}")

order = ["Overview", "Inputs", "HB Evidence", "Scenarios", "Concrete Scenarios", "Gaussian Copula", "Summary", "Validation Targets"]
wb._sheets = [wb[n] for n in order]
wb.save(OUT)
print("saved", OUT, "bayes", bayes_q95, bayes_mean)
