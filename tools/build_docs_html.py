"""
build_docs_html.py — renders docs/01..04 as HTML pages with MathJax formulas and inline SVG plots.

All plots are computed from ub_sim.py and from the recalculated workbook
tools/unintended_braking_risk_example.xlsx (run build_ub_example.py + a recalc first).
Synthetic, illustrative data throughout.
"""
import io, math, os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from scipy.stats import norm, lognorm, poisson, genpareto, t as student_t, chi2
from openpyxl import load_workbook
import ub_sim

HERE = os.path.dirname(os.path.abspath(__file__))
DOCS = os.path.join(HERE, "..", "docs")
XLSX = os.path.join(HERE, "unintended_braking_risk_example.xlsx")

# ---------- chart style (reference palette, light chart surface; figures sit on their own card) ----------
S1, S2, S3 = "#2a78d6", "#eb6834", "#1baf7a"     # categorical slots 1-3
INK, INK2, MUTED, GRID, SURF = "#0b0b0b", "#52514e", "#8a8984", "#e6e5e1", "#fcfcfb"
plt.rcParams.update({
    "svg.fonttype": "none", "font.family": ["DejaVu Sans"], "font.size": 10.5,
    "axes.edgecolor": MUTED, "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2, "text.color": INK,
    "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.8, "axes.spines.top": False, "axes.spines.right": False,
    "axes.facecolor": SURF, "figure.facecolor": SURF, "axes.titlesize": 11, "axes.titleweight": "bold",
    "axes.titlelocation": "left", "legend.frameon": False, "lines.linewidth": 2,
})


def svg(fig):
    buf = io.StringIO()
    fig.savefig(buf, format="svg", bbox_inches="tight", dpi=150)
    plt.close(fig)
    s = buf.getvalue()
    s = s[s.index("<svg"):]
    return s.replace("<svg ", '<svg role="img" preserveAspectRatio="xMidYMid meet" ', 1)


def figure(svg_str, caption, n):
    return f'<figure class="plot"><div class="plot-svg">{svg_str}</div><figcaption><b>Figure {n}.</b> {caption}</figcaption></figure>'


# ---------- data ----------
print("generating evidence (≈20 s)…")
cells, scen, conc = ub_sim.generate()
wb = load_workbook(XLSX, data_only=True)
sm, vt, gcs, scs = wb["Summary"], wb["Validation Targets"], wb["Gaussian Copula"], wb["Scenarios"]
R_point, R_bonf, R_bayes, budget = sm["B6"].value, sm["B7"].value, sm["B8"].value, sm["B11"].value
R_is, ess_med, n_hits = sm["B54"].value, sm["B57"].value, sm["B56"].value
assert R_point is not None, "Recalculate the workbook first (recalc.py)."

# =====================================================================================
# Figures — doc 01
# =====================================================================================
def fig_toy_cutin():
    rng = np.random.default_rng(1)
    fail = lambda g, v: (v > 0) & (g / np.maximum(v, 1e-9) < 1.2)
    N = 2000; g = rng.uniform(2, 60, N); v = rng.uniform(-2, 10, N); crit = fail(g, v)
    M = 4_000_000; G = np.exp(rng.normal(np.log(25), 0.5, M)); V = rng.normal(1, 1.5, M); p_true = fail(G, V).mean()
    gg, vv = np.meshgrid(np.linspace(2, 60, 300), np.linspace(-2, 10, 300))
    dens = lognorm.pdf(gg, s=0.5, scale=25) * norm.pdf(vv, 1, 1.5)
    fig, ax = plt.subplots(figsize=(7.2, 4.2))
    ax.contourf(gg, vv, dens, levels=8, cmap="Blues", alpha=0.85).set_rasterized(True)
    ax.scatter(g[~crit], v[~crit], s=6, color=MUTED, alpha=0.5, lw=0, label="test run, not critical", rasterized=True)
    ax.scatter(g[crit], v[crit], s=10, color=S2, lw=0, label="test run, critical (TTC < 1.2 s)", rasterized=True)
    x = np.linspace(2, 60, 50); ax.plot(x, x / 1.2, color=INK, lw=1.2, ls="--")
    ax.text(14, 9.2, "failure region: gap / closing speed < 1.2 s", color=INK, fontsize=9.5)
    ax.set_xlim(2, 60); ax.set_ylim(-2, 10)
    ax.set_xlabel("Initial gap g [m]"); ax.set_ylabel("Closing speed v [m/s]")
    ax.set_title("Where the test runs are vs. where real cut-ins are")
    ax.legend(loc="lower right", fontsize=9)
    ax.text(40, 3.4, "real-world density f(θ)\n(shaded, darker = more likely)", color="#1f4e8c", fontsize=9)
    return svg(fig), crit.mean(), p_true


def fig_convergence():
    rng = np.random.default_rng(4); s = (35, 55); h = (1.0, 1.5); n = 20000
    thf = ub_sim.sample_theta(s, h, n, rng); hf, _ = ub_sim.simulate(thf)
    thq = ub_sim.sample_theta(s, h, n, rng, proposal=True); hq, _ = ub_sim.simulate(thq)
    w = np.exp(ub_sim.log_density(thq, s, h, False) - ub_sim.log_density(thq, s, h, True))
    thr = ub_sim.sample_theta(s, h, 200000, rng); ref = ub_sim.simulate(thr)[0].mean()
    k = np.arange(1, n + 1)
    mc, isr = np.cumsum(hf) / k, np.cumsum(w * hq) / k
    fig, ax = plt.subplots(figsize=(7.2, 3.8))
    ax.plot(k, mc, color=S1, label="plain Monte Carlo from f")
    ax.plot(k, isr, color=S2, label="importance sampling from q, weighted by f/q")
    ax.axhline(ref, color=INK, lw=1, ls="--"); ax.text(1.2, ref * 1.08, f"reference (200,000 plain runs): {ref:.4f}", fontsize=9)
    ax.set_xscale("log"); ax.set_ylim(0, ref * 3)
    ax.set_xlabel("Number of simulation runs"); ax.set_ylabel("Estimated P(collision | HB)")
    ax.set_title("Running estimate for one logical scenario (35–55 km/h, follower 1–1.5 s)")
    ax.legend(loc="upper right", fontsize=9)
    return svg(fig), ref


def fig_pareto():
    pts = sorted([scs[f"R{r}"].value for r in range(6, 106)], reverse=True)
    tru = sorted([scs[f"X{r}"].value for r in range(6, 106)], reverse=True)
    cp, ct = np.cumsum(pts) / sum(pts), np.cumsum(tru) / sum(tru)
    x = np.arange(1, 101)
    fig, ax = plt.subplots(figsize=(7.2, 3.8))
    ax.step(x, cp, where="post", color=S1, label="point estimate (from observed HB counts)")
    ax.step(x, ct, where="post", color=MUTED, ls="--", label="if the HB rates were known (synthetic truth)")
    i10 = cp[9]; ax.annotate(f"top 10 scenarios: {i10:.0%}", (10, i10), (22, i10 - 0.18), arrowprops=dict(arrowstyle="-", color=INK2), fontsize=9.5)
    nz = int((np.array(pts) > 0).sum())
    ax.annotate(f"{100-nz} scenarios contribute 0\n(no HB observed, or no collision simulated)", (nz, 1.0), (45, 0.55),
                arrowprops=dict(arrowstyle="-", color=INK2), fontsize=9)
    ax.set_xlim(0, 100); ax.set_ylim(0, 1.03)
    ax.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0))
    ax.set_xlabel("Logical scenarios, sorted by contribution"); ax.set_ylabel("Cumulative share of risk")
    ax.set_title("Risk is concentrated in a few scenarios")
    ax.legend(loc="lower right", fontsize=9)
    return svg(fig), i10


def fig_posterior():
    rng = np.random.default_rng(7); draws = 200_000
    lam = {c["cell"]: rng.gamma(c["k"] + 0.5, 1.0 / c["hours"], draws) for c in cells}
    Rt = np.zeros(draws)
    for s in scen:
        p = rng.beta(s["coll"] + 0.5, s["runs"] - s["coll"] + 0.5, draws)
        Rt += s["s_trig"] * s["s_speed"] * s["s_hw"] * lam[s["cell"]] * p * s["inj"]
    fig, ax = plt.subplots(figsize=(7.2, 3.8))
    bins = np.logspace(np.log10(np.quantile(Rt, 0.001)), np.log10(max(R_bonf, Rt.max()) * 1.2), 70)
    ax.hist(Rt, bins=bins, color=S1, alpha=0.85, edgecolor=SURF, linewidth=0.6)
    ax.set_xscale("log")
    ymax = ax.get_ylim()[1]
    for xv, lab, col, ls in [(R_point, "point estimate", INK2, ":"), (np.quantile(Rt, 0.95), "Bayesian 95% quantile", S1, "-"),
                             (budget, "budget (1−ε)·A_H", S3, "-"), (R_bonf, "Bonferroni bound", S2, "--")]:
        ax.axvline(xv, color=col, ls=ls, lw=1.6)
        ax.text(xv * 1.06, ymax * (0.92 if lab != "point estimate" else 0.75), lab, rotation=90, va="top", fontsize=9, color=INK)
    ax.set_xlabel("Total risk R  [MAIS2+ injuries per operating hour]"); ax.set_ylabel("Posterior draws")
    ax.set_title("What the evidence says about R: posterior vs. bounds")
    return svg(fig)


def fig_evidence_targets():
    rows = [(vt[f"A{r}"].value, vt[f"F{r}"].value, vt[f"I{r}"].value) for r in range(6, 26)]
    labels = [r[0] for r in rows]; have = np.array([r[1] for r in rows]); need = np.array([r[2] for r in rows])
    y = np.arange(len(rows))
    fig, ax = plt.subplots(figsize=(7.2, 5.6))
    ax.barh(y + 0.2, need / 1000, height=0.38, color=S2, label="required (optimal allocation, Bonferroni)")
    ax.barh(y - 0.2, have / 1000, height=0.38, color=S1, label="replay hours so far")
    ax.set_yticks(y, labels); ax.invert_yaxis()
    ax.set_xlabel("Replay hours [thousand h]"); ax.set_title("Evidence needed per cell (trigger T1–T5 × speed band S1–S4)")
    ax.legend(loc="lower right", fontsize=9); ax.grid(axis="y", visible=False)
    ax.text(need.max() / 1000 * 0.42, 9.5, "T1 = clear road: no HB observed,\nbut the largest exposure → largest target", fontsize=9, color=INK)
    return svg(fig), have.sum(), need.sum()

# =====================================================================================
# Figures — doc 02
# =====================================================================================
def fig_rate_bound():
    T = np.logspace(2, 7, 200)
    fig, ax = plt.subplots(figsize=(7.2, 3.8))
    for k, col in zip((0, 1, 2), (S1, S2, S3)):
        ax.plot(T, chi2.ppf(0.95, 2 * (k + 1)) / 2 / T, color=col, label=f"{k} event{'s' if k != 1 else ''} observed")
    ax.set_xscale("log"); ax.set_yscale("log")
    ax.axhline(1e-4, color=INK2, lw=1, ls="--"); ax.text(1.3e2, 1.25e-4, "example SPI threshold 10⁻⁴ /h", fontsize=9)
    ax.set_xlabel("Exposure T [h]"); ax.set_ylabel("95% upper bound on the rate [1/h]")
    ax.set_title("A rate claim is only as strong as its denominator")
    ax.legend(fontsize=9)
    return svg(fig)


def mu_star(alpha=0.05, power=0.8):
    """Smallest expected count μ at which a one-sided exact Poisson test detects a doubled rate with the given power."""
    for mu in np.linspace(0.5, 60, 2000):
        c = int(poisson.ppf(1 - alpha, mu)) + 1            # reject if X ≥ c
        while poisson.sf(c - 1, mu) > alpha: c += 1
        if poisson.sf(c - 1, 2 * mu) >= power:
            return mu
    return float("nan")


def fig_detect():
    mu = mu_star()
    lam = np.logspace(-9, -1, 100)
    hours = mu / lam
    fleet_h = 50 * 3000
    fig, ax = plt.subplots(figsize=(7.2, 4.2))
    ax.plot(lam, hours / fleet_h, color=S1)
    spis = [(3e-8, "injury collision\n(lagging)"), (1e-6, "any rear-end struck\n(lagging)"), (1e-4, "unexplained brake request\n(leading)"),
            (1e-3, "rear TTC < 1.5 s after\nego braking (leading)"), (1e-2, "suppressed FP brake\ndetection (leading)")]
    for l, lab in spis:
        yv = mu / l / fleet_h
        ax.scatter([l], [yv], s=40, color=S2 if "lagging" in lab else S3, zorder=3, edgecolor=SURF, linewidth=1.5)
        ax.annotate(lab, (l, yv), (6, 6), textcoords="offset points", fontsize=8.5)
    ax.set_xscale("log"); ax.set_yscale("log")
    ax.axhline(1 / 52, color=INK2, lw=1, ls=":"); ax.text(1.5e-9, 1 / 52 * 1.3, "1 week", fontsize=9)
    ax.axhline(1, color=INK2, lw=1, ls=":"); ax.text(1.5e-9, 1.3, "1 year", fontsize=9)
    ax.set_xlabel("Baseline rate of the SPI event [1/h]")
    ax.set_ylabel("Fleet time to detect a doubling [years]")
    ax.set_title("Time to detect a 2× drift, 50 vehicles × 3,000 h/yr")
    ax.legend(handles=[Line2D([], [], marker="o", ls="", color=S2, label="lagging SPI"), Line2D([], [], marker="o", ls="", color=S3, label="leading SPI")],
              loc="upper right", fontsize=9)
    return svg(fig), mu


def fig_evt():
    rng = np.random.default_rng(12)
    n = 20000
    ttc = np.exp(rng.normal(np.log(3.0), 0.45, n))               # synthetic min-TTC per encounter [s]
    y = -ttc; u = np.quantile(y, 0.95); exc = y[y > u] - u
    c, loc, sc = genpareto.fit(exc, floc=0)
    xs = np.sort(ttc)
    emp = np.arange(1, n + 1) / n
    fig, ax = plt.subplots(figsize=(7.2, 3.9))
    ax.plot(xs, emp, color=S1, lw=2, label="empirical P(min TTC < x)")
    xg = np.linspace(0.0, -u, 200)
    tail = 0.05 * genpareto.sf(-xg - u, c, 0, sc)
    ax.plot(xg, tail, color=S2, ls="--", label="GPD tail fit, extrapolated")
    ax.axvline(-u, color=INK2, lw=1, ls=":"); ax.text(-u * 1.02, 2e-1, "threshold\n(5% lowest)", fontsize=9)
    ax.set_yscale("log"); ax.set_xlim(0, 4); ax.set_ylim(1e-7, 1)
    p0 = 0.05 * genpareto.sf(0 - u, c, 0, sc)
    ax.scatter([0.3], [0.05 * genpareto.sf(-0.3 - u, c, 0, sc)], color=S2, s=30, zorder=3)
    ax.text(0.35, 0.05 * genpareto.sf(-0.3 - u, c, 0, sc) * 2, "extrapolated P(min TTC < 0.3 s)", fontsize=9)
    ax.set_xlabel("min TTC x [s]"); ax.set_ylabel("Probability per encounter")
    ax.set_title("Extreme-value extrapolation from near misses (synthetic)")
    ax.legend(loc="lower right", fontsize=9)
    return svg(fig)

# =====================================================================================
# Figures — doc 03
# =====================================================================================
def fig_marginals():
    fig, axs = plt.subplots(1, 4, figsize=(9.6, 2.7))
    s = np.linspace(1.0, 1.5, 200); w = 0.5
    axs[0].plot(s, np.full_like(s, 1 / w), color=S1); axs[0].plot(s, 2 * (1 - (s - 1.0) / w) / w, color=S2)
    axs[0].set_title("Headway h (class 1–1.5 s)"); axs[0].set_xlabel("[s]")
    x = np.linspace(0.2, 4, 300)
    axs[1].plot(x, lognorm.pdf(x, s=ub_sim.TR_F[1], scale=math.exp(ub_sim.TR_F[0])), color=S1)
    axs[1].plot(x, lognorm.pdf(x, s=ub_sim.TR_Q[1], scale=math.exp(ub_sim.TR_Q[0])), color=S2)
    axs[1].set_title("Follower reaction T_r"); axs[1].set_xlabel("[s]")
    x = np.linspace(0.05, 5, 300)
    axs[2].plot(x, lognorm.pdf(x, s=ub_sim.TB_F[1], scale=math.exp(ub_sim.TB_F[0])), color=S1)
    axs[2].plot(x, lognorm.pdf(x, s=ub_sim.TB_Q[1], scale=math.exp(ub_sim.TB_Q[0])), color=S2)
    axs[2].set_title("Phantom-brake duration t_b"); axs[2].set_xlabel("[s]")
    x = np.linspace(3, 8.5, 300); d = np.where((x >= 3.5) & (x <= 8), 1 / 4.5, 0)
    axs[3].plot(x, d, color=S1); axs[3].plot(x, d, color=S2, ls=(0, (3, 3)))
    axs[3].set_title("Follower decel a_f"); axs[3].set_xlabel("[m/s²]")
    for a in axs: a.set_yticks([]); a.set_ylim(bottom=0)
    axs[0].set_ylabel("density")
    fig.legend(handles=[Line2D([], [], color=S1, label="real-world model f"), Line2D([], [], color=S2, label="IS proposal q")],
               loc="upper center", ncol=2, bbox_to_anchor=(0.5, 1.12), fontsize=9.5)
    fig.tight_layout()
    return svg(fig)


def fig_copula_scatter():
    rng = np.random.default_rng(21); n = 1500; rho = -0.4
    L = np.linalg.cholesky(np.array([[1, rho], [rho, 1]]))
    e = rng.standard_normal((n, 2)); z = e @ L.T
    ui, uc = norm.cdf(e), norm.cdf(z)
    tr = np.exp(ub_sim.TR_F[0] + ub_sim.TR_F[1] * z[:, 0]); af = 3.5 + 4.5 * uc[:, 1]
    fig, axs = plt.subplots(1, 3, figsize=(9.6, 3.3))
    axs[0].scatter(ui[:, 0], ui[:, 1], s=4, color=MUTED, lw=0, rasterized=True); axs[0].set_title("Independent (U-space)")
    axs[1].scatter(uc[:, 0], uc[:, 1], s=4, color=S1, lw=0, rasterized=True); axs[1].set_title("Gaussian copula ρ = −0.4 (U-space)")
    for a in axs[:2]: a.set_xlabel("U₃ (reaction time)"); a.set_xlim(0, 1); a.set_ylim(0, 1); a.set_aspect("equal")
    axs[0].set_ylabel("U₄ (deceleration)")
    axs[2].scatter(tr, af, s=4, color=S1, lw=0, rasterized=True); axs[2].set_title("Same draws, physical units")
    axs[2].set_xlabel("T_r [s]"); axs[2].set_ylabel("a_f [m/s²]")
    axs[2].text(1.75, 7.5, "late reactors\nbrake less hard", fontsize=9)
    fig.tight_layout()
    return svg(fig)


def fig_tail():
    rng = np.random.default_rng(31); n = 20000; rho = 0.6; nu = 3
    Lc = np.linalg.cholesky(np.array([[1, rho], [rho, 1]]))
    zg = rng.standard_normal((n, 2)) @ Lc.T; ug = norm.cdf(zg)
    w = np.sqrt(nu / rng.chisquare(nu, n))[:, None]; zt = (rng.standard_normal((n, 2)) @ Lc.T) * w; ut = student_t.cdf(zt, nu)
    q = 0.99
    fig, axs = plt.subplots(1, 2, figsize=(8.4, 3.6))
    out = []
    for a, u, lab, col in [(axs[0], ug, "Gaussian copula", S1), (axs[1], ut, "t-copula (ν = 3)", S2)]:
        m = (u[:, 0] > q) & (u[:, 1] > q)
        a.scatter(u[:, 0], u[:, 1], s=2, color=col, lw=0, alpha=0.35, rasterized=True)
        a.scatter(u[m, 0], u[m, 1], s=8, color=INK, lw=0)
        a.add_patch(plt.Rectangle((q, q), 1 - q, 1 - q, fill=False, ec=INK, lw=1))
        a.set_xlim(0.9, 1); a.set_ylim(0.9, 1); a.set_aspect("equal")
        a.set_title(f"{lab}: {m.sum()} joint extremes")
        a.set_xlabel("U₁"); out.append(int(m.sum()))
    axs[0].set_ylabel("U₂")
    fig.suptitle(f"Upper-right corner (both above the 99th percentile), same ρ = {rho}, {n:,} draws; independence would give ≈ {n*(1-q)**2:.0f}",
                 fontsize=9.5, x=0.02, ha="left", y=1.02, color=INK2)
    fig.tight_layout()
    return svg(fig), out


def fig_copula_heat():
    speeds = [s[0] for s in ub_sim.SPEEDS]; hws = [h[0] for h in ub_sim.HEADWAYS][1:]
    M = np.full((len(speeds), len(hws)), np.nan)
    for r in range(37, 57):
        sp, hw, pc, pi = gcs[f"A{r}"].value, gcs[f"B{r}"].value, gcs[f"C{r}"].value, gcs[f"D{r}"].value
        if hw in hws and pi:
            M[speeds.index(sp), hws.index(hw)] = pc / pi
    fig, ax = plt.subplots(figsize=(7.2, 3.3))
    im = ax.imshow(M, cmap="Blues", vmin=1, vmax=np.nanmax(M) * 1.05, aspect="auto")
    for i in range(M.shape[0]):
        for j in range(M.shape[1]):
            if not np.isnan(M[i, j]):
                ax.text(j, i, f"{M[i, j]:.2f}×", ha="center", va="center", fontsize=10, color=INK if M[i, j] < np.nanmax(M) * 0.7 else "white")
    ax.set_xticks(range(len(hws)), [h.replace("Follower ", "") for h in hws]); ax.set_yticks(range(len(speeds)), speeds)
    ax.set_xlabel("Follower time headway"); ax.grid(False)
    ax.set_title("P(collision | HB): Gaussian copula ÷ independent parameters")
    fig.colorbar(im, ax=ax, fraction=0.03, pad=0.02).outline.set_visible(False)
    return svg(fig), np.nanmin(M), np.nanmax(M)

# =====================================================================================
# Figures — doc 04
# =====================================================================================
def trajectory(v_kmh, h, a_e, t_b, t_r, a_f, dt=0.01, t_max=6):
    ve = vf = v_kmh / 3.6; gap = h * vf; T, VE, VF, GP = [], [], [], []; t = 0.0; hit = None
    while t < t_max:
        if t < t_b and ve > 0: ve = max(ve - a_e * dt, 0)
        if t >= t_r and vf > ve: vf = max(vf - a_f * dt, ve)
        gap -= (vf - ve) * dt
        T.append(t); VE.append(ve * 3.6); VF.append(vf * 3.6); GP.append(gap)
        if gap <= 0 and hit is None: hit = (t, (vf - ve) * 3.6); break
        t += dt
    return np.array(T), np.array(VE), np.array(VF), np.array(GP), hit


def fig_trajectories():
    fig, axs = plt.subplots(1, 2, figsize=(9.6, 3.4))
    cases = [(dict(v_kmh=45, h=0.8, a_e=5.0, t_b=1.6, t_r=1.6, a_f=4.0), "h = 0.8 s, T_r = 1.6 s, a_f = 4.0", S2),
             (dict(v_kmh=45, h=1.4, a_e=5.0, t_b=1.6, t_r=1.1, a_f=6.0), "h = 1.4 s, T_r = 1.1 s, a_f = 6.0", S1)]
    for kw, lab, col in cases:
        T, VE, VF, GP, hit = trajectory(**kw)
        axs[0].plot(T, VF, color=col, label=f"follower ({lab})")
        axs[1].plot(T, GP, color=col, label=lab)
        if hit:
            axs[1].scatter([hit[0]], [0], color=col, s=40, zorder=3, edgecolor=SURF, lw=1.5)
            axs[1].annotate(f"contact, Δv = {hit[1]:.0f} km/h", (hit[0], 0), (-120, 18), textcoords="offset points", fontsize=9)
    T, VE, _, _, _ = trajectory(**cases[1][0])
    axs[0].plot(T, VE, color=INK, lw=1.6, ls="--", label="ego (phantom brake 5 m/s² for 1.6 s)")
    axs[0].set_xlabel("time since phantom-brake onset [s]"); axs[0].set_ylabel("speed [km/h]"); axs[0].set_title("Speeds")
    axs[0].legend(fontsize=8, loc="lower left")
    axs[1].axhline(0, color=INK2, lw=1); axs[1].set_xlabel("time [s]"); axs[1].set_ylabel("gap [m]"); axs[1].set_title("Gap to follower")
    axs[1].legend(fontsize=8, loc="upper right")
    fig.tight_layout()
    return svg(fig)


def fig_weights():
    w = np.array([c["w"] for c in conc]); hit = np.array([c["hit"] for c in conc])
    ess = [scs[f"Z{r}"].value for r in range(6, 106)]
    fig, axs = plt.subplots(1, 2, figsize=(9.6, 3.3))
    bins = np.linspace(np.log10(w.min()) - 0.1, np.log10(w.max()) + 0.1, 40)
    axs[0].hist(np.log10(w[hit == 0]), bins=bins, color=MUTED, edgecolor=SURF, lw=0.5, label="no collision")
    axs[0].hist(np.log10(w[hit == 1]), bins=bins, color=S2, edgecolor=SURF, lw=0.5, label="collision")
    axs[0].axvline(0, color=INK, lw=1, ls="--"); axs[0].text(0.05, axs[0].get_ylim()[1] * 0.9, "w = 1", fontsize=9)
    axs[0].set_xlabel("log₁₀ weight w = f/q"); axs[0].set_ylabel("concrete scenarios"); axs[0].set_title("Weights of the 1,000 runs")
    axs[0].legend(fontsize=9)
    axs[1].hist(ess, bins=np.arange(0, 10.5, 0.5), color=S1, edgecolor=SURF, lw=0.5)
    axs[1].axvline(np.median(ess), color=INK, lw=1, ls="--"); axs[1].text(np.median(ess) + 0.15, axs[1].get_ylim()[1] * 0.9, f"median {np.median(ess):.1f}", fontsize=9)
    axs[1].set_xlabel("effective sample size (of 10)"); axs[1].set_ylabel("logical scenarios"); axs[1].set_title("How many runs really count")
    fig.tight_layout()
    return svg(fig)


def fig_concrete_scatter():
    h = np.array([c["h"] for c in conc]); tr = np.array([c["t_r"] for c in conc]); hit = np.array([c["hit"] for c in conc]); w = np.array([c["w"] for c in conc])
    fig, ax = plt.subplots(figsize=(7.2, 4.0))
    size = 6 + 40 * np.clip(np.log10(w) + 2, 0, 4) / 4
    ax.scatter(h[hit == 0], tr[hit == 0], s=size[hit == 0], color=MUTED, alpha=0.45, lw=0, label="no collision", rasterized=True)
    ax.scatter(h[hit == 1], tr[hit == 1], s=size[hit == 1], color=S2, alpha=0.9, lw=0, label="collision")
    for b in (1.0, 1.5, 2.0, 3.0): ax.axvline(b, color=GRID, lw=1, zorder=0)
    ax.set_xscale("log"); ax.set_xticks([0.5, 1, 1.5, 2, 3, 6], ["0.5", "1", "1.5", "2", "3", "6"])
    ax.set_xlabel("Follower time headway h [s] (class borders as lines)"); ax.set_ylabel("Follower reaction time T_r [s]")
    ax.set_title("The 1,000 concrete scenarios (marker size ∝ log weight)")
    ax.legend(fontsize=9, loc="upper right")
    return svg(fig)



# =====================================================================================
# Report (05) — figures from the workbook
# =====================================================================================
TRIG_SHORT = ["Clear road", "Overhead structure", "Low sun / shadow", "Spray / rain", "Roadside clutter"]
HW_SHORT = ["none < 3 s", "2–3 s", "1.5–2 s", "1–1.5 s", "< 1 s"]
SPD = [s[0] for s in ub_sim.SPEEDS]


def rfig_verdict():
    vals = [("Point estimate (200,000 runs)", R_point, MUTED), ("Point estimate (1,000 IS runs)", R_is, MUTED),
            ("Bayesian 95% quantile", R_bayes, S1), ("Bonferroni upper bound", R_bonf, S2)]
    fig, ax = plt.subplots(figsize=(7.2, 2.6))
    y = np.arange(len(vals))[::-1]
    for yi, (lab, v, col) in zip(y, vals):
        ax.barh(yi, v, color=col, height=0.55)
        ax.text(v * 1.15, yi, f"{v:.1e}", va="center", fontsize=9.5, color=INK)
    ax.set_yticks(y, [v[0] for v in vals]); ax.set_xscale("log"); ax.set_xlim(3e-9, 3e-6)
    ax.axvline(budget, color=S3, lw=2); ax.text(budget * 1.08, y[-1] - 0.45, "budget 9e-08", fontsize=9, color=INK)
    ax.set_xlabel("MAIS2+ injuries per operating hour"); ax.grid(axis="y", visible=False)
    ax.set_title("Verdict: passes only under the Bayesian argument")
    return svg(fig)


def rfig_exposure():
    fig, axs = plt.subplots(1, 3, figsize=(9.6, 2.6), sharey=False)
    for a, names, shares, t in [(axs[0], TRIG_SHORT, [x[1] for x in ub_sim.TRIGGERS], "Trigger context"),
                                (axs[1], SPD, [x[1] for x in ub_sim.SPEEDS], "Ego speed band"),
                                (axs[2], HW_SHORT, [x[1] for x in ub_sim.HEADWAYS], "Follower headway")]:
        yy = np.arange(len(names))[::-1]
        a.barh(yy, shares, color=S1, height=0.6)
        for yi, sv in zip(yy, shares): a.text(sv + 0.01, yi, f"{sv:.0%}", va="center", fontsize=9)
        a.set_yticks(yy, names); a.set_xlim(0, max(shares) * 1.3); a.set_title(t); a.grid(axis="y", visible=False)
        a.xaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0, decimals=0))
    fig.tight_layout()
    return svg(fig)


def rfig_hb():
    fig, ax = plt.subplots(figsize=(7.2, 5.4))
    for i, c in enumerate(cells):
        y = len(cells) - 1 - i; k, h = c["k"], c["hours"]
        lo = chi2.ppf(0.025, 2 * k) / 2 / h if k > 0 else 1e-7
        hi = chi2.ppf(0.975, 2 * k + 2) / 2 / h
        ax.plot([lo, hi], [y, y], color=S1, lw=2, solid_capstyle="round")
        if k > 0: ax.scatter([k / h], [y], color=S1, s=30, zorder=3, edgecolor=SURF, lw=1.2)
        else: ax.text(1.15e-7, y + 0.15, "k = 0", fontsize=8, color=INK2)
        ax.scatter([c["true_lam"]], [y], marker="D", color=MUTED, s=22, zorder=4)
    ax.set_yticks(range(len(cells)), [f"{c['cell']}  ({c['k']} in {c['hours']/1000:.1f}k h)" for c in cells][::-1], fontsize=8.5)
    ax.set_xscale("log"); ax.set_xlim(1e-7, 1e-2); ax.grid(axis="y", visible=False)
    ax.set_xlabel("Unintended-braking rate λ [1/h]")
    ax.set_title("HB rate per evidence cell: estimate and exact 95% interval")
    ax.legend(handles=[Line2D([], [], color=S1, marker="o", label="observed k/h with 95% CI"),
                       Line2D([], [], color=MUTED, marker="D", ls="", label="true λ (synthetic, unknowable)")], fontsize=8.5, loc="upper center", bbox_to_anchor=(0.5, -0.1), ncol=2)
    return svg(fig)


def _grid(field):
    M = np.zeros((len(SPD), len(HW_SHORT))); n = np.zeros_like(M)
    for s in scen:
        i = SPD.index(s["speed"]); j = [h[0] for h in ub_sim.HEADWAYS].index(s["headway"])
        M[i, j] += field(s); n[i, j] += 1
    return M / n


def heat(ax, M, title, fmt, cmap="Blues"):
    im = ax.imshow(M, cmap=cmap, aspect="auto", vmin=0)
    for i in range(M.shape[0]):
        for j in range(M.shape[1]):
            ax.text(j, i, fmt(M[i, j]), ha="center", va="center", fontsize=8.5, color="white" if M[i, j] > M.max() * 0.6 else INK)
    ax.set_xticks(range(M.shape[1]), HW_SHORT, fontsize=8.5); ax.grid(False); ax.set_title(title)
    return im


def rfig_coll_inj():
    pc = _grid(lambda s: s["coll"] / s["runs"]); dv = _grid(lambda s: s["dv_mean"]); inj = _grid(lambda s: s["inj"])
    fig, axs = plt.subplots(1, 3, figsize=(10, 3.0))
    heat(axs[0], pc, "P(collision | HB)", lambda v: f"{v:.3f}" if v else "0")
    heat(axs[1], dv, "Mean Δv at contact [km/h]", lambda v: f"{v:.0f}" if v else "–")
    heat(axs[2], inj, "E[P(MAIS2+) | collision]", lambda v: f"{v:.3f}" if v else "–")
    axs[0].set_yticks(range(len(SPD)), SPD)
    for a in axs[1:]: a.set_yticks([])
    for a in axs: a.set_xlabel("follower headway")
    fig.tight_layout()
    return svg(fig)


def rfig_risk_share():
    def mat(col):
        M = np.zeros((len(TRIGGERS_N), len(HW_SHORT)))
        for r in range(6, 106):
            ti = [t[0] for t in ub_sim.TRIGGERS].index(scs[f"B{r}"].value); hj = [h[0] for h in ub_sim.HEADWAYS].index(scs[f"D{r}"].value)
            M[ti, hj] += scs[f"{col}{r}"].value
        return M / M.sum()
    fig, axs = plt.subplots(1, 2, figsize=(9.6, 3.0))
    heat(axs[0], mat("R"), "Share of point-estimate risk", lambda v: f"{v:.0%}" if v >= 0.005 else "·")
    heat(axs[1], mat("X"), "Share if λ were known (synthetic truth)", lambda v: f"{v:.0%}" if v >= 0.005 else "·")
    axs[0].set_yticks(range(5), TRIG_SHORT); axs[1].set_yticks([])
    for a in axs: a.set_xlabel("follower headway")
    fig.tight_layout()
    return svg(fig)


TRIGGERS_N = ub_sim.TRIGGERS


def rfig_is_vs_mc():
    mc = np.array([scs[f"N{r}"].value * scs[f"P{r}"].value for r in range(6, 106)])
    isv = np.array([scs[f"AB{r}"].value for r in range(6, 106)])
    floor = 1e-7
    fig, ax = plt.subplots(figsize=(6.2, 4.2))
    m = (mc > 0) & (isv > 0)
    ax.scatter(mc[m], isv[m], s=26, color=S1, edgecolor=SURF, lw=1, zorder=3, label="both > 0")
    z = (mc > 0) & (isv == 0)
    ax.scatter(mc[z], np.full(z.sum(), floor), s=26, marker="v", color=S2, zorder=3, label="IS saw no collision in its 10 runs")
    lim = [floor, 1]
    ax.plot(lim, lim, color=INK2, lw=1, ls="--"); ax.text(2e-3, 6e-3, "agreement", rotation=33, fontsize=9, color=INK2)
    ax.set_xscale("log"); ax.set_yscale("log"); ax.set_xlim(*lim); ax.set_ylim(floor / 2, 1)
    ax.set_xlabel("2,000-run plain MC: E[coll · P(MAIS2+)]"); ax.set_ylabel("10-run IS estimate")
    ax.set_title("Per-scenario agreement of 10 IS runs with 2,000 plain runs")
    ax.legend(fontsize=8.5, loc="upper left")
    return svg(fig), int(z.sum()), int(((mc == 0)).sum())


# =====================================================================================
# Outlook (06)
# =====================================================================================
def ofig_ess():
    d = np.arange(1, 81)
    fig, ax = plt.subplots(figsize=(7.2, 3.8))
    for delta, col in [(0.25, S3), (0.5, S1), (1.0, S2)]:
        ax.plot(d, np.exp(-d * delta ** 2), color=col, label=f"shift δ = {delta} σ per dimension")
    rng = np.random.default_rng(3)
    for dd in (5, 20, 40):
        x = rng.standard_normal((20000, dd)) + 0.5; lw = (-0.5 * x ** 2 + 0.5 * (x - 0.5) ** 2).sum(1); w = np.exp(lw - lw.max())
        ax.scatter([dd], [w.sum() ** 2 / (w ** 2).sum() / 20000], color=S1, s=30, zorder=3, edgecolor=SURF, lw=1.2)
    for xv, lab in [(3, "unintended braking\n(3 shifted)"), (15, "ACC (≈15)"), (60, "L4 robotaxi\n(≈50–100)")]:
        ax.axvline(xv, color=GRID, lw=6, zorder=0); ax.text(xv + 1, 1.5e-1 if xv < 50 else 4e-1, lab, fontsize=8.5)
    ax.set_yscale("log"); ax.set_ylim(1e-6, 1.5); ax.set_xlim(0, 80)
    ax.set_xlabel("Number of parameters the proposal shifts"); ax.set_ylabel("ESS / N")
    ax.set_title("Why fixed importance sampling breaks down in high dimension")
    ax.legend(fontsize=8.5, loc="lower left")
    return svg(fig)


READING = """
<h2 id="reading">References and further reading</h2>
<h3>Standards</h3>
<ul class="refs">
<li>ISO 21448:2022, <i>Road vehicles — Safety of the intended functionality</i>. Clauses 6, 9–13, Annex C.</li>
<li>ISO/TS 5083:2025, <i>Road vehicles — Safety for automated driving systems — Design, verification and validation</i>.</li>
<li>ISO 34502:2022, <i>Scenario based safety evaluation framework</i>; ISO 34504, <i>Scenario categorization</i>.</li>
<li>ISO 15622, <i>Adaptive cruise control systems — Performance requirements and test procedures</i>.</li>
<li>ANSI/UL 4600, <i>Standard for Safety for the Evaluation of Autonomous Products</i>, Ch. 16 (SPIs).</li>
</ul>
<h3>Papers and reports</h3>
<ul class="refs">
<li>Putze, Westhofen, Koopmann, Böde, Neurohr (2023). On Quantification for SOTIF Validation of Automated Driving Systems. <a href="https://arxiv.org/abs/2304.10170">arXiv:2304.10170</a>.</li>
<li>Betschinske et al. (2025). Towards more efficient quantitative safety validation of residual risk for assisted and automated driving. <a href="https://arxiv.org/abs/2506.10363">arXiv:2506.10363</a>.</li>
<li>Kalra, Paddock (2016). <i>Driving to Safety</i>. RAND RR-1478. <a href="https://www.rand.org/pubs/research_reports/RR1478.html">rand.org</a>.</li>
<li>Zhao et al. (2017). Accelerated evaluation of automated vehicles safety in lane-change scenarios based on importance sampling. <a href="https://arxiv.org/abs/1605.04965">arXiv:1605.04965</a>.</li>
<li>de Gelder (2022). <i>Safety assessment of automated vehicles using real-world driving scenarios</i>. PhD thesis, TU Delft.</li>
<li>Ratiu, Rohlinger, Stolte, Wagner (2024). Towards an Argument Pattern for the Use of Safety Performance Indicators. <a href="https://arxiv.org/abs/2410.00578">arXiv:2410.00578</a>.</li>
<li>Koopman. <i>SPI vs KPI</i>, CMU lecture notes. <a href="https://users.ece.cmu.edu/~koopman/lectures/L124_SPI_vs_KPI.pdf">PDF</a>.</li>
<li>Schaller et al. (2026). Addressing SOTIF with a runtime monitor ensemble for AI-based perception systems. <i>Discover AI</i> 6:1172. <a href="https://doi.org/10.1007/s44163-026-02186-z">doi</a>.</li>
<li>Reich (2026). <i>SINADRA: Situation-Aware Dynamic Risk Assessment for Safe and Permissive Autonomous Systems</i>. Dr.-Ing. thesis, RPTU Kaiserslautern-Landau.</li>
<li>Glasmacher, Weber, Eckstein (2024). Towards a Completeness Argumentation for Scenario Concepts. <a href="https://arxiv.org/abs/2404.01934">arXiv:2404.01934</a>.</li>
<li><i>Coverage Metrics for a Scenario Database for the Scenario-Based Assessment of Automated Driving Systems</i> (2024). <a href="https://arxiv.org/abs/2409.01139">arXiv:2409.01139</a>.</li>
<li>Guo, Muñoz Sánchez, de Gelder, van der Sande (2023). Scenario Extraction from a Large Real-World Dataset for the Assessment of Automated Vehicles. <a href="https://arxiv.org/abs/2306.07815">arXiv:2306.07815</a>.</li>
<li>Hauer, Schmidt, Holzmüller, Pretschner (2019). Did We Test All Scenarios for Automated and Autonomous Driving Systems? IEEE ITSC.</li>
<li>ASAM OpenLABEL 1.0.0 (2021). <a href="https://www.asam.net/standards/detail/openlabel/">asam.net</a>. ISO 34503:2023, <i>Specification for operational design domain</i>.</li>
<li>UNECE (2021). New Assessment/Test Method for Automated Driving (NATM), ECE/TRANS/WP.29/2021/61; Commission Implementing Regulation (EU) 2022/1426.</li>
<li>Au, Beck (2001). Estimation of small failure probabilities in high dimensions by subset simulation. <i>Probabilistic Engineering Mechanics</i> 16(4).</li>
</ul>
<h3>Statistics books for deeper understanding</h3>
<ul class="refs">
<li><b>Wasserman (2004).</b> <i>All of Statistics</i>. Springer. Compact, rigorous tour of inference, written for scientists and engineers. Start here.</li>
<li><b>Casella, Berger (2002).</b> <i>Statistical Inference</i>, 2nd ed. Duxbury. The standard text on estimators, confidence intervals and hypothesis tests (lessons 1–2).</li>
<li><b>Meeker, Hahn, Escobar (2017).</b> <i>Statistical Intervals: A Guide for Practitioners and Researchers</i>, 2nd ed. Wiley. Exact Poisson and binomial bounds, zero-failure demonstration tests.</li>
<li><b>Rausand, Barros, Høyland (2020).</b> <i>System Reliability Theory: Models, Statistical Methods, and Applications</i>, 3rd ed. Wiley. Failure rates, demonstration testing, Bayesian reliability.</li>
<li><b>Gelman et al. (2013).</b> <i>Bayesian Data Analysis</i>, 3rd ed. CRC. Priors, posteriors, hierarchical models. Free PDF on the <a href="https://sites.stat.columbia.edu/gelman/book">authors' page</a>.</li>
<li><b>Owen (2013).</b> <i>Monte Carlo theory, methods and examples</i>. Ch. 9–10: importance sampling, diagnostics, effective sample size. Chapters online at <a href="https://artowen.su.domains/mc/">artowen.su.domains/mc</a>.</li>
<li><b>Robert, Casella (2004).</b> <i>Monte Carlo Statistical Methods</i>, 2nd ed. Springer. Deeper theory of simulation-based estimation.</li>
<li><b>Rubinstein, Kroese (2016).</b> <i>Simulation and the Monte Carlo Method</i>, 3rd ed. Wiley. Rare events and the cross-entropy method for choosing proposals.</li>
<li><b>Nelsen (2006).</b> <i>An Introduction to Copulas</i>, 2nd ed. Springer. Sklar's theorem, Kendall's τ, tail dependence.</li>
<li><b>Joe (2014).</b> <i>Dependence Modeling with Copulas</i>. CRC. Vine copulas, fitting, high-dimensional dependence.</li>
<li><b>Coles (2001).</b> <i>An Introduction to Statistical Modeling of Extreme Values</i>. Springer. GPD tails and threshold choice for near-miss extrapolation.</li>
</ul>
"""


def report_body(fs, n_zero_is, n_zero_mc):
    tiles = "".join(f'<div class="tile"><div class="k">{k}</div><div class="v">{v}</div><div class="s">{s}</div></div>' for k, v, s in [
        ("Logical scenarios", "100", "5 triggers × 4 speeds × 5 headways"),
        ("Concrete scenarios", "1,000", f"{n_hits} collisions, median ESS {ess_med:.1f}/10"),
        ("Risk, point estimate", f"{R_point:.1e}/h", f"{R_point/budget:.2f}× budget"),
        ("Bayesian 95% bound", f"{R_bayes:.1e}/h", f"{R_bayes/budget:.2f}× budget: pass"),
        ("Bonferroni bound", f"{R_bonf:.1e}/h", f"{R_bonf/budget:.1f}× budget: fail"),
        ("Replay hours", f"{have_h_g:,.0f} h", f"Bonferroni needs ≈ {need_h_g:,.0f} h")])
    return f"""
<div class="callout"><b>Synthetic example.</b> Validation target: MAIS2+ injuries from rear-end collisions caused by unintended braking ≤ \\(A_H = 10^{{-7}}\\)/h, with 10% reserved for unknown triggers (budget \\(9\\times10^{{-8}}\\)/h). Source: <code>tools/unintended_braking_risk_example.xlsx</code>; method in <a href="01-scenario-based-risk.html">doc 1</a> and <a href="04-how-the-concrete-scenarios-were-generated.html">doc 4</a>.</div>
<div class="tiles">{tiles}</div>
<div class="math">\\[ R = \\sum_{{\\ell=1}}^{{100}} \\text{{share}}_\\ell\;\\lambda_{{HB}}(\\text{{trigger}},\\text{{speed}})\;E\\big[\\mathbb 1_{{\\text{{coll}}}}\\,P(\\text{{MAIS2+}}\\mid\\Delta v)\\big]_\\ell \\]</div>

<h2>1 · Verdict</h2>
{figure(fs['verdict'], "All four estimates against the known-scenario budget (green line). The point estimates carry no confidence. The Bayesian posterior quantile passes; the Bonferroni bound, which multiplies 120 simultaneous upper bounds, does not.", 1)}

<h2>2 · Exposure</h2>
{figure(fs['exposure'], "Operating-time shares per factor. Scenario share = product of the three (independence assumed). Clear road dominates exposure, and therefore dominates the evidence requirement.", 2)}

<h2>3 · How often unintended braking happens</h2>
{figure(fs['hb'], "Replay evidence per trigger × speed cell. Cells with zero events still have wide upper bounds; clear-road cells have the most hours but the lowest true rate, so their bound is what limits the claim.", 3)}

<h2>4 · What happens after an unintended brake</h2>
{figure(fs['coll'], "From 2,000 plain runs per logical scenario, averaged over trigger contexts. Collision probability is driven by headway. Low speeds give smaller gaps for the same time headway, hence more collisions, but lower Δv, hence lower injury probability.", 4)}

<h2>5 · Where the risk sits</h2>
{figure(fs['share'], "Left: attribution from observed HB counts. Right: attribution if the true rates were known. With 0–4 events per cell, point-estimate attribution is largely Poisson noise. Clear road gets almost nothing on the left only because no event was observed there.", 5)}

<h2>6 · What the evidence supports</h2>
{figure(fs['posterior'], "Posterior of total risk (Jeffreys priors) with the point estimate, the Bayesian 95% quantile, the budget and the Bonferroni bound.", 6)}

<h2>7 · Do 1,000 concrete scenarios suffice?</h2>
{figure(fs['ismc'], f"Each dot is one logical scenario. Where both are non-zero, the 10-run IS estimates scatter around the 2,000-run reference. {n_zero_is} scenarios saw no collision in their 10 IS runs although plain MC did; {n_zero_mc} have no collision in either. Total risk from IS: {R_is:.1e}/h vs. {R_point:.1e}/h ({R_is/R_point:.2f}×).", 7)}
{figure(fs['weights'], "Importance weights and effective sample size per logical scenario.", 8)}

<h2>8 · Sensitivity to the dependence assumption</h2>
{figure(fs['cop'], "Ignoring the Gaussian-copula dependence would change P(collision | HB) by this factor, cell by cell.", 9)}

<h2>9 · What it would take to pass rigorously</h2>
{figure(fs['targets'], "Replay hours per evidence cell: available vs. required for the Bonferroni claim under the square-root allocation.", 10)}
<ul>
<li><b>Fastest route:</b> defend the Bayesian argument (prior choice, sensitivity to priors), or pool the cells with a hierarchical model instead of 120 separate bounds.</li>
<li><b>Data route:</b> clear-road replay hours dominate the requirement.</li>
<li><b>Model route:</b> measure the copula. A factor of {rmin_g:.1f}–{rmax_g:.1f}× in P(collision) is larger than most other uncertainties here.</li>
</ul>
"""


def outlook_body(fess):
    return f"""
<p>The unintended-braking example has one hazardous behaviour, one harm, one other agent and seven parameters. Real functions have many of each. The estimator does not change. What changes is the scenario space, the interaction between agents, and the cost of exploring rare regions.</p>
<div class="math">\\[ R_s = \\sum_{{\\text{{HB}}}}\\ \\sum_{{\\ell}}\\ \\nu_\\ell \\int P(\\text{{HB}}\\mid\\theta,\\ell)\\,P(S\\ge s\\mid \\text{{HB}},\\theta,\\ell)\\,f_\\ell(\\theta)\\,d\\theta \\quad\\le\\quad A_s \\]</div>

<h2>1 · Three levels compared</h2>
<div class="tbl-wrap"><table class="doc"><thead><tr><th></th><th>Unintended braking (this example)</th><th>ACC / L2 longitudinal</th><th>L4 urban robotaxi</th></tr></thead><tbody>
<tr><td><b>Hazardous behaviours</b></td><td>1 (phantom brake)</td><td>≈5–10: phantom brake, late/weak braking, wrong target selection, unintended acceleration, failure to resume or stop</td><td>dozens across all DDT subtasks: perception misses/FPs, prediction errors, unsafe gap acceptance, wrong right-of-way, MRM failures</td></tr>
<tr><td><b>Harms / affected parties</b></td><td>rear-end, follower occupants</td><td>rear-end both directions; occupants of ego, lead and follower</td><td>all road users, by type (VRU, cyclist, car, heavy vehicle), each with its own injury model</td></tr>
<tr><td><b>Scenario types</b></td><td>1 (phantom brake with follower)</td><td>car following, lead braking, cut-in, cut-out revealing a stationary object, approach to a queue</td><td>hundreds: intersections, unprotected turns, occluded VRUs, pick-up/drop-off, emergency vehicles, construction, police direction</td></tr>
<tr><td><b>Parameters θ</b></td><td>7</td><td>≈10–20 (lead/cut-in kinematics, follower, road, friction, sensor conditions)</td><td>≈50–100+ (multi-agent trajectories, occlusion geometry, intent, weather, map context)</td></tr>
<tr><td><b>Agent interaction</b></td><td>open loop: follower reacts, ego doesn't</td><td>closed loop: ACC reacts to lead; driver as fallback</td><td>closed loop, many reactive agents; behaviour models are themselves uncertain</td></tr>
<tr><td><b>Controllability</b></td><td>other driver only</td><td>driver override (L2, ISO 15622 context)</td><td>none from occupants; MRM, remote assistance, other road users</td></tr>
<tr><td><b>Acceptance criterion</b></td><td>one \\(A_H\\)</td><td>per-HE criteria, often relative to the human-driver benchmark (Annex C)</td><td>positive risk balance vs. a human benchmark in the same ODD (ISO/TS 5083), split per harm type</td></tr>
</tbody></table></div>

<h2>2 · ACC: what to add</h2>
<ol class="tight">
<li><b>HB catalogue</b> from the SOTIF analysis, each with its triggering conditions (radar multipath under bridges, stationary-object filtering, curve target selection, cut-in detection latency).</li>
<li><b>Scenario types per HB</b>, as a partition of the ODD by manoeuvre (follow / cut-in / cut-out / approach) × road × speed band × traffic density.</li>
<li><b>Two-sided harm:</b> late braking risks hitting the lead; phantom braking risks being hit. Sum per harm, not per HB.</li>
<li><b>Driver in the loop:</b> \\(P(\\bar C\\mid E)\\) becomes a driver-response model (take-over time, brake force). It is also uncertain, and also needs a copula with the scenario parameters.</li>
<li><b>Parameters with dependence:</b> lead deceleration, time gap, relative speed and cut-in lateral speed are coupled. Fit them from naturalistic data (e.g. highD-type datasets, if the ODD matches).</li>
<li><b>Sampling:</b> about 15 dimensions. Fixed-proposal IS starts to lose efficiency (Figure 1); use cross-entropy to adapt the proposal.</li>
</ol>

<h2>3 · L4 robotaxi: what changes fundamentally</h2>
<ul>
<li><b>Scenario space is open.</b> The taxonomy will never be complete, so the unknown-scenario term \\(R_{{\\text{{unknown}}}}\\) and its SPIs (discovery rate, Good–Turing \\(n_1/N\\)) become a main part of the argument, not a footnote.</li>
<li><b>Closed-loop, multi-agent.</b> Outcomes depend on how other agents react to the robotaxi. Reactive agent models enter \\(P(\\text{{HB}}\\mid\\theta)\\) and must be validated themselves.</li>
<li><b>Perception error models are central.</b> Simulating raw sensors at fidelity is rarely credible, so P(HB) is computed from planner replays with injected, statistically modelled perception errors (by class, range, occlusion, weather).</li>
<li><b>High dimension.</b> Fixed importance sampling collapses (Figure 1). Use adaptive or sequential methods: cross-entropy, subset simulation (Au &amp; Beck 2001), and surrogate-guided search (Gaussian-process or learned failure-boundary models), always with a final unbiased estimate and ESS.</li>
<li><b>Acceptance criterion.</b> Positive risk balance per harm type against a human benchmark matched to the ODD (ISO/TS 5083), with the rules from lesson 1 still applied to each claim.</li>
<li><b>Runtime evidence.</b> Situation-aware risk monitors (Reich's SINADRA) and monitor ensembles (Schaller et al.) supply leading SPIs and runtime restrictions. They reduce \\(\\nu_\\ell\\) for risky situations, and that reduction must be argued in the same equation.</li>
</ul>
{figure(fess, "Effective sample size of importance sampling with a Gaussian proposal shifted by δ standard deviations in d dimensions: ESS/N = exp(−dδ²). Dots: simulation check (δ = 0.5). Shifting 3 parameters is harmless; shifting 15 costs most of the runs; shifting 60 is hopeless without adaptive proposals or dimension reduction.", 1)}
<div class="math">\\[ w = \\prod_{{i=1}}^d \\frac{{\\varphi(x_i)}}{{\\varphi(x_i-\\delta)}}, \\qquad E_q[w^2] = e^{{d\\delta^2}}, \\qquad \\frac{{\\text{{ESS}}}}{{N}} \\approx \\frac{{1}}{{E_q[w^2]}} = e^{{-d\\delta^2}} \\]</div>

<h2>4 · A staged roadmap</h2>
<ol class="tight">
<li><b>One HB, one harm</b> (this example): build the data pipeline, the evidence cells and the SPI loop end to end.</li>
<li><b>ACC:</b> several HBs and both rear-end directions; driver response model; fitted copulas; cross-entropy IS; per-harm aggregation.</li>
<li><b>L4 pilot ODD:</b> a geofenced, limited ODD with a few hundred scenario types; perception error models; reactive agents; unknown-scenario SPIs; runtime risk monitors.</li>
<li><b>L4 scale-out:</b> extend the ODD only where scenario coverage, exposure data and SPIs support it, re-running the risk sum per extension.</li>
</ol>
"""


# =====================================================================================
# Doc 07 — scenario database, ODD coverage, completeness
# =====================================================================================
def sfig_granularity():
    rng = np.random.default_rng(41); s = (35, 55); n = 120000
    th = ub_sim.sample_theta(s, (0.5, 3.5), n, rng, corr=False)
    hit, _ = ub_sim.simulate(th)
    edges = np.arange(0.5, 3.55, 0.1); idx = np.digitize(th["h"], edges) - 1
    p = np.array([hit[idx == i].mean() for i in range(len(edges) - 1)]); mid = (edges[:-1] + edges[1:]) / 2
    fig, ax = plt.subplots(figsize=(7.2, 3.8))
    ax.plot(mid, p, color=S1, marker="o", ms=3.5, label="fine bins (0.1 s)")
    classes = [(0.5, 1.0), (1.0, 1.5), (1.5, 2.0), (2.0, 3.0), (3.0, 3.5)]
    for lo, hi in classes:
        m = (th["h"] >= lo) & (th["h"] < hi); pc = hit[m].mean()
        ax.plot([lo, hi], [pc, pc], color=S2, lw=2.5)
        ax.axvline(lo, color=GRID, lw=1, zorder=0)
        rng_in = p[(mid >= lo) & (mid < hi)]
        if len(rng_in) and rng_in.max() > 0.01:
            ax.annotate(f"range {rng_in.min():.2f}–{rng_in.max():.2f}", ((lo + hi) / 2, rng_in.max()), (0, 8), textcoords="offset points", ha="center", fontsize=8.5)
    ax.plot([], [], color=S2, lw=2.5, label="current class averages")
    ax.set_xlabel("Follower time headway h [s]"); ax.set_ylabel("P(collision | HB)")
    ax.set_title("Granularity: within-class variation is largest at short headway (35–55 km/h)")
    ax.legend(fontsize=9)
    return svg(fig)


def sfig_tagger():
    rng = np.random.default_rng(42)
    true_lat = rng.lognormal(np.log(0.55), 0.45, 1500)                  # peak lateral speed of real cut-ins [m/s]
    wobble = np.abs(rng.normal(0, 0.18, 8000))                          # lane-keeping wobble / tracking noise of non-cut-ins
    meas_t, meas_f = true_lat + rng.normal(0, 0.08, true_lat.size), wobble + rng.normal(0, 0.08, wobble.size)
    th = np.linspace(0.05, 1.0, 200)
    rec = np.array([(meas_t > t).mean() for t in th])
    tp = np.array([(meas_t > t).sum() for t in th]); fp = np.array([(meas_f > t).sum() for t in th])
    prec = tp / np.maximum(tp + fp, 1)
    fig, ax = plt.subplots(figsize=(7.2, 3.6))
    ax.plot(th, rec, color=S1, label="recall (share of real cut-ins found)")
    ax.plot(th, prec, color=S2, label="precision (share of detections that are real)")
    t0 = 0.35; r0 = (meas_t > t0).mean(); p0 = (meas_t > t0).sum() / ((meas_t > t0).sum() + (meas_f > t0).sum())
    ax.axvline(t0, color=INK2, lw=1, ls=":"); ax.text(t0 + 0.01, 0.12, f"threshold 0.35 m/s:\nrecall {r0:.2f}, precision {p0:.2f}", fontsize=9)
    ax.set_ylim(0, 1.03); ax.set_xlabel("Tagger threshold on peak lateral speed [m/s]"); ax.set_ylabel("rate")
    ax.set_title("A scenario tagger is a classifier: its errors bias exposure")
    ax.legend(fontsize=9, loc="center right")
    return svg(fig), r0, p0


def sfig_pair_coverage():
    rng = np.random.default_rng(43)
    weather = ["dry", "light rain", "heavy rain", "fog", "snow", "low sun"]
    road = ["residential", "urban arterial", "intersection", "roundabout", "bus lane", "construction zone", "tunnel"]
    pw = np.array([0.62, 0.17, 0.06, 0.03, 0.02, 0.10]); pr = np.array([0.30, 0.30, 0.20, 0.06, 0.05, 0.04, 0.05])
    hours = rng.poisson(np.outer(pw, pr) * 3000)                        # synthetic: 3,000 h of tagged exposure
    n = 30
    fig, ax = plt.subplots(figsize=(7.6, 3.6))
    im = ax.imshow(np.minimum(hours, n) / n, cmap="Blues", vmin=0, vmax=1, aspect="auto")
    for i in range(len(weather)):
        for j in range(len(road)):
            ax.text(j, i, f"{hours[i, j]}", ha="center", va="center", fontsize=9, color="white" if hours[i, j] >= n * 0.7 else INK)
    ax.set_xticks(range(len(road)), road, rotation=25, ha="right", fontsize=8.5); ax.set_yticks(range(len(weather)), weather)
    ax.grid(False)
    cov = (np.minimum(hours, n).sum()) / (n * hours.size)
    ax.set_title(f"Pairwise ODD-tag coverage: hours per cell, saturating at n = {n} (CoverageTag = {cov:.2f})")
    fig.colorbar(im, ax=ax, fraction=0.03, pad=0.02, label="min(hours, n) / n").outline.set_visible(False)
    return svg(fig), cov, int((hours < n).sum()), hours.size


def sfig_saturation():
    rng = np.random.default_rng(44); S_true = 1000
    probs = 1 / np.arange(1, S_true + 1) ** 1.8; probs /= probs.sum()
    N = 200_000; draws = rng.choice(S_true, size=N, p=probs)
    checkpoints = np.unique(np.logspace(2, np.log10(N), 40).astype(int))
    Sobs, chao, gt, true_miss = [], [], [], []
    for c in checkpoints:
        cnt = np.bincount(draws[:c], minlength=S_true); f1 = (cnt == 1).sum(); f2 = (cnt == 2).sum()
        Sobs.append((cnt > 0).sum()); chao.append((cnt > 0).sum() + (f1 * (f1 - 1) / (2 * (f2 + 1))))
        gt.append(f1 / c); true_miss.append(probs[cnt == 0].sum())
    fig, axs = plt.subplots(1, 2, figsize=(9.6, 3.5))
    axs[0].plot(checkpoints, Sobs, color=S1, label="scenario types observed")
    axs[0].plot(checkpoints, chao, color=S2, ls="--", label="Chao1 estimate of total")
    axs[0].axhline(S_true, color=INK2, lw=1, ls=":"); axs[0].text(120, S_true * 1.03, f"true number of types: {S_true} (synthetic)", fontsize=8.5)
    axs[0].set_xscale("log"); axs[0].set_xlabel("scenario occurrences recorded"); axs[0].set_ylabel("types"); axs[0].set_title("Discovery curve")
    axs[0].legend(fontsize=8.5, loc="lower right")
    axs[1].plot(checkpoints, gt, color=S2, label="Good–Turing estimate f₁/N")
    axs[1].plot(checkpoints, true_miss, color=INK2, ls=":", label="true missing mass (synthetic)")
    axs[1].set_xscale("log"); axs[1].set_yscale("log"); axs[1].set_xlabel("scenario occurrences recorded")
    axs[1].set_ylabel("P(next occurrence is a new type)"); axs[1].set_title("Missing probability mass")
    axs[1].legend(fontsize=8.5)
    fig.tight_layout()
    return svg(fig), Sobs[-1], chao[-1], gt[-1], true_miss[-1]


def scenario_db_body(fg, ft, fp, fs):
    gran, (tag_svg, r0, p0), (pair_svg, cov, n_under, n_cells), (sat_svg, sobs, chao, gtm, tmiss) = fg, ft, fp, fs
    return f"""
<p>How to validate an L4 system for SOTIF at vehicle level, what a scenario database contributes, how recordings feed it, how scenarios are identified automatically, how fine the ODD tags must be, and how to argue completeness. Plots use synthetic data.</p>

<h2>1 · The vehicle-level V&amp;V strategy for L4</h2>
<p>Terminology: ISO 21448 reserves “vehicle-level SOTIF strategy” (VLSS) for a set of vehicle-level <i>requirements</i>, verified according to the Clause 9 V&amp;V strategy (3.34, p. 10; D.1, p. 159). What follows is that Clause 9 strategy. ISO 21448 divides scenarios into known not hazardous (area 1), known hazardous (2), unknown hazardous (3) and unknown not hazardous (4) areas (4.2.2, pp. 12–14). Validation shows that the known-unsafe and unknown-unsafe areas carry acceptable residual risk. For L4, complement it with ISO/TS 5083 (ADS level; positive risk balance is already a rationale in ISO 21448 6.5, p. 30), UL 4600 (SPIs, safety case) and, for EU type approval, the UNECE NATM pillars (audit, simulation, track, real world, in-service monitoring; ECE/TRANS/WP.29/2021/61, Regulation (EU) 2022/1426).</p>
<div class="tbl-wrap"><table class="doc"><thead><tr><th>Pillar</th><th>SOTIF</th><th>What it shows</th><th>Feeds</th></tr></thead><tbody>
<tr><td>ODD spec, HARA, triggering-condition analysis</td><td>Cl. 5–7</td><td>what can go wrong, where</td><td>\\(A_s\\), HB/HE list, taxonomy</td></tr>
<tr><td>Component V&amp;V (perception KPIs per ODD stratum, planner checks)</td><td>Cl. 10</td><td>component insufficiencies</td><td>perception error models</td></tr>
<tr><td><b>Scenario-based simulation</b> from the database (falsification + IS estimation)</td><td>Cl. 10</td><td>risk in known scenarios</td><td>\\(p_\\ell\\), coverage</td></tr>
<tr><td>Log replay / XiL</td><td>Cl. 10</td><td>real inputs, current software</td><td>\\(\\lambda\\) per context</td></tr>
<tr><td>Proving ground</td><td>Cl. 10</td><td>sim anchoring at extremes</td><td>sim-to-real bounds</td></tr>
<tr><td><b>Public-road exploration and FOT</b></td><td>Cl. 11</td><td>unknown triggers, exposure</td><td>\\(\\nu,\\ f(\\theta),\\ R_{{\\text{{unknown}}}}\\)</td></tr>
<tr><td>Shadow mode / operation</td><td>Cl. 13</td><td>assumptions still hold</td><td>SPIs</td></tr>
<tr><td>Release argument</td><td>Cl. 12</td><td>claim per harm</td><td>\\(\\sum_\\ell \\nu_\\ell^U p_\\ell^U + R_{{\\text{{unknown}}}}^U \\le A_s\\)</td></tr>
</tbody></table></div>

<h2>2 · What the scenario database contributes</h2>
<ol class="tight">
<li><b>Makes “known” explicit.</b> The taxonomy is the boundary between known and unknown, and logical scenarios must partition the ODD.</li>
<li><b>Holds the weights:</b> \\(\\nu_\\ell\\) and \\(f_\\ell(\\theta)\\) from recordings.</li>
<li><b>Generates tests</b> (logical → concrete, e.g. OpenSCENARIO) with traceability triggering condition → HB → HE → requirement → test.</li>
<li><b>Shows coverage:</b> which cells (scenario × triggering condition × software version) have evidence.</li>
<li><b>Stores every run</b> with \\(\\theta\\), \\(q(\\theta)\\), software hash and outcome, so the risk can be recomputed after each change.</li>
<li><b>Moves unknown to known</b>: newly discovered types become categories, and their arrival rate is a Clause 11 SPI.</li>
</ol>
<pre class="flow">Recording(id, vehicle, sw_hash, map_ver, calib_state, route, hours, raw_uri)
ExposureSlice(recording_id, t0, t1, odd_tags…)              -- denominators, incl. “nothing happened”
ScenarioCategory(id, version, tag_rule, param_schema, partition_key)
Occurrence(id, recording_id, t0, t1, category_id, θ…, odd_tags, min_ttc, hb_flag, monitor_flags)
HazardLink(category_id, hb_id, he_id, triggering_condition_id)
TestRun(id, category_id, θ…, q_density, platform, sw_hash, outcome, Δv)</pre>

<h2>3 · From recordings to the database</h2>
<pre class="flow">raw logs ─► reference world model ─► context enrichment ─► tagging ─► scenario extraction ─► DB
(sensors,    (offline perception     (map matching,        (actor      (tag combinations      (Occurrence +
 bus, system  + labels; NOT the       weather, light,       activities, → category; θ at        ExposureSlice,
 internals)   online stack)           ODD tags per t)       relations)   anchor events)         log pointer)</pre>
<ul>
<li><b>Extract scenarios with a reference world model.</b> If the stack under test decides which scenarios exist, it cannot miss its own failures.</li>
<li><b>Tag every driven second</b>, even when no scenario happens. Otherwise \\(\\nu\\) has no denominator.</li>
<li><b>Provenance</b> (software hash, map, calibration) and a pointer back to the raw log window on every occurrence.</li>
<li><b>Version the taxonomy</b> and re-tag historical data when it changes.</li>
</ul>

<h2>4 · Identifying scenarios automatically</h2>
<p><b>Known types: tag-based extraction.</b> Tag each actor's activities (braking, lane change, turning) and relations (lead vehicle, cut-in, crossing). A category is a tag combination, and \\(\\theta\\) is read at an anchor event, e.g. lane crossing for a cut-in (Guo, Muñoz Sánchez, de Gelder, van der Sande 2023, on the Waymo Open Motion Dataset). The tagger is a classifier, so validate it against a human-labelled sample and correct the exposure:</p>
<div class="math">\\[ \\hat\\nu_\\ell = \\frac{{n_{{\\text{{detected}}}}\\cdot \\text{{precision}}}}{{\\text{{recall}}\\cdot T}} \\]</div>
{figure(tag_svg, f"Synthetic cut-in tagger thresholding the peak lateral speed. At 0.35 m/s it finds {r0:.0%} of real cut-ins, and {p0:.0%} of its detections are real. Uncorrected, exposure would be biased by the factor precision/recall. Measure both per ODD stratum, because rain and night change them.", 1)}
<p><b>New types: Clause 11 discovery.</b> (1) A queue of <i>unexplained critical events</i> (low TTC, hard braking, HB flags, monitor flags, disengagements, remote assistance) that match no category goes to human review. (2) Unsupervised clustering of time-window embeddings, with outliers far from all known clusters flagged. (3) ODD novelty: conditions outside the spec, or rare tag combinations.</p>

<h2>5 · ODD tags: coverage and granularity</h2>
<p>ISO 34503 gives the ODD taxonomy (scenery, environmental conditions, dynamic elements). ISO 34504 gives scenario-categorisation tags. Both are a <b>shared vocabulary, not a sufficient resolution</b>: ISO 34504 offers examples rather than prescribed values, and does not fix thresholds such as what “moving faster” means. Two things must be added for your function.</p>
<h3>Missing tags</h3>
<p>Risk-relevant attributes for <i>your</i> triggering conditions are often not standard tags: overhead structures, road spray and low-sun angle for phantom braking, for example. Derive extra tags from the Clause 7 triggering-condition analysis, from SINADRA-style structured environment models (guide phrases over an environment ontology identify the factors that change a hazardous situation's risk; Reich 2026), and from unexplained field events. Map each custom tag to a parent in ISO 34503/34504 so the vocabulary stays exchangeable.</p>
<h3>Granularity: how fine is fine enough?</h3>
<p>A class may lump values together as long as a shift of the distribution <i>within</i> the class cannot move the risk materially. With conditional harm \\(p(\\theta)\\), class exposure \\(\\nu_c\\), and test vs. deployment distributions inside the class:</p>
<div class="math">\\[ \\big|\\Delta R_c\\big| = \\nu_c\\left|\\int_c p(\\theta)\\,\\big(f^{{\\text{{dep}}}}_c - f^{{\\text{{test}}}}_c\\big)\\,d\\theta\\right| \;\\le\; \\nu_c\\,\\big(p^{{\\max}}_c - p^{{\\min}}_c\\big)\\,\\mathrm{{TV}}\\big(f^{{\\text{{dep}}}}_c, f^{{\\text{{test}}}}_c\\big) \\]</div>
<p>Refine a class until \\(\\sum_c \\nu_c\\,(p^{{\\max}}_c-p^{{\\min}}_c)\\,\\mathrm{{TV}}^{{\\max}}_c \\le \\delta\\), a reserved share of the budget. The rule refines where harm varies steeply <i>and</i> exposure is high. Boundaries must also be measurable in logs and at runtime, otherwise the class cannot be tagged or monitored.</p>
{figure(gran, "P(collision | HB) on a fine 0.1 s grid against the current headway classes. In the shortest class the collision probability varies several-fold, so a shift towards 0.5–0.7 s inside it would go unnoticed at class level. That is the class to split. The 2–3 s class is flat and can stay coarse.", 2)}
<h3>Combinatorial coverage</h3>
<p>Coverage of single tags is not enough; triggering conditions are often <i>combinations</i>. Count evidence per tag pair (or t-wise) and saturate at a minimum \\(n\\) (tag-based coverage, <i>Coverage Metrics for a Scenario Database…</i>, arXiv:2409.01139):</p>
<div class="math">\\[ \\text{{Coverage}}_{{\\text{{tag}}}}(n) = \\frac{{1}}{{n\\,|L|\\,|C|}}\\sum_{{L}}\\sum_{{C}} \\min\\big(n, N(L,C)\\big) \\]</div>
{figure(pair_svg, f"Synthetic exposure hours per weather × road-type pair. {n_under} of {n_cells} pairs have fewer than 30 h. Single-tag coverage looks fine, but heavy rain at roundabouts or fog in tunnels is barely tested. Use this to plan routes and the simulation focus.", 3)}

<h2>6 · Arguing completeness</h2>
<p>Completeness of a scenario concept cannot be proven; it is <i>argued</i>, typically in GSN, by refuting counter-hypotheses with evidence (Glasmacher, Weber, Eckstein 2024). Completeness is binary and applies to the concept; coverage is quantitative and applies to parameter spaces and value assignments. As they put it, <i>“unforeseen scenarios cannot be identified with argumentation, but with external input”</i>. Use five legs:</p>
<ol class="tight">
<li><b>By construction:</b> taxonomy derived systematically (ISO 34503 attributes × guidewords, SEM, triggering-condition analysis), reviewed by independent experts; atomicity of base scenarios.</li>
<li><b>Explained time (Type II coverage):</b> the share of driven time assigned to some category. Glasmacher et al. report no unassigned seconds at base-scenario level on inD. Every unassigned second is a candidate unknown.</li>
<li><b>Saturation:</b> the discovery curve flattens, and the estimated missing mass is small.</li>
<li><b>Risk-weighted remainder:</b> what matters is not the number of missing types but their risk. Bound it with the Clause 11 field evidence (lesson 1) inside the reserve \\(\\varepsilon A_H\\).</li>
<li><b>Kept open in operation</b> (Cl. 13): discovery rate, unexplained-event rate and tagger recall as SPIs, since completeness claims expire.</li>
</ol>
<div class="math">\\[ \\hat M_0 = \\frac{{f_1}}{{N}}\\ \\ (\\text{{Good–Turing}}), \\qquad \\hat S = S_{{\\text{{obs}}}} + \\frac{{f_1(f_1-1)}}{{2(f_2+1)}}\\ \\ (\\text{{Chao1}}), \\qquad R_{{\\text{{unknown}}}} \\lesssim \\hat M_0\\,\\nu_{{\\text{{tot}}}}\\,\\bar p_{{\\text{{unk}}}} \\]</div>
<p>\\(f_1, f_2\\): number of types seen exactly once or twice; \\(N\\): occurrences; \\(\\nu_{{\\text{{tot}}}}\\): total scenario occurrence rate; \\(\\bar p_{{\\text{{unk}}}}\\): harm per unknown occurrence, bounded conservatively or by field driving. Hauer et al. (2019) frame the same question as “did we test all scenario types?”.</p>
{figure(sat_svg, f"Synthetic: 1,000 scenario types with a long-tailed (Zipf, exponent 1.8) frequency distribution. After 200,000 occurrences, {sobs:.0f} types are seen and Chao1 estimates {chao:.0f}, a lower bound on the true 1,000; the Good–Turing missing mass is {gtm:.1e} (true: {tmiss:.1e}). The rare tail is reached last, and rare is also where triggering conditions hide. That is why saturation is one leg, not the whole argument.", 4)}

<h2>7 · OpenLABEL vs. ISO 34504 tags</h2>
<div class="tbl-wrap"><table class="doc"><thead><tr><th></th><th>ASAM OpenLABEL (v1.0.0, 2021)</th><th>ISO 34504:2024</th></tr></thead><tbody>
<tr><td><b>What it is</b></td><td>A <b>data format</b>: JSON schema for annotations</td><td>A <b>vocabulary and structure</b> for categorising scenarios</td></tr>
<tr><td><b>Answers</b></td><td>How do I store and exchange labels on recordings?</td><td>What do I call a scenario and its attributes?</td></tr>
<tr><td><b>Level</b></td><td>Frame and object level (boxes, segmentation, tracks) <i>and</i> scenario level</td><td>Scenario level only</td></tr>
<tr><td><b>Content</b></td><td>Elements (objects, actions, events, contexts, relations) with frame intervals; relations as subject–predicate–object; streams; coordinate systems; links to external ontologies</td><td>Tags for scenery, environment, dynamic elements and behaviour, grouped into categories; examples, no exact values</td></tr>
<tr><td><b>Semantics</b></td><td>Brings none of its own: each element points to an ontology entry you choose</td><td>Is a semantic source you can point to</td></tr>
<tr><td><b>Role in the pipeline</b></td><td>The container that carries tags with time intervals on recordings and links scenario files</td><td>The agreed names inside that container</td></tr>
</tbody></table></div>
<p>They complement each other: ISO 34503/34504 (plus your custom tags) form the ontology; OpenLABEL stores the per-recording, per-interval annotations that reference it; the scenario database indexes them; OpenSCENARIO describes executable tests. The OpenLABEL concept paper lists BSI PAS 1883 and ASAM OpenODD as related standards. The mapping to ISO 34504 is yours to define.</p>
<p class="meta">Sources for this page: Glasmacher, Weber, Eckstein 2024 (arXiv:2404.01934); <i>Coverage Metrics for a Scenario Database for the Scenario-Based Assessment of ADS</i> (arXiv:2409.01139); Guo et al. 2023 (arXiv:2306.07815); ASAM OpenLABEL concept paper and standard page; TNO on ISO 34504 (2024); ISO 34503:2023; Reich 2026 (SINADRA).</p>
"""

# =====================================================================================
# HTML
# =====================================================================================
FONTS = "https://fonts.googleapis.com/css2?family=Source+Serif+4:ital,opsz,wght@0,8..60,400;0,8..60,600;1,8..60,400&family=IBM+Plex+Sans+Condensed:wght@500;600&family=JetBrains+Mono:wght@400;600&display=swap"
PAGES = [("01-scenario-based-risk.html", "Scenario-based residual risk"),
         ("02-field-data-and-spis.html", "Field data and SPIs"),
         ("03-gaussian-copula.html", "Gaussian copula"),
         ("04-how-the-concrete-scenarios-were-generated.html", "How the 1,000 scenarios were generated"),
         ("05-unintended-braking-report.html", "Unintended braking report"),
         ("06-scaling-to-acc-and-robotaxi.html", "Scaling up: ACC and L4 robotaxi"),
         ("07-scenario-database-and-completeness.html", "Scenario database, ODD coverage and completeness")]
EXTRA_CSS = """
.page{max-width:1060px}.col{max-width:46rem}
figure.plot{margin:1.6rem 0 2rem;background:#fcfcfb;border:1px solid var(--rule);border-radius:4px;padding:.8rem .8rem .6rem;color:#0b0b0b}
figure.plot .plot-svg{overflow-x:auto}figure.plot svg{max-width:100%;height:auto;display:block}
figure.plot figcaption{font-size:var(--step--1);line-height:1.5;color:#52514e;margin-top:.5rem}
.math{overflow-x:auto;margin:.6rem 0 1.1rem}
table.doc{min-width:100%}table.doc td{font-family:var(--serif);text-align:left;vertical-align:top}table.doc th{text-align:left}
.toc{display:flex;flex-wrap:wrap;gap:.4rem 1.2rem;font:500 var(--step--1) var(--label);margin:.4rem 0 1.4rem}
.toc a[aria-current]{color:var(--ink);text-decoration:none;font-weight:600}
code{overflow-wrap:anywhere}mjx-container[display="true"]{overflow-x:auto;overflow-y:hidden;max-width:100%}
.callout{border-left:3px solid var(--accent);padding:.2rem 0 .2rem 1rem;margin:1.2rem 0}
.tiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(13rem,1fr));gap:.6rem;margin:1rem 0 1.4rem}
.tile{border:1px solid var(--rule);border-radius:4px;padding:.6rem .8rem;background:var(--panel)}
.tile .k{font:500 var(--step--1)/1.2 var(--label);color:var(--ink-soft)}.tile .v{font:600 1.3rem/1.3 var(--mono);font-variant-numeric:tabular-nums}
.tile .s{font-size:var(--step--1);color:var(--ink-soft)}
ul.refs li{margin-bottom:.35rem;font-size:var(--step--1)}
pre.flow{font:400 .85rem/1.5 var(--mono);background:var(--panel);padding:.9rem 1rem;overflow-x:auto;border-radius:3px}
"""


def page(fname, title, dek, body):
    toc = "".join(f'<a href="{f}"{" aria-current=page" if f == fname else ""}>{i+1}. {t}</a>' for i, (f, t) in enumerate(PAGES))
    idx = [p[0] for p in PAGES].index(fname)
    prev_ = f'<a href="{PAGES[idx-1][0]}">← {PAGES[idx-1][1]}</a>' if idx > 0 else '<a href="../index.html">← Course overview</a>'
    next_ = f'<a href="{PAGES[idx+1][0]}">{PAGES[idx+1][1]} →</a>' if idx < len(PAGES) - 1 else '<a href="../index.html">Course overview →</a>'
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="claude:viewport-fit-sides" content="cover">
<title>{title}</title>
<link rel="stylesheet" href="{FONTS}">
<link rel="stylesheet" href="../assets/course.css">
<style>{EXTRA_CSS}</style>
<script>window.MathJax={{tex:{{inlineMath:[['\\\\(','\\\\)']],displayMath:[['\\\\[','\\\\]']]}},svg:{{fontCache:'global'}}}};</script>
<script defer src="https://cdn.jsdelivr.net/npm/mathjax@3.2.2/es5/tex-svg.js"></script>
</head><body><main class="page"><div class="col">
<nav class="crumbs" aria-label="Course"><a href="../index.html">SOTIF Risk Course</a><span>{"Report" if idx == 4 else ("Outlook" if idx == 5 else f"Doc {idx+1} of {len(PAGES)}")}</span></nav>
<h1>{title}</h1>
<p class="dek">{dek}</p>
<nav class="toc" aria-label="Docs">{toc}</nav>
{body}
{READING}
<p class="ask">Questions, objections or a case from your own HARA? Ask in the chat.</p>
<nav class="nav" aria-label="Doc navigation">{prev_}{next_}</nav>
</div></main></body></html>"""


def main():
    os.makedirs(DOCS, exist_ok=True)
    print("figures 01…")
    f1, crit_frac, p_true = fig_toy_cutin()
    f2, ref = fig_convergence()
    f3, top10 = fig_pareto()
    f4 = fig_posterior()
    f5, have_h, need_h = fig_evidence_targets()
    print("figures 02…")
    f6 = fig_rate_bound(); f7, mu = fig_detect(); f8 = fig_evt()
    print("figures 03…")
    f9 = fig_marginals(); f10 = fig_copula_scatter(); f11, tails = fig_tail(); f12, rmin, rmax = fig_copula_heat()
    print("figures 04…")
    f13 = fig_trajectories(); f14 = fig_weights(); f15 = fig_concrete_scatter()
    print("report + outlook…")
    global have_h_g, need_h_g, rmin_g, rmax_g
    have_h_g, need_h_g, rmin_g, rmax_g = have_h, need_h, rmin, rmax
    ismc, nz_is, nz_mc = rfig_is_vs_mc()
    fs = dict(verdict=rfig_verdict(), exposure=rfig_exposure(), hb=rfig_hb(), coll=rfig_coll_inj(), share=rfig_risk_share(),
              posterior=f4, ismc=ismc, weights=f14, cop=f12, targets=f5)
    b5 = report_body(fs, nz_is, nz_mc)
    b6 = outlook_body(ofig_ess())
    print("doc 07…")
    b7 = scenario_db_body(sfig_granularity(), sfig_tagger(), sfig_pair_coverage(), sfig_saturation())

    # ------------------------------------------------------------------ 01
    b1 = f"""
<p>How to turn the evaluation of many scenarios, critical and non-critical, into a residual-risk number, and how that number relates to validation targets. Worked example: <code>tools/unintended_braking_risk_example.xlsx</code> (synthetic data).</p>

<h2>1 · Direction of the calculation</h2>
<p>A HARA is built system-outward: hazardous behaviour (HB) → hazardous event (HE) → scenarios. Probability flows the other way. <strong>The world produces situations at some rate; the system responds with an HB or not.</strong> For computing risk the scenario is the random variable, and the HB is an outcome conditioned on it.</p>
<ul>
<li>Store the mapping as <em>scenario → {{possible HB, HE}}</em>, not HE → scenarios.</li>
<li>Logical scenarios must <strong>partition the ODD</strong>: mutually exclusive and exhaustive. Overlap double-counts exposure, and then only the conservative Bonferroni bound holds (Putze et al. 2023, Eq. 2):
<div class="math">\\[ P(H) \\le \\sum_{{T,B,E}} P(T)\\,P(B\\mid T)\\,P(E\\mid B,T)\\,P(H\\mid E,B,T) \\]</div></li>
<li>Large combinatorial counts are usually products of ODD factors. Those factors belong in the parameter vector \\(\\theta\\), not in separate logical scenarios.</li>
</ul>

<h2>2 · The estimator</h2>
<p>For severity class \\(s\\), summed over logical scenarios \\(\\ell\\):</p>
<div class="math">\\[ R_s = \\sum_\\ell \\nu_\\ell\\, p_{{\\ell,s}}, \\qquad p_{{\\ell,s}} = \\int P(HB\\mid\\theta,\\ell)\\; P(S\\ge s\\mid HB,\\theta,\\ell)\\; f_\\ell(\\theta)\\,d\\theta \\]</div>
<div class="tbl-wrap"><table class="doc"><thead><tr><th>Symbol</th><th>Meaning</th><th>Source</th></tr></thead><tbody>
<tr><td>\\(\\nu_\\ell\\)</td><td>exposure: occurrences or time share of scenario \\(\\ell\\) per operating hour</td><td>field data</td></tr>
<tr><td>\\(f_\\ell(\\theta)\\)</td><td>joint distribution of the concrete parameters (marginals + copula)</td><td>field data</td></tr>
<tr><td>\\(P(HB\\mid\\theta)\\)</td><td>system response</td><td>simulation, anchored by proving ground</td></tr>
<tr><td>\\(P(S\\mid HB,\\theta)\\)</td><td>collision kinematics → injury risk curve</td><td>simulation + accident data</td></tr>
</tbody></table></div>
<p>From \\(N\\) concrete runs drawn from a test distribution \\(q_\\ell\\):</p>
<div class="math">\\[ \\hat p_{{\\ell,s}} = \\frac1N\\sum_{{i=1}}^{{N}} w_i\\,h_i, \\qquad w_i = \\frac{{f_\\ell(\\theta_i)}}{{q_\\ell(\\theta_i)}}, \\qquad c_\\ell = \\frac{{\\nu_\\ell\\,\\hat p_{{\\ell,s}}}}{{R_s}} \\]</div>
<p>\\(h_i\\) is the run outcome: 0/1 harm, or \\(P(S\\ge s\\mid\\Delta v_i)\\). \\(c_\\ell\\) is the scenario's share of the risk.</p>

<h3>Counting critical runs is not a risk estimate</h3>
{figure(f1, f"Toy cut-in. A uniform grid design puts {crit_frac:.1%} of its runs in the failure region, but the real-world probability of failure per cut-in is {p_true:.1e}, about 1,000× smaller. Only the weights \\(w_i\\) connect test runs to the real world. Non-critical runs are evidence too: they are the bulk of the sum.", 1)}
<p>Falsification and criticality search find <em>triggering conditions</em> (Clause 10 → Clause 8). They do not estimate risk unless you can write down the distribution \\(q\\) they sampled from. Keep the two campaigns separate.</p>

<h3>Importance sampling</h3>
{figure(f2, f"Plain Monte Carlo needs thousands of runs before its first collision; importance sampling from a proposal \\(q\\) that over-samples critical conditions converges much earlier and stays unbiased. Report the effective sample size \\((\\sum w)^2/\\sum w^2\\) with every IS estimate. In the full example, 1,000 IS runs reproduce the 200,000-run plain estimate to a factor of {R_is/R_point:.2f}.", 2)}

<h3>Relation to Annex C</h3>
<p>ISO 21448 Annex C.2 writes \\(A_H = R_{{HB}}\\cdot P(E\\mid HB)\\cdot P(\\bar C\\mid E)\\cdot P(S\\mid\\bar C)\\). Those factors are the scenario averages of the integral above. The scenario approach keeps the \\(\\theta\\)-dependence that Annex C averages away. That makes it more efficient, and also more demanding of data.</p>

<h2>3 · Relation to validation targets</h2>
<p>The field-only approach has one target, \\(\\tau = -\\ln(1-C)/R_{{HB}}\\) (lesson 1). The scenario approach replaces it with one claim and several evidence targets:</p>
<div class="math">\\[ \\sum_\\ell \\nu_\\ell^{{U}}\\, p_{{\\ell,s}}^{{U}} \\;+\\; R_{{\\text{{unknown}}}}^{{U}} \\;\\le\\; A_s \\quad\\text{{at confidence }}C, \\qquad \\sum_i (1-C_i) \\le 1-C \\]</div>
<div class="tbl-wrap"><table class="doc"><thead><tr><th>Term</th><th>Validation target</th><th>Measured in</th></tr></thead><tbody>
<tr><td>\\(\\nu_\\ell^U\\)</td><td>enough naturalistic data per scenario class (Poisson bound on counts)</td><td>hours of ODD data</td></tr>
<tr><td>\\(f_\\ell\\)</td><td>estimation error of the fitted distribution below a threshold</td><td>scenario instances</td></tr>
<tr><td>\\(p_\\ell^U\\)</td><td>upper bound per scenario. Plain MC with 0 failures needs \\(N = 3/p^*\\) runs, the rule of three, so IS is not optional</td><td>runs, ESS</td></tr>
<tr><td>sim credibility</td><td>real-vs-sim agreement for the same \\(\\theta\\) within a stated bound</td><td>proving ground, replays</td></tr>
<tr><td>\\(R_{{\\text{{unknown}}}}^U\\)</td><td>field driving with no unexplained HB (lesson 1 \\(\\tau\\), restricted to what the taxonomy misses)</td><td>hours / km</td></tr>
</tbody></table></div>

<h3>What the unintended-braking example shows</h3>
{figure(f3, f"Cumulative share of the point estimate over the 100 logical scenarios. The top 10 carry {top10:.0%}. Zero events does not mean zero risk: many scenarios get 0 because no HB happened to be observed in their cell. The dashed line shows the attribution if the true HB rates were known.", 3)}
{figure(f4, f"Posterior of total risk (Jeffreys priors on HB rates and collision probabilities) against the budget \\((1-\\varepsilon)A_H = {budget:.0e}\\)/h. The Bayesian 95% quantile ({R_bayes:.1e}) passes. The Bonferroni bound ({R_bonf:.1e}), which multiplies 120 simultaneous upper bounds, fails. The inference method and the defensibility of its prior decide the evidence plan.", 4)}
<p>Spreading the budget across evidence cells to minimise total test hours gives a square-root rule:</p>
<div class="math">\\[ \\min_{{B_j}} \\sum_j \\frac{{\\lambda_k\\,G_j}}{{B_j}} \\;\\; \\text{{s.t.}} \\;\\; \\sum_j B_j = B \\;\\;\\Rightarrow\\;\\; B_j = B\\,\\frac{{\\sqrt{{G_j}}}}{{\\sum_i \\sqrt{{G_i}}}}, \\qquad T_{{\\text{{total}}}} = \\frac{{\\lambda_k\\left(\\sum_j\\sqrt{{G_j}}\\right)^2}}{{B}} \\]</div>
{figure(f5, f"Replay hours available ({have_h:,.0f} h in total) vs. required for the Bonferroni claim under the square-root allocation ({need_h:,.0f} h in total).", 5)}
<p><strong>Screening by bound:</strong> a scenario can never contribute more than \\(\\nu_\\ell\\cdot 1\\). Reserve a fraction \\(\\varepsilon\\) of \\(A_H\\). Scenarios whose summed exposure bounds fit inside it need no simulation.</p>

<h2>4 · Parameterising a logical scenario</h2>
<ol class="tight">
<li><strong>Scenario type + parameters</strong> (ISO 34502 logical/concrete): e.g. cut-in gap, closing speed, lateral speed, duration, ego speed; plus outcome-relevant ODD conditions.</li>
<li><strong>Keep \\(\\theta\\) small</strong> (3–6 dimensions) via a sensitivity analysis.</li>
<li><strong>Mine instances</strong> from drive logs with a scenario tagger. Each detection gives one \\(\\theta\\) sample and one count toward \\(\\nu\\).</li>
<li><strong>Fit \\(f_\\ell\\)</strong>: marginals + copula (<a href="03-gaussian-copula.html">doc 3</a>) or KDE (de Gelder 2022).</li>
<li><strong>Exposure</strong> \\(\\hat\\nu_\\ell = n_\\ell/T\\) with a Poisson/Gamma interval.</li>
<li><strong>Partition check</strong>: no instance may belong to two logical scenarios.</li>
</ol>

<h2>5 · Where each conditional probability comes from</h2>
<div class="tbl-wrap"><table class="doc"><thead><tr><th>Quantity</th><th>Primary source</th><th>Caveat</th></tr></thead><tbody>
<tr><td>\\(\\nu_\\ell,\\ f_\\ell(\\theta)\\)</td><td>own fleet logs; public naturalistic data only if the ODD matches; accident databases for tails</td><td>system-dependent: e.g. cut-in gaps depend on the ego's following policy</td></tr>
<tr><td>\\(P(HB\\mid\\theta)\\)</td><td>simulation, with a <strong>perception error model</strong> (miss/FP vs. range, occlusion, weather) learned from labelled field data</td><td>sim-to-real gap must be quantified</td></tr>
<tr><td>\\(P(\\bar C\\mid E)\\)</td><td>L4: only other road users' evasion, via reactive agent models, or 1</td><td>an assumption to justify</td></tr>
<tr><td>\\(P(S\\mid HB,\\theta)\\)</td><td>simulated \\(\\Delta v\\), impact angle → injury risk curve</td><td>carry the curve's confidence band</td></tr>
</tbody></table></div>
<p class="meta">References: ISO 21448:2022 (Cl. 6, 9–11, Annex C); ISO 34502:2022; Putze et al. 2023 (arXiv:2304.10170); Betschinske et al. 2025 (arXiv:2506.10363); de Gelder 2022 (TU Delft); Zhao et al. 2017 (arXiv:1605.04965).</p>
"""
    # ------------------------------------------------------------------ 02
    b2 = f"""
<p>What to record during field testing and operation, what to compute from it, and how to turn it into leading and lagging safety performance indicators (SPIs). Examples refer to the unintended-braking target.</p>

<h2>1 · Data to collect, organised by the risk equation</h2>
<div class="math">\\[ R = \\sum_\\ell \\underbrace{{\\text{{share}}_\\ell}}_{{\\text{{exposure}}}}\\cdot \\underbrace{{\\lambda_{{HB}}}}_{{\\text{{HB rate}}}}\\cdot \\underbrace{{P(\\text{{coll}}\\mid HB)}}_{{\\text{{scenario}}}}\\cdot \\underbrace{{P(\\text{{injury}}\\mid\\Delta v)}}_{{\\text{{severity}}}} \\]</div>
<div class="tbl-wrap"><table class="doc"><thead><tr><th>Feeds</th><th>Data</th><th>How</th></tr></thead><tbody>
<tr><td><b>Denominators / exposure</b></td><td>operating hours and km, time-stamped, with ODD tags: road type, speed, weather, light, traffic density, follower presence and headway</td><td>continuous low-rate signals + map/weather lookups</td></tr>
<tr><td><b>Scenario distributions</b></td><td>every occurrence of each scenario type with its parameters (gap, closing speed, follower reaction and decel after ego braking…)</td><td>scenario tagger. The only source for marginals and copula.</td></tr>
<tr><td><b>HB rate</b></td><td>every brake request with its cause (confirmed object / FP / unexplained), plus <b>near-HBs</b>: suppressed FP detections</td><td>event-triggered raw-sensor ring buffer (±10 s)</td></tr>
<tr><td><b>Perception error model</b></td><td>misses and FPs vs. labelled ground truth, by class, range, occlusion, weather, including persistence in frames</td><td>labelled sample, oversampled at triggering conditions</td></tr>
<tr><td><b>Outcomes</b></td><td>contacts and collisions with \\(\\Delta v\\); police and insurance reports; injuries; near-miss surrogates (min TTC, PET, DRAC, rear TTC after ego braking)</td><td>rear radar/camera, IMU, incident process</td></tr>
<tr><td><b>Responses</b></td><td>minimal-risk manoeuvres, remote-assist requests, disengagements, runtime-monitor flags, ODD exits</td><td>system logs</td></tr>
<tr><td><b>Provenance</b></td><td>software/model hash, configuration, map version, calibration state, maintenance</td><td>attached to every hour. Needed to check the frozen-software assumption.</td></tr>
</tbody></table></div>

<h2>2 · Statistics to compute</h2>
<p><strong>Rates with confidence bounds</strong> per ODD stratum and software version:</p>
<div class="math">\\[ \\lambda^U = \\frac{{\\chi^2_{{2(k+1)}}(C)}}{{2T}}, \\qquad \\lambda^U \\approx \\frac{{3}}{{T}}\\ \\text{{for }}k=0,\\ C=0.95 \\]</div>
{figure(f6, "The 95% upper bound on a rate falls as 1/T. Each observed event shifts the curve up. Before a rate SPI can show its threshold is met, it needs about 3/threshold hours with no events.", 6)}
<ul>
<li><strong>Scenario frequencies and parameter distributions</strong>: \\(\\hat\\nu = n/T\\) with a Gamma interval. Marginals + copula, with Kendall \\(\\tau\\) per pair, \\(\\rho=\\sin(\\pi\\tau/2)\\), and checks for positive definiteness and tail dependence.</li>
<li><strong>Conditional probabilities</strong>: HB per triggering-condition occurrence (binomial, Clopper–Pearson \\(p^U = B^{{-1}}(C;\\,k+1,\\,n-k)\\)); collision given HB from surrogates.</li>
<li><strong>Extreme value analysis</strong> on proximity metrics. Fit a generalised Pareto distribution to the exceedances \\(Y-u \\mid Y>u\\) and extrapolate toward contact:
<div class="math">\\[ P(Y>y) \\approx P(Y>u)\\left(1+\\xi\\,\\frac{{y-u}}{{\\sigma}}\\right)^{{-1/\\xi}}, \\qquad Y = -\\text{{TTC}}_{{\\min}} \\]</div></li>
</ul>
{figure(f8, "Synthetic min-TTC per encounter. Only the lowest 5% are used to fit the tail, which is then extrapolated to TTC values never observed. This is how near misses can say something about crash frequency. The answer is only as good as the threshold choice and the extreme-value assumptions (Åsljung et al.; reviewed in Betschinske et al. 2025).", 7)}
<ul>
<li><strong>Discovery rate of unknown scenarios</strong> (Clause 11). Good–Turing estimate of the probability that the next scenario is of an unseen type: \\(\\hat P_{{\\text{{new}}}} \\approx n_1/N\\) (types seen exactly once ÷ all occurrences).</li>
<li><strong>Representativeness</strong>: \\(\\chi^2\\) or Wasserstein divergence between tested and target ODD distributions per stratum.</li>
<li><strong>Change detection</strong>: CUSUM or sequential tests on rates; exact conditional Poisson test for software-version rate ratios.</li>
</ul>

<h2>3 · Safety performance indicators</h2>
<div class="callout"><b>UL 4600:</b> an SPI is <i>“a metric supported by evidence that uses a threshold comparison to condition a claim in a safety case”</i>, and <i>“relying solely on lagging indicators is not acceptable”</i> (quoted in Ratiu et al. 2024). <b>Koopman:</b> a KPI asks <i>how well do we drive</i>; an SPI asks <i>how often are we potentially unsafe</i>.</div>
<p>Each SPI needs four things: (1) the safety-case claim it conditions; (2) the metric and its data source; (3) a threshold derived from the risk budget; (4) the response when it is breached. Responses: update the safety case, restrict operations (speed, geofence), update the system, or ground the fleet.</p>
<div class="tbl-wrap"><table class="doc"><thead><tr><th>Type</th><th>SPI</th><th>Claim it conditions</th><th>Threshold</th></tr></thead><tbody>
<tr><td>Lagging</td><td>rear-end collisions with ego struck, per h, by severity</td><td>overall validation target</td><td>\\(A_H\\)</td></tr>
<tr><td>Lagging</td><td>injury collisions per h</td><td>same</td><td>\\(A_H\\)</td></tr>
<tr><td>Leading</td><td>unexplained brake requests per 1,000 h, per trigger context</td><td>HB rate ≤ target per context</td><td>\\(\\lambda\\) target, <i>Validation Targets</i> sheet</td></tr>
<tr><td>Leading</td><td>suppressed FP brake detections per 1,000 h</td><td>margin before HB</td><td>trend alarm (e.g. doubling)</td></tr>
<tr><td>Leading</td><td>rear TTC &lt; 1.5 s within 3 s after ego braking</td><td>\\(P(\\text{{coll}}\\mid HB)\\) as modelled</td><td>simulation prediction per stratum</td></tr>
<tr><td>Safety case</td><td>share of time with follower &lt; 1 s</td><td>exposure assumption (7%)</td><td>\\(\\chi^2\\) test vs. assumed shares</td></tr>
<tr><td>Safety case</td><td>Kendall \\(\\tau\\)(headway, reaction)</td><td>copula assumption</td><td>CI contains assumed \\(\\rho\\)</td></tr>
<tr><td>Safety case</td><td>rate of unclassifiable scenarios / unknown triggers</td><td>reserve \\(\\varepsilon\\) holds</td><td>\\(\\hat P_{{\\text{{new}}}}\\times\\)severity \\(\\le \\varepsilon A_H\\)</td></tr>
<tr><td>Safety case</td><td>calibration loss; operation on a software version that wasn't validated</td><td>frozen-software assumption</td><td>0 tolerated</td></tr>
</tbody></table></div>

<h3>Why lagging SPIs alone cannot steer</h3>
<p>The time an SPI needs to detect that its rate has doubled depends only on the expected count. For a one-sided exact Poisson test (\\(\\alpha=0.05\\), power 0.8) that takes \\(\\mu^*\\approx{mu:.1f}\\) expected events, so \\(T = \\mu^*/\\lambda\\):</p>
{figure(f7, "Fleet time to detect a doubling of the SPI rate for a fleet of 50 vehicles × 3,000 h/yr. Lagging SPIs near the acceptance criterion would take decades to centuries. Leading SPIs detect drift in days to weeks, and each is tied to one term of the risk equation, so a breach says which term moved.", 8)}
<p class="meta">References: ANSI/UL 4600 Ch. 16; Ratiu, Rohlinger, Stolte, Wagner 2024 (arXiv:2410.00578); Koopman, <i>SPI vs KPI</i> (CMU lecture notes); Betschinske et al. 2025; Schaller et al. 2026 (<i>Discover AI</i> 6:1172); ISO 21448:2022 Cl. 13.</p>
"""
    # ------------------------------------------------------------------ 03
    Rm = ub_sim.R; nm = ["v_e", "h", "T_r", "a_f"]
    rtab = "<tr><th></th>" + "".join(f"<th>\\({n}\\)</th>" for n in nm) + "</tr>" + "".join(
        f"<tr><th>\\({nm[i]}\\)</th>" + "".join(f"<td class='num'>{Rm[i,j]:+.2f}</td>" for j in range(4)) + "</tr>" for i in range(4))
    b3 = f"""
<p>How the scenario parameters are coupled in the example, and how to do it with real data. The live version, with editable \\(R\\), Cholesky factor in formulas and a 200-draw demo, is the sheet <i>Gaussian Copula</i> in the workbook. Code: <code>sample_theta()</code>, <code>log_density()</code> in <code>tools/ub_sim.py</code>.</p>

<h2>1 · What it is</h2>
<p>A copula is a joint distribution on \\([0,1]^d\\) with uniform marginals. <strong>Sklar's theorem:</strong> every joint CDF splits into marginals and a copula:</p>
<div class="math">\\[ F(x_1,\\dots,x_d) = C\\big(F_1(x_1),\\dots,F_d(x_d)\\big), \\qquad C_R(u) = \\Phi_R\\big(\\Phi^{{-1}}(u_1),\\dots,\\Phi^{{-1}}(u_d)\\big) \\]</div>
<p>Each scenario parameter keeps its natural marginal (uniform speed in a band, lognormal reaction time, …), and \\(R\\) alone sets how the parameters move together.</p>
{figure(f9, "The four marginals that differ or matter, under the real-world model f and the importance-sampling proposal q. q pushes toward short headways, late reactions and long phantom brakes; deceleration is the same under both.", 9)}

<h2>2 · Sampling</h2>
<div class="math">\\[ \\varepsilon\\sim\\mathcal N(0,I),\\quad Z = L\\varepsilon\\ \\ (R = LL^\\top),\\quad U_i = \\Phi(Z_i),\\quad X_i = F_i^{{-1}}(U_i) \\]</div>
{figure(f10, "Left: independent uniforms. Middle: the same construction with ρ = −0.4. The dependence lives entirely in the copula. Right: the same draws mapped through the marginals (lognormal reaction time, uniform deceleration).", 10)}
<p>Correlation matrix used in the example (illustrative):</p>
<div class="tbl-wrap"><table>{rtab}</table></div>
<p>The signs encode an assumed story: faster traffic keeps slightly larger time gaps; close followers are more alert; late reactors also brake less hard.</p>

<h2>3 · Density (needed for importance weights)</h2>
<div class="math">\\[ c_R(u) = |R|^{{-1/2}}\\exp\\!\\Big(-\\tfrac12\\, z^\\top (R^{{-1}}-I)\\, z\\Big),\\quad z=\\Phi^{{-1}}(u), \\qquad f(x) = c_R\\big(F(x)\\big)\\prod_i f_i(x_i) \\]</div>
<p>The weights \\(w = f(\\theta)/q(\\theta)\\) evaluate this for both models. Under the proposal the same \\(R\\) is applied to q's marginals, so the copula terms do <em>not</em> cancel in the ratio.</p>

<h2>4 · Fitting \\(R\\) from field data</h2>
<ul>
<li>Pseudo-observations \\(u = \\text{{rank}}/(n+1)\\), normal scores \\(z=\\Phi^{{-1}}(u)\\), and \\(R = \\operatorname{{corr}}(z)\\).</li>
<li>Pairwise: Kendall's \\(\\tau\\) → \\(\\rho = \\sin(\\pi\\tau/2)\\). Rank-based fits do not depend on the marginals.</li>
<li>Validity: \\(R\\) symmetric positive definite (\\(\\det R>0\\), the Cholesky factor exists). Otherwise project to the nearest correlation matrix.</li>
</ul>

<h2>5 · Main limitation: no tail dependence</h2>
<div class="math">\\[ \\lambda_U = \\lim_{{q\\to1}} P\\big(U_2>q \\mid U_1>q\\big) = 0 \\ \\text{{for the Gaussian copula }}(\\rho \\lt 1), \\qquad \\lambda_U = 2\\,t_{{\\nu+1}}\\!\\Big(-\\sqrt{{\\tfrac{{(\\nu+1)(1-\\rho)}}{{1+\\rho}}}}\\Big) > 0 \\ \\text{{for the t-copula}} \\]</div>
{figure(f11, f"Same correlation, different joint extremes: {tails[0]} vs. {tails[1]} draws in the top-1% corner. If real data show joint extremes (very late reaction AND very weak braking), a Gaussian copula under-estimates exactly the critical corner. Check with empirical tail-dependence estimates; use t- or vine copulas if needed.", 11)}

<h2>6 · Effect in the example</h2>
{figure(f12, f"Ratio of P(collision | HB) with the copula to the same model with independent parameters, 20,000 runs per cell. Ignoring the dependence changes the collision probability by {rmin:.1f}× to {rmax:.1f}×. That error goes straight into the risk sum, so the dependence assumption needs its own evidence and its own SPI (doc 2).", 12)}
"""
    # ------------------------------------------------------------------ 04
    b4 = f"""
<p>This documents exactly what <code>tools/ub_sim.py</code> does to produce the sheet <i>Concrete Scenarios</i>. <strong>Everything is made up</strong>: no field data, no real system, no real simulator. The method is meant to be reused; the numbers are not.</p>

<h2>Overview</h2>
<pre class="flow">for each of the 100 logical scenarios ℓ (trigger × speed band × headway class):
  1. draw 2,000 parameter sets θ from the real-world model f_ℓ   → plain Monte Carlo  (reference)
  2. draw    10 parameter sets θ from the proposal q_ℓ           → importance sampling (Concrete Scenarios)
  3. simulate each θ with a 1-D kinematic model                 → collision yes/no, Δv
  4. for the 10 IS runs: w = f_ℓ(θ) / q_ℓ(θ)                     → exact density ratio, incl. copula</pre>
<p>100 × 10 = <b>1,000 concrete scenarios</b>. Reproducible: <code>numpy.random.default_rng(2026)</code>. Draw order: Poisson event counts for the 20 evidence cells, then per logical scenario the 2,000 f-runs followed by the 10 q-runs.</p>

<h2>Step 0 · What a logical scenario fixes</h2>
<div class="tbl-wrap"><table class="doc"><thead><tr><th>Factor</th><th>Values</th><th>Effect on the concrete scenario</th></tr></thead><tbody>
<tr><td>Trigger context (5)</td><td>clear road, overhead structure, low sun, spray, roadside clutter</td><td>none on kinematics; only changes the HB rate \\(\\lambda\\)</td></tr>
<tr><td>Ego speed band (4)</td><td>20–35, 35–55, 55–75, 75–95 km/h</td><td>range of \\(v_e\\)</td></tr>
<tr><td>Headway class (5)</td><td>3–6 s (“no follower within 3 s”), 2–3, 1.5–2, 1–1.5, 0.5–1 s</td><td>range of \\(h\\)</td></tr>
</tbody></table></div>

<h2>Step 1 · The parameter vector \\(\\theta\\)</h2>
<div class="tbl-wrap"><table class="doc"><thead><tr><th>Parameter</th><th>Real-world model f</th><th>Proposal q</th><th>Copula?</th></tr></thead><tbody>
<tr><td>ego speed \\(v_e\\)</td><td>\\(\\mathcal U\\)(band)</td><td>same</td><td>yes</td></tr>
<tr><td>follower headway \\(h\\)</td><td>\\(\\mathcal U\\)(class)</td><td>density \\(2(1-s)\\), skewed to short</td><td>yes</td></tr>
<tr><td>follower reaction \\(T_r\\)</td><td>\\(\\ln\\mathcal N(\\ln 1.1,\\ 0.30)\\)</td><td>\\(\\ln\\mathcal N(\\ln 1.5,\\ 0.35)\\)</td><td>yes</td></tr>
<tr><td>follower decel \\(a_f\\)</td><td>\\(\\mathcal U(3.5,\\ 8.0)\\) m/s²</td><td>same</td><td>yes</td></tr>
<tr><td>phantom duration \\(t_b\\)</td><td>\\(\\ln\\mathcal N(\\ln 0.8,\\ 0.50)\\)</td><td>\\(\\ln\\mathcal N(\\ln 1.3,\\ 0.50)\\)</td><td>no</td></tr>
<tr><td>phantom decel \\(a_e\\)</td><td>\\(\\mathcal U(2.5,\\ 6.0)\\) m/s²</td><td>same</td><td>no</td></tr>
<tr><td>follower offset \\(v_f-v_e\\)</td><td>\\(\\mathcal N(0,\\ 0.5)\\) m/s</td><td>same</td><td>no</td></tr>
</tbody></table></div>
<p>Initial gap \\(= h\\,v_f\\). The marginals are drawn in <a href="03-gaussian-copula.html#">doc 3, Figure 9</a>.</p>

<h2>Step 2 · Copula sampling</h2>
<div class="math">\\[ Z = L\\varepsilon,\\quad U=\\Phi(Z),\\quad v_e = v_{{lo}}+U_1(v_{{hi}}-v_{{lo}}),\\quad h = h_{{lo}}+s\\,(h_{{hi}}-h_{{lo}}),\\ \\ s=\\begin{{cases}}U_2 & (f)\\\\ 1-\\sqrt{{1-U_2}} & (q)\\end{{cases}} \\]</div>
<div class="math">\\[ T_r = \\exp\\!\\big(\\mu+\\sigma\\,\\Phi^{{-1}}(U_3)\\big),\\qquad a_f = 3.5 + 4.5\\,U_4 \\]</div>

<h2>Step 3 · Kinematic simulation</h2>
<p>One-dimensional, explicit Euler, \\(\\Delta t = 0.01\\) s, horizon 12 s, time from phantom-brake onset:</p>
<div class="math">\\[ \\dot v_e = -a_e\\,\\mathbb 1[t \\lt t_b,\\ v_e \\gt 0], \\qquad \\dot v_f = -a_f\\,\\mathbb 1[t\\ge T_r,\\ v_f \\gt v_e], \\qquad \\dot g = -(v_f-v_e) \\]</div>
<p>Contact at the first \\(g\\le 0\\): collision = 1, \\(\\Delta v = v_f-v_e\\). Injury \\(P(\\text{{MAIS2+}}\\mid\\Delta v) = 1/\\big(1+e^{{-(\\Delta v-45)/7}}\\big)\\), \\(\\Delta v\\) in km/h (illustrative).</p>
{figure(f13, "Two concrete scenarios with the same phantom brake. A short headway with a late, weak reaction ends in contact. A longer headway with a faster, firmer reaction does not.", 13)}
<p>Simplifications: no lateral escape, no brake build-up or jerk, no reaction to the ego's brake release, a single follower, no gradient or friction variation.</p>

<h2>Step 4 · Importance weights</h2>
<div class="math">\\[ w = \\frac{{f_\\ell(\\theta)}}{{q_\\ell(\\theta)}},\\qquad \\log f(\\theta) = \\log c_R(z_f) + \\sum_i \\log f_i(\\theta_i),\\qquad z_{{f,i}} = \\Phi^{{-1}}\\big(F_i(\\theta_i)\\big) \\]</div>
<div class="math">\\[ \\widehat{{E}}\\big[\\mathbb 1_{{\\text{{coll}}}}\\,P(\\text{{MAIS2+}})\\big] = \\frac1{{10}}\\sum_{{i=1}}^{{10}} w_i\\,\\mathbb 1_{{\\text{{coll}},i}}\\,P(\\text{{MAIS2+}}\\mid\\Delta v_i),\\qquad \\text{{ESS}} = \\frac{{(\\sum w_i)^2}}{{\\sum w_i^2}} \\]</div>
{figure(f14, f"Left: weights span about five orders of magnitude. Collisions come mostly from the over-sampled region, where w &lt; 1. Right: effective sample size per logical scenario (median {ess_med:.1f} of 10). A few heavy weights dominate where the proposal is far from f.", 14)}
{figure(f15, f"All 1,000 concrete scenarios: {n_hits} collisions, concentrated at short headways and late reactions. Plain sampling from f at 10 runs per scenario would mostly see none.", 15)}

<h2>Step 5 · Checks</h2>
<div class="tbl-wrap"><table class="doc"><thead><tr><th>Check</th><th>Result</th><th>Meaning</th></tr></thead><tbody>
<tr><td>\\(E_q[w]\\), 200,000 draws (35–55 km/h, 1–1.5 s)</td><td>0.996</td><td>weights correctly normalised (should be 1)</td></tr>
<tr><td>IS vs. 100,000 plain f-runs, same setting</td><td>0.0161 vs. 0.0157</td><td>unbiased</td></tr>
<tr><td>mean weight over the 1,000 runs</td><td>{np.mean([c['w'] for c in conc]):.2f}</td><td>consistent with 1</td></tr>
<tr><td>total risk, 1,000 IS vs. 200,000 plain runs</td><td>{R_is:.1e} vs. {R_point:.1e} /h</td><td>ratio {R_is/R_point:.2f}, from 200× fewer runs</td></tr>
<tr><td>collisions among the 1,000 runs</td><td>{n_hits}</td><td>plain sampling would mostly see 0</td></tr>
</tbody></table></div>

<h2>What else was made up</h2>
<ul>
<li>HB event counts: Poisson(true \\(\\lambda\\) × replay hours) from assumed true rates (grey in the workbook).</li>
<li>Exposure shares per factor, combined as a product (independence between the three factors).</li>
<li>Replay hours per evidence cell.</li>
</ul>

<h2>Using the method with real data</h2>
<ol class="tight">
<li>Replace f's marginals with distributions fitted to your scenario instances, and \\(R\\) with normal-score or Kendall-\\(\\tau\\) estimates.</li>
<li>Replace <code>simulate()</code> with your simulator. Log \\(\\theta\\), the outcome and \\(q(\\theta)\\) for every run.</li>
<li>Choose q from a pilot run, by shifting marginals toward failure regions or with cross-entropy optimisation. Monitor the ESS.</li>
<li>Keep a pure-f Monte Carlo baseline on a few scenarios as a regression check for the weights.</li>
</ol>
"""
    contents = [
        (b1, "Turning critical and non-critical scenario evaluations into a residual-risk number, and what that means for validation targets."),
        (b2, "What to record during field testing, which statistics to compute, and how to build leading and lagging safety performance indicators."),
        (b3, "Coupling scenario parameters while keeping their own distributions: sampling, density, fitting, and the tail-dependence caveat."),
        (b4, "The exact recipe behind the made-up concrete scenarios: distributions, copula sampling, kinematics, importance weights and checks."),
        (b5, "The 1,000-scenario workbook as a condensed visual report: exposure, evidence, outcomes, where the risk sits, and the verdict."),
        (b6, "What changes when the same method is applied to ACC and then to an L4 urban robotaxi, and a staged roadmap."),
        (b7, "Vehicle-level SOTIF validation for L4, the scenario database and its data pipeline, automatic scenario identification, ODD-tag granularity and completeness arguments."),
    ]
    for (fname, title), (body, dek) in zip(PAGES, contents):
        with open(os.path.join(DOCS, fname), "w", encoding="utf-8") as fh:
            fh.write(page(fname, title, dek, body))
        print("wrote", fname)


if __name__ == "__main__":
    main()
