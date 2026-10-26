"""
ub_sim.py — evidence generator for the unintended-braking (phantom braking) worked example.

ALL NUMBERS ARE SYNTHETIC AND ILLUSTRATIVE. They exist to show the calculation chain,
not to describe any real system. Replace each block with your own data source.

Partition of the ODD into 100 logical scenarios:
    5 trigger contexts  x  4 ego speed bands  x  5 follower-headway classes
Chain per logical scenario l:
    R_l = share_l * lambda_HB(trigger, speed) * P(collision | HB, l) * E[P(MAIS2+ | dv) | collision, l]
"""
import numpy as np

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

# Evidence budget: targeted open-loop replay / test hours per (trigger, speed) cell.
# Deliberately NOT proportional to exposure: trigger contexts are over-sampled by route choice.
REPLAY_HOURS = {
    0: [12000, 14000, 6000, 4000],
    1: [3000, 4000, 2500, 2000],
    2: [3000, 3500, 2000, 1500],
    3: [2500, 3000, 2000, 1500],
    4: [2000, 2500, 1500, 1000],
}
N_RUNS = 2000  # simulation runs per logical scenario, conditioned on an HB occurring


def injury_prob(dv_kmh):
    """Illustrative MAIS2+ risk curve vs. collision delta-v (km/h). Real curves: fit to GIDAS / NASS."""
    return 1.0 / (1.0 + np.exp(-(dv_kmh - 45.0) / 7.0))


def simulate(speed_rng, hw_rng, n, rng, dt=0.01, t_max=12.0):
    """1-D kinematics: ego brakes unintentionally, follower reacts. Returns collision flags and delta-v (km/h)."""
    v_e = rng.uniform(*speed_rng, n) / 3.6
    v_f = np.clip(v_e + rng.normal(0, 0.5, n), 0, None)
    gap = rng.uniform(*hw_rng, n) * v_f                     # bumper-to-bumper [m]
    a_e = rng.uniform(2.5, 6.0, n)                           # phantom brake decel [m/s^2]
    t_b = rng.lognormal(np.log(0.8), 0.5, n)                 # phantom brake duration [s]
    t_r = rng.lognormal(np.log(1.1), 0.3, n)                 # follower reaction time [s]
    a_f = rng.uniform(3.5, 8.0, n)                           # follower braking decel [m/s^2]
    hit = np.zeros(n, bool)
    dv = np.zeros(n)
    t = 0.0
    while t < t_max:
        braking_e = (t < t_b) & (v_e > 0)
        v_e = np.where(braking_e, np.maximum(v_e - a_e * dt, 0), v_e)
        braking_f = (t >= t_r) & (v_f > v_e)
        v_f = np.where(braking_f, np.maximum(v_f - a_f * dt, v_e), v_f)
        gap = gap - (v_f - v_e) * dt
        new = (gap <= 0) & ~hit
        dv[new] = (v_f[new] - v_e[new]) * 3.6
        hit |= new
        gap = np.where(hit, 1e9, gap)                         # freeze after contact
        t += dt
    return hit, dv


def generate():
    rng = np.random.default_rng(SEED)
    cells = []      # (trigger, speed) evidence cells
    for ti, (tn, ts, lam) in enumerate(TRIGGERS):
        for si, (sn, ss, srng, mult) in enumerate(SPEEDS):
            h = REPLAY_HOURS[ti][si]
            k = int(rng.poisson(lam * mult * h))
            cells.append(dict(cell=f"T{ti+1}S{si+1}", trigger=tn, speed=sn, hours=h, k=k, true_lam=lam * mult))
    scen = []
    for ti, (tn, ts, _) in enumerate(TRIGGERS):
        for si, (sn, ss, srng, _) in enumerate(SPEEDS):
            for hi, (hn, hs, hrng) in enumerate(HEADWAYS):
                hit, dv = simulate(srng, hrng, N_RUNS, rng)
                c = int(hit.sum())
                inj = float(injury_prob(dv[hit]).mean()) if c else 0.0
                scen.append(dict(id=f"L{len(scen)+1:03d}", cell=f"T{ti+1}S{si+1}", trigger=tn, speed=sn, headway=hn,
                                 s_trig=ts, s_speed=ss, s_hw=hs, runs=N_RUNS, coll=c, inj=inj,
                                 dv_mean=float(dv[hit].mean()) if c else 0.0))
    return cells, scen


def bayes_quantile(cells, scen, q=0.95, draws=200_000, seed=7):
    """Posterior of total risk: Jeffreys Gamma for HB rates, Jeffreys Beta for collision probs; injury mean fixed."""
    rng = np.random.default_rng(seed)
    lam = {c["cell"]: rng.gamma(c["k"] + 0.5, 1.0 / c["hours"], draws) for c in cells}
    R = np.zeros(draws)
    for s in scen:
        p = rng.beta(s["coll"] + 0.5, s["runs"] - s["coll"] + 0.5, draws)
        R += s["s_trig"] * s["s_speed"] * s["s_hw"] * lam[s["cell"]] * p * s["inj"]
    return float(np.quantile(R, q)), float(R.mean())


if __name__ == "__main__":
    cells, scen = generate()
    point = sum(s["s_trig"] * s["s_speed"] * s["s_hw"] * (next(c for c in cells if c["cell"] == s["cell"])["k"] /
                next(c for c in cells if c["cell"] == s["cell"])["hours"]) * s["coll"] / s["runs"] * s["inj"] for s in scen)
    print("k per cell:", [c["k"] for c in cells])
    print("collision rates:", [round(s["coll"] / s["runs"], 3) for s in scen[:10]])
    print("point R =", point)
    print("bayes 95% / mean =", bayes_quantile(cells, scen))
