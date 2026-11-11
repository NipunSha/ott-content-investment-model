# Data dictionary (tableau/data)
All money in INR crore. `option` is commission / acquire / coproduce; `scenario` is base / downside / upside.

| File | Grain | Key fields |
|---|---|---|
| summary_by_option_scenario.csv | option x scenario | npv_cr, pv_cost_cr, pv_contribution_cr, roi_pv, payback_month_from_launch (blank = not within horizon), peak_cash_exposure_cr, pv_<stream>_cr, pv_cost_<line>_cr |
| pv_breakdown_long.csv | option x scenario x line | kind (contribution/cost), line, pv_cr (costs negative) |
| cashflows_monthly.csv | option x scenario x month | month_from_decision, months_since_launch, rev_*_cr, cost_*_cr, net_cash_cr, cumulative_net_cash_cr |
| sensitivity_tornado.csv | option x parameter | low_value, high_value, base_npv_cr, npv_at_low_cr, npv_at_high_cr, swing_cr |
| breakeven.csv | option x scenario x parameter | current_value, breakeven_value (blank = no break-even in search range), breakeven_effective_adds |
| indifference_points.csv | option pair x parameter | indifference_value, a_better_when |
| decision_grid_adds_vs_cost.csv / _vs_rights.csv | grid cell | two driver values, npv_<option>_cr, best_option |
| npv_by_cost_per_episode.csv | cost level x option | prod_cost_per_episode_cr, npv_cr |
| montecarlo_summary.csv | option | mean, median, sd, percentiles, prob_npv_positive, cvar05_npv_cr, prob_best_option |
| montecarlo_draws_sample.csv | draw x option (first 5,000 draws) | npv_cr, perf_original, perf_acquired |
| montecarlo_sigma_robustness.csv | option x sigma setting | as summary |

Parameters are defined in `docs/assumptions_register.csv` (columns: id, group, parameter, unit, low, base, high, type, basis, source_id). `type` is ASSUMPTION or CASE_DEFINITION; no parameter is an observed market quote.
