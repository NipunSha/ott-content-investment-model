"""Scenario, sensitivity, break-even and Monte Carlo analysis built on model.evaluate."""
import numpy as np
import pandas as pd
from .model import evaluate, evaluate_all, breakeven, indifference, cashflows, OPTIONS, STREAMS, COSTS, _structure
from .params import load_params, load_ranges, load_scenarios, apply_scenario, load_register

FIXED_TYPES = {"CASE_DEFINITION"}
BREAKEVEN_BOUNDS = {  # search ranges for break-even solving (wider than register ranges on purpose)
    "gross_adds": (0, 5_000_000), "arpu_month": (1, 1000), "prod_cost_per_episode_cr": (0.01, 20),
    "licence_fee_pct_of_prod_cost": (0.01, 3), "monthly_churn": (0.005, 0.5), "avod_viewers": (0, 100_000_000),
}


def scenario_table():
    base = load_params()
    rows = []
    for name, ov in load_scenarios().items():
        p = apply_scenario(base, ov)
        for o in OPTIONS:
            rows.append({"scenario": name, **evaluate(o, p)})
    return pd.DataFrame(rows)


def cashflow_table():
    base = load_params()
    rows = []
    for name, ov in load_scenarios().items():
        p = apply_scenario(base, ov)
        for o in OPTIONS:
            cf = cashflows(o, p)
            cum = np.cumsum(cf["net"])
            for t in cf["month"]:
                r = {"scenario": name, "option": o, "month_from_decision": int(t),
                     "months_since_launch": int(cf["months_since_launch"][t]),
                     "net_cash_cr": cf["net"][t], "cumulative_net_cash_cr": cum[t],
                     "discount_factor": cf["discount_factor"][t]}
                r.update({f"rev_{s}_cr": cf["revenue"][s][t] for s in STREAMS})
                r.update({f"cost_{c}_cr": cf["cost"][c][t] for c in COSTS})
                rows.append(r)
    return pd.DataFrame(rows)


def tornado():
    """One-at-a-time sensitivity: move each uncertain driver to its register low and high."""
    base, ranges = load_params(), load_ranges()
    types = {r["id"]: r["type"] for r in load_register()}
    rows = []
    for o in OPTIONS:
        b = evaluate(o, base)["npv_cr"]
        for k, (lo, _, hi) in ranges.items():
            if types[k] in FIXED_TYPES or lo == hi:
                continue
            n_lo = evaluate(o, {**base, k: lo})["npv_cr"]
            n_hi = evaluate(o, {**base, k: hi})["npv_cr"]
            if n_lo == b and n_hi == b:
                continue  # parameter does not affect this option
            rows.append({"option": o, "parameter": k, "low_value": lo, "high_value": hi, "base_npv_cr": b,
                         "npv_at_low_cr": n_lo, "npv_at_high_cr": n_hi, "swing_cr": abs(n_hi - n_lo)})
    return pd.DataFrame(rows).sort_values(["option", "swing_cr"], ascending=[True, False])


def breakeven_table():
    base = load_params()
    rows = []
    for name, ov in load_scenarios().items():
        p = apply_scenario(base, ov)
        for o in OPTIONS:
            for k, (lo, hi) in BREAKEVEN_BOUNDS.items():
                if k == "licence_fee_pct_of_prod_cost" and o != "acquire":
                    continue
                v = breakeven(o, p, k, lo, hi)
                row = {"scenario": name, "option": o, "parameter": k, "current_value": p[k],
                       "breakeven_value": v, "breakeven_over_current": (v / p[k]) if v else None}
                if k == "gross_adds":  # express in the option's own subscribers (after its audience multiplier)
                    m = _structure(o, p)["aud"]
                    row.update(current_effective_adds=p[k] * m, breakeven_effective_adds=v * m if v else None)
                rows.append(row)
    return pd.DataFrame(rows)


def indifference_table():
    """Parameter values at which pairs of options are equally attractive (base case otherwise)."""
    base = load_params()
    checks = [("commission", "coproduce", "residual_rights_value_pct", 0, 5),
              ("commission", "coproduce", "post_window_factor", 0, 1),
              ("commission", "coproduce", "platform_cost_share", 0.05, 1),
              ("commission", "coproduce", "title_performance", 0.05, 20),
              ("commission", "acquire", "title_performance", 0.05, 20),
              ("coproduce", "acquire", "title_performance", 0.05, 20),
              ("coproduce", "acquire", "acq_audience_multiplier", 0.05, 2),
              ("commission", "acquire", "licence_fee_pct_of_prod_cost", 0.01, 3)]
    rows = []
    for a, b, k, lo, hi in checks:
        v = indifference(a, b, base, k, lo, hi)
        rows.append({"option_a": a, "option_b": b, "parameter": k, "base_value": base[k], "indifference_value": v,
                     "a_better_when": None if v is None else ("above" if evaluate(a, {**base, k: hi})["npv_cr"] > evaluate(b, {**base, k: hi})["npv_cr"] else "below")})
    return pd.DataFrame(rows)


def decision_grid(x="gross_adds", y="prod_cost_per_episode_cr", nx=25, ny=25, extra=None):
    """Which option has the highest NPV across a grid of two drivers (others at base)."""
    base, ranges = {**load_params(), **(extra or {})}, load_ranges()
    xs = np.linspace(ranges[x][0] * 0.5, ranges[x][2] * 1.2, nx)
    ys = np.linspace(ranges[y][0], ranges[y][2], ny)
    rows = []
    for xv in xs:
        for yv in ys:
            res = {o: evaluate(o, {**base, x: xv, y: yv})["npv_cr"] for o in OPTIONS}
            best = max(res, key=res.get)
            rows.append({x: xv, y: yv, **{f"npv_{o}_cr": v for o, v in res.items()},
                         "best_option": best if res[best] > 0 else "none (all NPV < 0)", "best_npv_cr": res[best]})
    return pd.DataFrame(rows)


def monte_carlo(n=20000, seed=7, sigma_original=0.75, sigma_acquired=0.35):
    """Simulate NPV for the three options under shared market draws.

    - Uncertain register parameters: triangular(low, base, high).
    - Title performance: a lognormal multiplier with mean 1 applied to all audience drivers.
      Commission and co-production share one draw (same title); the acquired title has a
      separate, tighter draw because its track record is observable before the deal.
    Distribution choices are assumptions; see docs/methodology.md.
    """
    rng = np.random.default_rng(seed)
    base, ranges = load_params(), load_ranges()
    types = {r["id"]: r["type"] for r in load_register()}
    # Audience drivers stay at base: the performance multiplier is their only source of variance
    # (drawing both would count audience uncertainty twice). The discount rate is a policy choice, not a risk.
    held = {"gross_adds", "engaged_share_of_base", "avod_viewers", "discount_rate_annual"}
    uncertain = [k for k, (lo, b, hi) in ranges.items() if types[k] not in FIXED_TYPES and lo < hi and k not in held]
    draws = {k: rng.triangular(ranges[k][0], ranges[k][1], ranges[k][2], n) for k in uncertain}
    perf = {"orig": rng.lognormal(-sigma_original ** 2 / 2, sigma_original, n),
            "acq": rng.lognormal(-sigma_acquired ** 2 / 2, sigma_acquired, n)}
    rows = []
    for i in range(n):
        p = {**base, **{k: draws[k][i] for k in uncertain}}
        rec = {"draw": i, "perf_original": perf["orig"][i], "perf_acquired": perf["acq"][i]}
        for o in OPTIONS:
            m = perf["acq"][i] if o == "acquire" else perf["orig"][i]
            rec[o] = evaluate(o, {**p, "title_performance": m})["npv_cr"]
        rows.append(rec)
    return pd.DataFrame(rows)


def cost_curve(costs=None):
    """NPV of each option across production cost per episode (other inputs at base)."""
    base = load_params()
    costs = costs if costs is not None else np.round(np.arange(0.3, 3.01, 0.1), 2)
    return pd.DataFrame([{"prod_cost_per_episode_cr": c, "option": o, "npv_cr": evaluate(o, {**base, "prod_cost_per_episode_cr": c})["npv_cr"]} for c in costs for o in OPTIONS])


def mc_summary(mc):
    rows = []
    best = mc[list(OPTIONS)].idxmax(axis=1)
    for o in OPTIONS:
        x = mc[o].to_numpy()
        q5 = np.quantile(x, 0.05)
        rows.append({"option": o, "mean_npv_cr": x.mean(), "median_npv_cr": np.median(x), "sd_npv_cr": x.std(ddof=1),
                     "p05_npv_cr": q5, "p25_npv_cr": np.quantile(x, 0.25), "p75_npv_cr": np.quantile(x, 0.75),
                     "p95_npv_cr": np.quantile(x, 0.95), "prob_npv_positive": (x > 0).mean(),
                     "cvar05_npv_cr": x[x <= q5].mean(), "prob_best_option": (best == o).mean(),
                     "mean_over_sd": x.mean() / x.std(ddof=1)})
    return pd.DataFrame(rows)
