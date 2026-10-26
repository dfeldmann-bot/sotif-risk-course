"""Render every docs figure as vector PDF for the LaTeX report and dump the quoted numbers to JSON."""
import json, os, sys
import build_docs_html as B

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "report", "figures")
os.makedirs(OUT, exist_ok=True)
_name = {"n": None}

def save_pdf(fig):
    p = os.path.join(OUT, _name["n"] + ".pdf")
    fig.savefig(p, bbox_inches="tight")
    B.plt.close(fig)
    return p

B.svg = save_pdf
nums = {}
def run(name, fn, *a):
    _name["n"] = name
    r = fn(*a)
    print("fig", name)
    return r

_, nums["toy_crit_frac"], nums["toy_p_true"] = run("f01_toy_cutin", B.fig_toy_cutin)
_, nums["conv_ref"] = run("f02_convergence", B.fig_convergence)
_, nums["top10"] = run("f03_pareto", B.fig_pareto)
run("f04_posterior", B.fig_posterior)
_, nums["have_h"], nums["need_h"] = run("f05_evidence_targets", B.fig_evidence_targets)
run("f06_rate_bound", B.fig_rate_bound)
_, nums["mu_star"] = run("f07_detect", B.fig_detect)
run("f08_evt", B.fig_evt)
run("f09_marginals", B.fig_marginals)
run("f10_copula_scatter", B.fig_copula_scatter)
_, nums["tails"] = run("f11_tail", B.fig_tail)
_, nums["cop_rmin"], nums["cop_rmax"] = run("f12_copula_heat", B.fig_copula_heat)
run("f13_trajectories", B.fig_trajectories)
run("f14_weights", B.fig_weights)
run("f15_concrete_scatter", B.fig_concrete_scatter)
B.have_h_g, B.need_h_g, B.rmin_g, B.rmax_g = nums["have_h"], nums["need_h"], nums["cop_rmin"], nums["cop_rmax"]
run("f16_verdict", B.rfig_verdict)
run("f17_exposure", B.rfig_exposure)
run("f18_hb", B.rfig_hb)
run("f19_coll_inj", B.rfig_coll_inj)
run("f20_risk_share", B.rfig_risk_share)
_, nums["nz_is"], nums["nz_mc"] = run("f21_is_vs_mc", B.rfig_is_vs_mc)
run("f22_ess_dim", B.ofig_ess)
run("f23_granularity", B.sfig_granularity)
_, nums["tag_recall"], nums["tag_precision"] = run("f24_tagger", B.sfig_tagger)
_, nums["pair_cov"], nums["pair_under"], nums["pair_cells"] = run("f25_pair_coverage", B.sfig_pair_coverage)
_, nums["sat_sobs"], nums["sat_chao"], nums["sat_gt"], nums["sat_true_miss"] = run("f26_saturation", B.sfig_saturation)
nums.update(R_point=B.R_point, R_bonf=B.R_bonf, R_bayes=B.R_bayes, budget=B.budget, R_is=B.R_is, ess_med=B.ess_med, n_hits=B.n_hits,
            w_mean=float(sum(c["w"] for c in B.conc) / len(B.conc)), w_min=min(c["w"] for c in B.conc), w_max=max(c["w"] for c in B.conc))
nums = {k: (float(v) if not isinstance(v, list) else v) for k, v in nums.items()}
json.dump(nums, open(os.path.join(OUT, "..", "numbers.json"), "w"), indent=1)
print(json.dumps(nums, indent=1))
