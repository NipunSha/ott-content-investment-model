import numpy as np
import pytest
from ott_model import load_params, load_scenarios, apply_scenario, evaluate, breakeven, OPTIONS
from ott_model.model import cashflows, indifference
from ott_model.params import load_register

P = load_params()


def test_register_ranges_are_ordered_and_typed():
    for r in load_register():
        lo, b, hi = float(r["low"]), float(r["base"]), float(r["high"])
        assert lo <= b <= hi, r["id"]
        assert r["type"] in {"ASSUMPTION", "CASE_DEFINITION", "OBSERVED", "CALCULATED"}


def test_scenarios_only_touch_known_parameters():
    for ov in load_scenarios().values():
        apply_scenario(P, ov)
    with pytest.raises(KeyError):
        apply_scenario(P, {"not_a_parameter": 1})


@pytest.mark.parametrize("o", OPTIONS)
def test_no_audience_means_npv_equals_minus_cost(o):
    p = {**P, "gross_adds": 0, "engaged_share_of_base": 0, "avod_viewers": 0, "secondary_licensing_pct": 0, "residual_rights_value_pct": 0}
    r = evaluate(o, p)
    assert r["pv_contribution_cr"] == pytest.approx(0)
    assert r["npv_cr"] == pytest.approx(-r["pv_cost_cr"])
    assert r["payback_month_from_launch"] is None


def test_commission_cost_adds_up_by_hand():
    r = evaluate("commission", P)
    prod = P["episodes"] * P["prod_cost_per_episode_cr"]
    by_hand = prod * (1 + P["overrun_pct"]) * (1 + P["producer_fee_pct"]) + prod * P["marketing_pct_of_production"] \
        + P["episodes"] * P["dub_languages"] * P["dub_cost_per_episode_lang_cr"]
    cf = cashflows("commission", P)
    assert cf["total_cost"].sum() - cf["cost"]["delivery"].sum() == pytest.approx(by_hand)


def test_cohort_matches_closed_form():
    # one cohort of subscribers decays geometrically: sum of survivors over the horizon
    p = {**P, "engaged_share_of_base": 0, "avod_viewers": 0, "secondary_licensing_pct": 0, "residual_rights_value_pct": 0,
         "discount_rate_annual": 0.0, "delivery_cost_per_hour_inr": 0}
    cf = cashflows("commission", p)
    c, H, unit = P["monthly_churn"], int(P["horizon_months"]), P["arpu_month"] * P["contribution_margin_sub"] / 1e7
    sub_months = sum(share * (1 - (1 - c) ** (H - lag)) / c for lag, share in enumerate((0.6, 0.25, 0.15)))
    assert cf["revenue"]["sub_acquisition"].sum() == pytest.approx(P["gross_adds"] * sub_months * unit)


def test_advertising_is_independent_of_paying_subscribers():
    # guards against double counting: ad revenue comes only from non-paying ad-tier viewers
    a = evaluate("commission", P)["pv_advertising_cr"]
    b = evaluate("commission", {**P, "gross_adds": P["gross_adds"] * 3, "existing_base_subs": 0})["pv_advertising_cr"]
    assert a == pytest.approx(b)


def test_acquire_has_no_production_risk_and_stops_at_licence_end():
    assert evaluate("acquire", P)["pv_cost_overrun_cr"] == 0
    assert evaluate("acquire", {**P, "overrun_pct": 0.3})["npv_cr"] == pytest.approx(evaluate("acquire", P)["npv_cr"])
    cf = cashflows("acquire", P)
    after = cf["months_since_launch"] >= P["licence_term_months"]
    assert cf["total_revenue"][after].sum() == pytest.approx(0)


def test_coproduction_shares_cost_and_rights():
    full = cashflows("commission", P); co = cashflows("coproduce", P)
    assert co["cost"]["production_or_licence"].sum() == pytest.approx(full["cost"]["production_or_licence"].sum() * P["platform_cost_share"])
    assert co["revenue"]["secondary_licensing"].sum() == pytest.approx(full["revenue"]["secondary_licensing"].sum() * P["platform_secondary_share"])
    assert co["cost"]["producer_fee"].sum() == 0


@pytest.mark.parametrize("o", OPTIONS)
def test_npv_increases_with_adds_and_breakeven_is_a_root(o):
    assert evaluate(o, {**P, "gross_adds": 400000})["npv_cr"] > evaluate(o, P)["npv_cr"]
    be = breakeven(o, P, "gross_adds", 0, 5_000_000)
    assert be is not None and abs(evaluate(o, {**P, "gross_adds": be})["npv_cr"]) < 1e-6


def test_discounting_lowers_value_of_later_cash():
    cf = cashflows("commission", P)
    assert cf["discount_factor"][0] == 1 and cf["discount_factor"][12] == pytest.approx(1 / (1 + P["discount_rate_annual"]))


def test_indifference_point_equalises_options():
    v = indifference("commission", "coproduce", P, "residual_rights_value_pct", 0, 5)
    q = {**P, "residual_rights_value_pct": v}
    assert evaluate("commission", q)["npv_cr"] == pytest.approx(evaluate("coproduce", q)["npv_cr"], abs=1e-6)


def test_monte_carlo_is_reproducible_and_mean_one_performance():
    from ott_model.analysis import monte_carlo
    a, b = monte_carlo(n=400, seed=1), monte_carlo(n=400, seed=1)
    assert a.equals(b)
    assert monte_carlo(n=4000, seed=2)["perf_original"].mean() == pytest.approx(1.0, abs=0.06)


def test_payback_and_delivery_and_rights_timing():
    rich = {**P, "gross_adds": 2_000_000}
    r = evaluate("acquire", rich)
    cf = cashflows("acquire", rich)
    cum = np.cumsum(cf["net"])
    m = r["payback_month_from_decision"]
    assert m >= cf["launch"] and cum[m] >= 0 and (m == cf["launch"] or cum[m - 1] < 0)
    hours = (P["gross_adds"] + P["existing_base_subs"] * P["engaged_share_of_base"]) * P["hours_per_paid_viewer"] + P["avod_viewers"] * P["hours_per_avod_viewer"]
    c = cashflows("commission", P)
    assert c["cost"]["delivery"].sum() == pytest.approx(hours * P["delivery_cost_per_hour_inr"] / 1e7)
    L = int(P["production_months"])
    assert np.flatnonzero(c["revenue"]["secondary_licensing"]).tolist() == [L + int(P["secondary_month_after_launch"])]
    assert np.flatnonzero(c["revenue"]["residual_rights"]).tolist() == [L + int(P["horizon_months"]) - 1]


def test_zero_production_months_is_rejected():
    with pytest.raises(ValueError):
        evaluate("commission", {**P, "production_months": 0})


def test_tornado_and_grid_are_consistent_with_evaluate():
    from ott_model.analysis import tornado, decision_grid
    t = tornado().iloc[0]
    assert t.npv_at_high_cr == pytest.approx(evaluate(t.option, {**P, t.parameter: t.high_value})["npv_cr"])
    g = decision_grid(nx=3, ny=3).iloc[4]
    assert g.npv_coproduce_cr == pytest.approx(evaluate("coproduce", {**P, "gross_adds": g.gross_adds, "prod_cost_per_episode_cr": g.prod_cost_per_episode_cr})["npv_cr"])
