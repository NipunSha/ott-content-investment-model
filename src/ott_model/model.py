"""Monthly cash-flow model for one content investment under three deal structures.

Conventions
- Money is in INR crore (1 crore = 1e7 INR). Month 0 is the decision date.
- Only *incremental* effects of the title are counted: subscribers who join because of it,
  existing subscribers who would otherwise have churned, and ad impressions from
  non-paying ad-tier viewers. Advertising shown to paying subscribers is treated as part
  of blended ARPU, so it is not counted again.
- Subscriber cohorts follow active[t] = active[t-1] * (1 - churn) + new[t].
"""
import numpy as np
from scipy.optimize import brentq
from .params import ADDS_CURVE

CRORE = 1e7
OPTIONS = ("commission", "acquire", "coproduce")
STREAMS = ("sub_acquisition", "sub_retention", "advertising", "secondary_licensing", "residual_rights")
COSTS = ("production_or_licence", "producer_fee", "overrun", "marketing", "localisation", "delivery")


def _structure(option, p):
    """Translate deal structure into launch month, audience scale and rights window."""
    H = int(p["horizon_months"])
    if option == "commission":
        return dict(launch=int(p["production_months"]), aud=1.0, window=H, post=1.0)
    if option == "coproduce":
        return dict(launch=int(p["production_months"]), aud=p["copro_audience_multiplier"],
                    window=int(p["exclusive_window_months"]), post=p["post_window_factor"])
    if option == "acquire":
        return dict(launch=int(p["acq_launch_month"]), aud=p["acq_audience_multiplier"],
                    window=int(p["licence_term_months"]), post=0.0)
    raise ValueError(option)


def cashflows(option, p):
    """Return dict of monthly arrays (INR crore) for revenue streams, cost lines and helpers."""
    s = _structure(option, p)
    L, H = s["launch"], int(p["horizon_months"])
    if L < 1 or H < 1:
        raise ValueError("launch month and horizon must be at least 1 month")
    T = L + H  # months 0..T-1 ; launch month is index L
    k = np.arange(T) - L  # months since launch
    live = k >= 0
    window = np.where(k < s["window"], 1.0, s["post"]) * live

    curve = np.zeros(T)
    curve[L:L + len(ADDS_CURVE)] = ADDS_CURVE

    churn = p["monthly_churn"]
    perf = p.get("title_performance", 1.0)
    aud = s["aud"] * perf  # audience scale: deal structure x title performance
    new_adds = p["gross_adds"] * aud * curve
    eff = (k >= 0) & (k < int(p["retention_effect_months"]))
    engaged = p["existing_base_subs"] * min(p["engaged_share_of_base"] * aud, 1.0)
    new_retained = engaged * p["churn_reduction_pp"] * eff

    def cohort(new):
        active = np.zeros(T)
        for t in range(T):
            active[t] = (active[t - 1] * (1 - churn) if t else 0.0) + new[t]
        return active

    unit = p["arpu_month"] * p["contribution_margin_sub"] / CRORE
    rev = {
        "sub_acquisition": cohort(new_adds) * unit * window,
        "sub_retention": cohort(new_retained) * unit * window,
    }
    avod_hours = p["avod_viewers"] * aud * p["hours_per_avod_viewer"] * curve
    impressions = avod_hours * p["ad_impressions_per_hour"] * p["ad_fill_rate"]
    rev["advertising"] = impressions * p["avod_cpm_inr"] / 1000 * p["ad_contribution_margin"] / CRORE

    prod = p["episodes"] * p["prod_cost_per_episode_cr"]
    sec = np.zeros(T)
    residual = np.zeros(T)
    m_sec = L + int(p["secondary_month_after_launch"])
    cost = {c: np.zeros(T) for c in COSTS}
    spend = np.zeros(T)
    if option in ("commission", "coproduce"):
        spend[1:L + 1] = 1.0 / L  # production cash spread evenly over months 1..L
        share = 1.0 if option == "commission" else p["platform_cost_share"]
        cost["production_or_licence"] = prod * share * spend
        cost["overrun"] = prod * share * p["overrun_pct"] * spend
        if option == "commission":
            cost["producer_fee"] = prod * (1 + p["overrun_pct"]) * p["producer_fee_pct"] * spend
        mkt = prod * p["marketing_pct_of_production"]
        cost["marketing"][L - 1] += mkt / 2
        cost["marketing"][L] += mkt / 2
        cost["localisation"][L - 1] = p["episodes"] * p["dub_languages"] * p["dub_cost_per_episode_lang_cr"]
        rights_share = 1.0 if option == "commission" else p["platform_secondary_share"]
        if m_sec < T:
            sec[m_sec] = prod * p["secondary_licensing_pct"] * perf * rights_share
        residual[T - 1] = prod * p["residual_rights_value_pct"] * perf * rights_share
    else:
        fee = prod * p["licence_fee_pct_of_prod_cost"]
        cost["production_or_licence"][L] = fee
        cost["marketing"][L] = fee * p["acq_marketing_pct_of_fee"]
        cost["localisation"][L] = p["episodes"] * p["acq_dub_languages"] * p["dub_cost_per_episode_lang_cr"]
    rev["secondary_licensing"] = sec
    rev["residual_rights"] = residual

    paid_hours = (p["gross_adds"] * aud + engaged) * p["hours_per_paid_viewer"] * curve
    cost["delivery"] = (paid_hours + avod_hours) * p["delivery_cost_per_hour_inr"] / CRORE

    r_m = (1 + p["discount_rate_annual"]) ** (1 / 12) - 1
    df = (1 + r_m) ** -np.arange(T)
    total_rev = sum(rev.values())
    total_cost = sum(cost.values())
    return dict(month=np.arange(T), months_since_launch=k, revenue=rev, cost=cost,
                total_revenue=total_rev, total_cost=total_cost, net=total_rev - total_cost,
                discount_factor=df, launch=L)


def evaluate(option, p):
    cf = cashflows(option, p)
    df, net = cf["discount_factor"], cf["net"]
    cum = np.cumsum(net)
    idx = np.where(cum >= 0)[0]
    # payback only counts once the launch has happened and cumulative cash has turned positive
    idx = idx[idx >= cf["launch"]]
    pv_cost = float((cf["total_cost"] * df).sum())
    pv_rev = float((cf["total_revenue"] * df).sum())
    out = {
        "option": option,
        "npv_cr": pv_rev - pv_cost,
        "pv_cost_cr": pv_cost,
        "pv_contribution_cr": pv_rev,
        "undiscounted_cost_cr": float(cf["total_cost"].sum()),
        "undiscounted_contribution_cr": float(cf["total_revenue"].sum()),
        "roi_pv": (pv_rev - pv_cost) / pv_cost,
        "payback_month_from_decision": int(idx[0]) if len(idx) else None,
        "payback_month_from_launch": int(idx[0] - cf["launch"]) if len(idx) else None,
        "peak_cash_exposure_cr": float(-cum.min()),
        "launch_month": cf["launch"],
    }
    for s in STREAMS:
        out[f"pv_{s}_cr"] = float((cf["revenue"][s] * df).sum())
    for c in COSTS:
        out[f"pv_cost_{c}_cr"] = float((cf["cost"][c] * df).sum())
    return out


def evaluate_all(p):
    return {o: evaluate(o, p) for o in OPTIONS}


def breakeven(option, p, param, lo, hi):
    """Value of `param` in [lo, hi] at which NPV = 0, or None if NPV does not change sign."""
    f = lambda x: evaluate(option, {**p, param: x})["npv_cr"]
    flo, fhi = f(lo), f(hi)
    if flo == 0:
        return lo
    if flo * fhi > 0:
        return None
    return float(brentq(f, lo, hi, xtol=1e-9))


def indifference(option_a, option_b, p, param, lo, hi):
    """Value of `param` at which the two options have equal NPV, or None."""
    f = lambda x: evaluate(option_a, {**p, param: x})["npv_cr"] - evaluate(option_b, {**p, param: x})["npv_cr"]
    flo, fhi = f(lo), f(hi)
    if flo * fhi > 0:
        return None
    return float(brentq(f, lo, hi, xtol=1e-9))
