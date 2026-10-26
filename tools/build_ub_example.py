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

cells, scen = ub_sim.generate()
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
    ("Sheets", "Inputs → HB Evidence (20 cells) → Scenarios (100 rows) → Summary → Validation Targets (how much more evidence each cell needs)."),
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
        "True λ (synthetic) [1/h]", "Contribution with true λ [1/h]"]
header(sc, 5, cols, [6, 30, 11, 20, 8, 9, 9, 9, 10, 11, 11, 8, 9, 10, 10, 10, 10, 12, 12, 9, 12, 12, 12, 12])
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
put(sm, "A46", "Sum of their screening bounds"); put(sm, "B46", "=SUMIF(Scenarios!U6:U105,\"<=\"&B11*0.001)", BLACK, SCI); put(sm, "C46", "1/h")

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

wb.save(OUT)
print("saved", OUT, "bayes", bayes_q95, bayes_mean)
