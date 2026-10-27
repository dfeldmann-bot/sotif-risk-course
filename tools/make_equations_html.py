#!/usr/bin/env python3
"""
make_equations_html.py — render every equation from SOTIF Risk Course, Lesson 1
(acceptance criterion → validation target) to one standalone HTML file, with
worked numbers computed from your inputs.

Standard library only. Equations are typeset with MathJax 3 (loaded from a CDN),
so the HTML needs an internet connection when you open it.

Usage:
    python3 make_equations_html.py                       # lesson example values
    python3 make_equations_html.py --A_H 1e-8 --pE 0.05 --pC 0.3 --pS 0.5 --C 0.99 --k 1 \
        --fleet 100 --hours 6000 -o my_targets.html
"""
import argparse
import html
import math
from datetime import date


# ---------- statistics (no SciPy needed) ----------
def poisson_cdf(k: int, lam: float) -> float:
    term = math.exp(-lam)
    total = term
    for i in range(1, k + 1):
        term *= lam / i
        total += term
    return total


def lambda_k(k: int, C: float) -> float:
    """λ with P(X ≤ k | λ) = 1 − C, i.e. ½·χ²_{2(k+1)}(C). Solved by bisection."""
    target = 1.0 - C
    lo, hi = 0.0, 10.0 + 10.0 * k
    while poisson_cdf(k, hi) > target:
        hi *= 2
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if poisson_cdf(k, mid) > target:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def sci(x: float, digits: int = 3) -> str:
    """LaTeX scientific notation."""
    if x == 0:
        return "0"
    e = math.floor(math.log10(abs(x)))
    if -2 <= e < 4:
        return f"{x:.{digits}g}"
    m = x / 10 ** e
    return rf"{m:.{digits - 1}f}\times 10^{{{e}}}"


# ---------- content ----------
def build(a):
    R_HB = a.A_H / (a.pE * a.pC * a.pS)
    lam0 = -math.log(1 - a.C)
    lamk = lambda_k(a.k, a.C)
    tau0 = lam0 / R_HB
    tauk = lamk / R_HB
    fleet_h = a.fleet * a.hours
    F_rand = 1.09e-8
    n_rand = math.log(1 - 0.95) / math.log(1 - F_rand)
    tau_schaller = -math.log(0.05) / 1e-9

    # Each entry: (section, title, latex, explanation, worked, source)
    eqs = [
        ("Decomposition", "Annex C.2 factorisation of the acceptance criterion",
         r"A_H = R_{HB}\cdot P(E\mid HB)\cdot P(\bar C\mid E)\cdot P(S\mid \bar C)",
         "The harm rate is the hazardous-behaviour rate multiplied by the chance it meets an exposing scenario, is not controlled, and reaches severity S.",
         rf"A_H = {sci(a.A_H)}\ \mathrm{{h^{{-1}}}},\quad P(E\mid HB)={a.pE},\ P(\bar C\mid E)={a.pC},\ P(S\mid\bar C)={a.pS}",
         "ISO 21448:2022, C.2.1, Formula (C.1), p. 127; critique: Putze et al. 2023 (arXiv:2304.10170), Sec. IV-B"),
        ("Decomposition", "Tolerable hazardous-behaviour rate",
         r"R_{HB} = \frac{A_H}{P(E\mid HB)\,P(\bar C\mid E)\,P(S\mid \bar C)}",
         "Solve the factorisation for the rate the system itself controls. Each justified factor below 1 relaxes the target.",
         rf"R_{{HB}} = \frac{{{sci(a.A_H)}}}{{{a.pE}\cdot{a.pC}\cdot{a.pS}}} = {sci(R_HB)}\ \mathrm{{h^{{-1}}}}",
         "Betschinske et al. 2025 (arXiv:2506.10363), Eq. 6"),
        ("Decomposition", "Correct conditioning (chain rule)",
         r"P(H) = P(HB)\,P(E\mid HB)\,P(\bar C\mid E,HB)\,P(S\mid \bar C,E,HB)",
         "Annex C.2 drops conditioning. Using P(S | C̄) silently assumes severity is independent of the scenario and the behaviour, which you would have to justify.",
         None, "Putze et al. 2023, §III"),
        ("Zero-failure test", "Poisson model for hazardous behaviours",
         r"P(X = n \mid \lambda) = \frac{\lambda^{n} e^{-\lambda}}{n!},\qquad \lambda = R\,\tau",
         "Expected count after τ hours of exposure at constant rate R (homogeneous Poisson process).",
         None, "ISO 21448:2022, C.3, Example 3 (Poisson stopping rule), p. 137"),
        ("Zero-failure test", "Hypotheses",
         r"H_0:\ R > A_H \qquad H_1:\ R \le A_H",
         "Passing the test rejects H₀. In Lesson 1 the test is applied at the behaviour level, with R_HB as the threshold.",
         None, "Betschinske et al. 2025, Eq. 3"),
        ("Zero-failure test", "Pass condition with zero observed events",
         r"P(X=0\mid R_{HB}\tau) = e^{-R_{HB}\tau} \le 1-C",
         "A system exactly at the limit would show zero events with probability at most 1 − C.",
         None, "Lesson 1, Eq. 2"),
        ("Zero-failure test", "Validation target (k = 0)",
         r"\tau = \frac{-\ln(1-C)}{R_{HB}}",
         "Required failure-free exposure. Notation: ISO 21448 Formula (C.7) and Putze et al. write α for the confidence C; ISO 21448 C.6.3.2 and Betschinske et al. use α for 1 − C, so their form is −ln(α)/A_H.",
         rf"\tau = \frac{{-\ln(1-{a.C})}}{{{sci(R_HB)}}} = \frac{{{lam0:.4f}}}{{{sci(R_HB)}}} = {sci(tau0, 4)}\ \mathrm{{h}}",
         "ISO 21448:2022, C.3, Formula (C.7), p. 137 (α = confidence there); Betschinske et al. 2025, Sec. III-C, Eq. 5 (α = type-I error)"),
        ("Zero-failure test", "Rule of three",
         r"-\ln(1-0.95) = \ln 20 \approx 2.996 \;\Rightarrow\; \tau \approx \frac{3}{R_{HB}}",
         "At 95% confidence you need about three times the inverse target rate, with zero events.",
         None, "Standard reliability result"),
        ("Zero-failure test", "RAND exact form (per-mile Bernoulli trials)",
         r"n = \frac{\ln(1-C)}{\ln(1-F)} \;\approx\; \frac{-\ln(1-C)}{F}\quad (F \ll 1)",
         "Kalra & Paddock treat each mile as a trial with failure probability F. It agrees with the Poisson form to first order in F.",
         rf"F = 1.09\times10^{{-8}}\ \mathrm{{mi^{{-1}}}},\ C=0.95:\quad n = {sci(n_rand, 4)}\ \text{{failure-free miles}}",
         "Kalra & Paddock, RAND RR-1478 (2016), Eq. 2"),
        ("Zero-failure test", "Schaller et al. example",
         r"R = 10^{-9}\ \mathrm{h^{-1}},\ C = 0.95:\quad \tau = \frac{2.996}{10^{-9}}",
         "Their example criterion for overlooking a car on the other lane. This is why they argue for monitor outputs as proxy evidence.",
         rf"\tau = {sci(tau_schaller, 3)}\ \mathrm{{h}} \approx {tau_schaller / 8766:,.0f}".replace(",", "{,}") + r"\ \text{vehicle-years (24/7)}",
         "Schaller et al. 2026, Discover AI 6:1172, §5.1"),
        ("Plans allowing k events", "Pass condition with up to k events",
         r"P(X \le k \mid \lambda) = \sum_{i=0}^{k} \frac{\lambda^{i}e^{-\lambda}}{i!} \le 1 - C",
         "Fix k and τ before driving. Changing either after seeing data inflates the type-I error.",
         None, "Betschinske et al. 2025, Eq. 4"),
        ("Plans allowing k events", "Poisson–χ² identity",
         r"\lambda_k(C) = \tfrac12\,\chi^2_{2(k+1)}(C), \qquad \tau_k = \frac{\lambda_k(C)}{R_{HB}}",
         "The λ that solves the pass condition with equality is half the χ² quantile with 2(k+1) degrees of freedom.",
         rf"k={a.k},\ C={a.C}:\quad \lambda_k = {lamk:.4f},\quad \tau_k = {sci(tauk, 4)}\ \mathrm{{h}}",
         "Standard (Poisson–gamma–χ² relation)"),
        ("Plans allowing k events", "Calendar time for a test fleet",
         r"T_{\text{cal}} = \frac{\tau_k}{N_{\text{fleet}}\cdot h_{\text{yr}}}",
         "Converts exposure into calendar years for a given fleet.",
         rf"T_{{\text{{cal}}}} = \frac{{{sci(tauk, 4)}}}{{{a.fleet}\cdot{a.hours}}} = {tauk / fleet_h:.2f}\ \text{{years}}",
         "Lesson 1 calculator"),
        ("Scaling", "Price of confidence",
         r"\frac{\tau(C_2)}{\tau(C_1)} = \frac{\ln(1-C_2)}{\ln(1-C_1)}",
         "τ grows only logarithmically with confidence but linearly with 1/R.",
         rf"\frac{{\tau(0.99)}}{{\tau(0.95)}} = \frac{{\ln 0.01}}{{\ln 0.05}} = {math.log(0.01) / math.log(0.05):.3f}",
         "Lesson 1, Exercise 3"),
        ("Scaling", "Price of allowing k events",
         r"\frac{\tau_k}{\tau_0} = \frac{\lambda_k(C)}{-\ln(1-C)}",
         "At 95%, one allowed event costs 58% more exposure.",
         rf"\frac{{\tau_1}}{{\tau_0}}\Big|_{{C=0.95}} = \frac{{{lambda_k(1, 0.95):.3f}}}{{{-math.log(0.05):.3f}}} = {lambda_k(1, 0.95) / -math.log(0.05):.3f}",
         "Lesson 1, §3"),
        ("Aggregation", "Bonferroni-type bound over triggering condition → behaviour → event paths",
         r"P(H) \le \sum_{T,B,E} P(T)\,P(B\mid T)\,P(E\mid B,T)\,P(H\mid E,B,T)",
         "Several paths can lead to the same harm, and their contributions add. Annex C.2 omits this aggregation, so the budget A_H must be allocated across paths.",
         None, "Putze et al. 2023, Eq. 2"),
        ("Aggregation", "Joint confidence over several validation targets",
         r"C_{\text{joint}} \ge 1 - \sum_i (1 - C_i)",
         "If you validate m paths separately, the confidence that all of them hold is at least this (Bonferroni).",
         r"m = 3,\ C_i = 0.95:\quad C_{\text{joint}} \ge 0.85",
         "Betschinske et al. 2025 (decomposition of hazardous behaviour)"),
    ]
    return eqs, dict(R_HB=R_HB, tau0=tau0, tauk=tauk, lamk=lamk, years=tauk / fleet_h)


CSS = """
:root{--bg:#f6f7f5;--fg:#1a2220;--soft:#4a5654;--rule:#d5dbd8;--panel:#ebefed;--accent:#0e6b63;color-scheme:light}
@media (prefers-color-scheme:dark){:root{--bg:#121816;--fg:#e3e9e6;--soft:#a3b0ac;--rule:#2c3734;--panel:#1b2421;--accent:#4fb8ad;color-scheme:dark}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);font:400 1.05rem/1.6 "Source Serif 4",Georgia,serif;
 padding:2.5rem max(16px,env(safe-area-inset-right,0px)) 4rem max(16px,env(safe-area-inset-left,0px))}
main{max-width:46rem;margin:0 auto}
h1{font-size:2rem;line-height:1.15;margin:.2rem 0 .5rem;text-wrap:balance}
h2{font:600 .85rem/1 "IBM Plex Sans Condensed",Arial,sans-serif;letter-spacing:.08em;text-transform:uppercase;color:var(--accent);margin:2.8rem 0 .8rem;border-bottom:1px solid var(--rule);padding-bottom:.4rem}
.eq{margin:0 0 1.8rem}
.eq h3{font-size:1.05rem;margin:0 0 .3rem}
.eq h3 .n{font-family:"JetBrains Mono",monospace;color:var(--soft);font-weight:400;margin-right:.5rem}
.tex{background:var(--panel);padding:.6rem 1rem;overflow-x:auto;border-radius:3px}
.worked{border-left:3px solid var(--accent);padding:.1rem 0 .1rem .9rem;margin:.5rem 0;overflow-x:auto}
.src,.meta{font-size:.85rem;color:var(--soft)}
table{border-collapse:collapse;font:400 .9rem "JetBrains Mono",monospace;margin:.5rem 0 1rem}
td,th{padding:.25rem .8rem;border-bottom:1px solid var(--rule);text-align:right}
td:first-child,th:first-child{text-align:left;font-family:"Source Serif 4",Georgia,serif}
"""


def render(a, eqs, res):
    out = []
    out.append("<!doctype html><html lang='en'><head><meta charset='utf-8'>")
    out.append("<meta name='viewport' content='width=device-width, initial-scale=1, viewport-fit=cover'>")
    out.append("<title>Validation Target Equations</title>")
    out.append("<link rel='stylesheet' href='https://fonts.googleapis.com/css2?family=Source+Serif+4:wght@400;600&family=IBM+Plex+Sans+Condensed:wght@600&family=JetBrains+Mono&display=swap'>")
    out.append(f"<style>{CSS}</style>")
    out.append("<script>window.MathJax={tex:{inlineMath:[['\\\\(','\\\\)']]},svg:{fontCache:'global'}};</script>")
    out.append("<script defer src='https://cdn.jsdelivr.net/npm/mathjax@3.2.2/es5/tex-svg.js'></script>")
    out.append("</head><body><main>")
    out.append("<p class='meta'>SOTIF Risk Course · Lesson 1 · generated " + date.today().isoformat() + "</p>")
    out.append("<h1>Validation target equations</h1>")
    out.append("<p>From acceptance criterion to required test exposure under ISO 21448. Worked numbers use the inputs below; regenerate with your own values via the command-line flags.</p>")
    out.append("<table><tr><th>Input</th><th>Value</th></tr>")
    for k, v in [("A_H (1/h)", a.A_H), ("P(E | HB)", a.pE), ("P(C̄ | E)", a.pC), ("P(S | C̄)", a.pS),
                 ("Confidence C", a.C), ("Events allowed k", a.k), ("Fleet size", a.fleet), ("Hours / vehicle-year", a.hours)]:
        out.append(f"<tr><td>{html.escape(k)}</td><td>{v:g}</td></tr>")
    out.append("</table>")
    out.append("<table><tr><th>Result</th><th>Value</th></tr>"
               f"<tr><td>R_HB (1/h)</td><td>{res['R_HB']:.3e}</td></tr>"
               f"<tr><td>τ, k = 0 (h)</td><td>{res['tau0']:,.0f}</td></tr>"
               f"<tr><td>λ_k(C)</td><td>{res['lamk']:.4f}</td></tr>"
               f"<tr><td>τ_k (h)</td><td>{res['tauk']:,.0f}</td></tr>"
               f"<tr><td>Calendar years</td><td>{res['years']:.2f}</td></tr></table>")
    section = None
    for i, (sec, title, tex, expl, worked, src) in enumerate(eqs, 1):
        if sec != section:
            out.append(f"<h2>{html.escape(sec)}</h2>")
            section = sec
        out.append("<div class='eq'>")
        out.append(f"<h3><span class='n'>({i})</span>{html.escape(title)}</h3>")
        out.append(f"<div class='tex'>\\[{html.escape(tex)}\\]</div>")
        out.append(f"<p>{html.escape(expl)}</p>")
        if worked:
            out.append(f"<div class='worked'>\\[{html.escape(worked)}\\]</div>")
        out.append(f"<p class='src'>Source: {html.escape(src)}</p>")
        out.append("</div>")
    out.append("<h2>Assumptions behind every result above</h2><ol>"
               "<li>Homogeneous Poisson process: constant rate, independent events.</li>"
               "<li>Representative exposure: the test mix of conditions equals the deployed mix.</li>"
               "<li>Frozen software, or an argued carry-over of hours across fixes.</li>"
               "<li>All paths to harm H are counted, with the budget allocated (Eq. 16–17).</li>"
               "<li>Frequentist confidence: not P(rate &lt; R) = C unless you state a prior.</li></ol>")
    out.append("</main></body></html>")
    return "\n".join(out)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--A_H", type=float, default=1e-7, help="acceptance criterion, harm per hour")
    p.add_argument("--pE", type=float, default=0.1, help="P(E | HB)")
    p.add_argument("--pC", type=float, default=0.5, help="P(not controllable | E)")
    p.add_argument("--pS", type=float, default=0.2, help="P(S | not controllable)")
    p.add_argument("--C", type=float, default=0.95, help="confidence level")
    p.add_argument("--k", type=int, default=0, help="events allowed in the plan")
    p.add_argument("--fleet", type=int, default=50, help="test fleet size")
    p.add_argument("--hours", type=float, default=3000, help="operating hours per vehicle-year")
    p.add_argument("-o", "--out", default="validation_target_equations.html")
    a = p.parse_args()
    if not (0 < a.C < 1):
        p.error("--C must be between 0 and 1")
    eqs, res = build(a)
    with open(a.out, "w", encoding="utf-8") as f:
        f.write(render(a, eqs, res))
    print(f"Wrote {a.out}: {len(eqs)} equations; R_HB = {res['R_HB']:.3e}/h, tau_k = {res['tauk']:,.0f} h")


if __name__ == "__main__":
    main()
