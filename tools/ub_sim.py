"""
ub_sim.py — evidence generator for the unintended-braking (phantom braking) worked example.

ALL NUMBERS ARE SYNTHETIC AND ILLUSTRATIVE. They exist to show the calculation chain,
not to describe any real system. Replace each block with your own data source.

Partition of the ODD into 100 logical scenarios:
    5 trigger contexts  x  4 ego speed bands  x  5 follower-headway classes
Chain per logical scenario l:
    R_l = share_l * lambda_HB(trigger, speed) * E_f[ 1{collision}(θ) * P(MAIS2+ | Δv(θ)) ]

Concrete-scenario parameters θ are drawn through a GAUSSIAN COPULA:
    Z ~ N(0, R)  (via Cholesky, Z = L·ε)  →  U = Φ(Z)  →  X_i = F_i⁻¹(U_i)
so each parameter keeps its own marginal distribution while the dependence between
(ego speed, follower time headway, follower reaction time, follower deceleration)
is set by the correlation matrix R.
"""
import math
import numpy as np
from scipy.stats import norm, lognorm

SEED = 2026

# ---------------- partition definition ----------------
TRIGGERS = [  # name, operating-time share, TRUE HB rate per hour in context (synthetic ground truth)
    ("Clear road, no trigger", 0.80, 2e-5),
    ("Overhead structure (bridge, gantry)", 0.05, 4e-4),
    ("Low sun / hard shadow", 0.07, 2e-4),
    ("Spray / heavy rain", 0.05, 6e-4),
    ("Roadside clutter / debris", 0.03, 3e-4),
]
SPEEDS = [  # name, share, speed range km/h, FP-rate multiplier
    ("≤ 30 km/h", 0.35, (20, 35), 1.0),
    ("31–50 km/h", 0.40, (35, 55), 1.0),
    ("51–70 km/h", 0.15, (55, 75), 1.2),
    ("71–90 km/h", 0.10, (75, 95), 1.5),
]
HEADWAYS = [  # name, share, time-headway range of the following vehicle [s]
    ("No follower within 3 s", 0.45, (3.0, 6.0)),
    ("Follower 2–3 s", 0.20, (2.0, 3.0)),
    ("Follower 1.5–2 s", 0.15, (1.5, 2.0)),
    ("Follower 1–1.5 s", 0.13, (1.0, 1.5)),
    ("Follower < 1 s", 0.07, (0.5, 1.0)),
]
REPLAY_HOURS = {
    0: [12000, 14000, 6000, 4000],
    1: [3000, 4000, 2500, 2000],
    2: [3000, 3500, 2000, 1500],
    3: [2500, 3000, 2000, 1500],
    4: [2000, 2500, 1500, 1000],
}
N_RUNS = 2000        # plain Monte Carlo runs per logical scenario (sampled from f)
N_CONCRETE = 10      # importance-sampled concrete scenarios per logical scenario (100 x 10 = 1000)

# ---------------- Gaussian copula ----------------
COPULA_VARS = ["Ego speed v_e", "Follower time headway h", "Follower reaction time T_r", "Follower deceleration a_f"]
# Illustrative correlations (NOT measured):
#   v_e–h   +0.25 : within a band, faster traffic keeps slightly larger time gaps
#   h–T_r   −0.30 : drivers who follow closely tend to be more alert (shorter reaction)
#   T_r–a_f −0.40 : late reactors also brake less hard (low-alertness driver state)
R = np.array([
    [1.00, 0.25, 0.00, 0.00],
    [0.25, 1.00, -0.30, 0.00],
    [0.00, -0.30, 1.00, -0.40],
    [0.00, 0.00, -0.40, 1.00],
])
L_CHOL = np.linalg.cholesky(R)
R_INV = np.linalg.inv(R)
LOGDET_R = float(np.log(np.linalg.det(R)))

# Marginals under the real-world model f and under the importance-sampling proposal q
TR_F = (math.log(1.1), 0.30)   # follower reaction time, lognormal (log-median, log-sd)
TR_Q = (math.log(1.5), 0.35)   # proposal: later reactions
TB_F = (math.log(0.8), 0.50)   # phantom-brake duration
TB_Q = (math.log(1.3), 0.50)   # proposal: longer brakes
AF = (3.5, 8.0)                # follower decel, uniform (same under f and q)
AE = (2.5, 6.0)                # phantom-brake decel, uniform (same under f and q)
INJ_MID, INJ_SCALE = 45.0, 7.0 # illustrative MAIS2+ logistic curve over Δv [km/h]


def injury_prob(dv_kmh):
    """Illustrative MAIS2+ risk curve vs. collision delta-v (km/h). Real curves: fit to GIDAS / NASS."""
    return 1.0 / (1.0 + np.exp(-(np.asarray(dv_kmh) - INJ_MID) / INJ_SCALE))


def _ln_cdf(x, mu_sd):
    return norm.cdf((np.log(x) - mu_sd[0]) / mu_sd[1])


def _ln_pdf(x, mu_sd):
    return lognorm.pdf(x, s=mu_sd[1], scale=math.exp(mu_sd[0]))


def sample_theta(speed_rng, hw_rng, n, rng, proposal=False, corr=True):
    """Draw n concrete scenarios. proposal=True uses the IS proposal q; corr=False uses the independence copula."""
    eps = rng.standard_normal((n, 4))
    z = eps @ L_CHOL.T if corr else eps
    u = norm.cdf(z)
    v = speed_rng[0] + u[:, 0] * (speed_rng[1] - speed_rng[0])
    s = 1 - np.sqrt(1 - u[:, 1]) if proposal else u[:, 1]          # q: linear density 2(1−s), skewed to short headway
    h = hw_rng[0] + s * (hw_rng[1] - hw_rng[0])
    trp = TR_Q if proposal else TR_F
    t_r = np.exp(trp[0] + trp[1] * norm.ppf(u[:, 2]))
    a_f = AF[0] + u[:, 3] * (AF[1] - AF[0])
    tbp = TB_Q if proposal else TB_F
    t_b = rng.lognormal(tbp[0], tbp[1], n)
    a_e = rng.uniform(*AE, n)
    dvf = rng.normal(0, 0.5, n)
    return dict(v=v, h=h, t_r=t_r, a_f=a_f, t_b=t_b, a_e=a_e, dvf=dvf)


def log_density(th, speed_rng, hw_rng, proposal):
    """Exact log joint density of θ under f (proposal=False) or q (proposal=True). Independent parts that are
    identical under f and q (v_e marginal, a_f, a_e, follower speed offset) are included for completeness."""
    w_v = speed_rng[1] - speed_rng[0]; w_h = hw_rng[1] - hw_rng[0]
    s = (th["h"] - hw_rng[0]) / w_h
    u = np.column_stack([
        (th["v"] - speed_rng[0]) / w_v,
        1 - (1 - s) ** 2 if proposal else s,
        _ln_cdf(th["t_r"], TR_Q if proposal else TR_F),
        (th["a_f"] - AF[0]) / (AF[1] - AF[0]),
    ])
    u = np.clip(u, 1e-12, 1 - 1e-12)
    z = norm.ppf(u)
    log_c = -0.5 * LOGDET_R - 0.5 * np.einsum("ij,jk,ik->i", z, R_INV - np.eye(4), z)   # Gaussian copula density
    log_marg = (-np.log(w_v)
                + (np.log(2 * (1 - s) / w_h) if proposal else -np.log(w_h))
                + np.log(_ln_pdf(th["t_r"], TR_Q if proposal else TR_F))
                - np.log(AF[1] - AF[0])
                + np.log(_ln_pdf(th["t_b"], TB_Q if proposal else TB_F)))
    return log_c + log_marg


def simulate(th, dt=0.01, t_max=12.0):
    """1-D kinematics: ego brakes unintentionally, follower reacts. Returns collision flags and Δv (km/h)."""
    v_e = th["v"] / 3.6
    v_f = np.clip(v_e + th["dvf"], 0, None)
    gap = th["h"] * v_f
    a_e, t_b, t_r, a_f = th["a_e"], th["t_b"], th["t_r"], th["a_f"]
    n = len(v_e); hit = np.zeros(n, bool); dv = np.zeros(n); t = 0.0
    while t < t_max:
        v_e = np.where((t < t_b) & (v_e > 0), np.maximum(v_e - a_e * dt, 0), v_e)
        v_f = np.where((t >= t_r) & (v_f > v_e), np.maximum(v_f - a_f * dt, v_e), v_f)
        gap = gap - (v_f - v_e) * dt
        new = (gap <= 0) & ~hit
        dv[new] = (v_f[new] - v_e[new]) * 3.6
        hit |= new
        gap = np.where(hit, 1e9, gap)
        t += dt
    return hit, dv


def generate():
    rng = np.random.default_rng(SEED)
    cells = []
    for ti, (tn, ts, lam) in enumerate(TRIGGERS):
        for si, (sn, ss, srng, mult) in enumerate(SPEEDS):
            h = REPLAY_HOURS[ti][si]
            k = int(rng.poisson(lam * mult * h))
            cells.append(dict(cell=f"T{ti+1}S{si+1}", trigger=tn, speed=sn, hours=h, k=k, true_lam=lam * mult))
    scen, concrete = [], []
    for ti, (tn, ts, _) in enumerate(TRIGGERS):
        for si, (sn, ss, srng, _) in enumerate(SPEEDS):
            for hi, (hn, hs, hrng) in enumerate(HEADWAYS):
                lid = f"L{len(scen)+1:03d}"
                th = sample_theta(srng, hrng, N_RUNS, rng)
                hit, dv = simulate(th)
                c = int(hit.sum())
                scen.append(dict(id=lid, cell=f"T{ti+1}S{si+1}", trigger=tn, speed=sn, headway=hn,
                                 s_trig=ts, s_speed=ss, s_hw=hs, runs=N_RUNS, coll=c,
                                 inj=float(injury_prob(dv[hit]).mean()) if c else 0.0,
                                 dv_mean=float(dv[hit].mean()) if c else 0.0))
                # importance-sampled concrete scenarios
                thq = sample_theta(srng, hrng, N_CONCRETE, rng, proposal=True)
                hq, dvq = simulate(thq)
                w = np.exp(log_density(thq, srng, hrng, False) - log_density(thq, srng, hrng, True))
                for j in range(N_CONCRETE):
                    concrete.append(dict(cid=f"C{len(concrete)+1:04d}", lid=lid, trigger=tn, speed=sn, headway=hn,
                                         v=thq["v"][j], vf=(thq["v"][j] / 3.6 + thq["dvf"][j]) * 3.6, h=thq["h"][j],
                                         a_e=thq["a_e"][j], t_b=thq["t_b"][j], t_r=thq["t_r"][j], a_f=thq["a_f"][j],
                                         w=float(w[j]), hit=int(hq[j]), dv=float(dvq[j]) if hq[j] else 0.0))
    return cells, scen, concrete


def copula_effect(n=20000, seed=11):
    """P(collision | HB) per speed band × headway class, with the Gaussian copula vs. independence."""
    rng = np.random.default_rng(seed)
    out = []
    for sn, _, srng, _ in SPEEDS:
        for hn, _, hrng in HEADWAYS:
            pc = simulate(sample_theta(srng, hrng, n, rng, corr=True))[0].mean()
            pi = simulate(sample_theta(srng, hrng, n, rng, corr=False))[0].mean()
            out.append(dict(speed=sn, headway=hn, p_cop=float(pc), p_ind=float(pi), n=n))
    return out


def demo_normals(n=200, seed=5):
    return np.random.default_rng(seed).standard_normal((n, 4))


def bayes_quantile(cells, scen, q=0.95, draws=200_000, seed=7):
    """Posterior of total risk: Jeffreys Gamma for HB rates, Jeffreys Beta for collision probs; injury mean fixed."""
    rng = np.random.default_rng(seed)
    lam = {c["cell"]: rng.gamma(c["k"] + 0.5, 1.0 / c["hours"], draws) for c in cells}
    Rt = np.zeros(draws)
    for s in scen:
        p = rng.beta(s["coll"] + 0.5, s["runs"] - s["coll"] + 0.5, draws)
        Rt += s["s_trig"] * s["s_speed"] * s["s_hw"] * lam[s["cell"]] * p * s["inj"]
    return float(np.quantile(Rt, q)), float(Rt.mean())


if __name__ == "__main__":
    cells, scen, conc = generate()
    lam = {c["cell"]: c["k"] / c["hours"] for c in cells}
    sh = {s["id"]: s["s_trig"] * s["s_speed"] * s["s_hw"] for s in scen}
    point = sum(sh[s["id"]] * lam[s["cell"]] * s["coll"] / s["runs"] * s["inj"] for s in scen)
    isr = sum(sh[c["lid"]] * lam[next(s["cell"] for s in scen if s["id"] == c["lid"])] * c["w"] * c["hit"] * float(injury_prob(c["dv"])) / N_CONCRETE for c in conc)
    print("concrete:", len(conc), "hits:", sum(c["hit"] for c in conc), "w range", min(c["w"] for c in conc), max(c["w"] for c in conc))
    print("point R (2000-run MC) =", point, " point R (1000 IS concrete) =", isr)
    print("bayes 95% / mean =", bayes_quantile(cells, scen))
    print("Cholesky L =\n", L_CHOL.round(4))
