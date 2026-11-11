"""Reproduce every output: Excel model, Tableau-ready CSVs, report figures.
Usage: python scripts/run_all.py"""
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from ott_model import analysis as a
from ott_model.excel_export import build
from ott_model.model import OPTIONS, STREAMS, COSTS

OUT = ROOT / "tableau" / "data"; FIG = ROOT / "reports" / "figures"
OUT.mkdir(parents=True, exist_ok=True); FIG.mkdir(parents=True, exist_ok=True)
COL = {"commission": "#1F3A5F", "acquire": "#C8553D", "coproduce": "#2A9D8F"}

def main():
    build()
    st = a.scenario_table(); st.to_csv(OUT / "summary_by_option_scenario.csv", index=False)
    # long cost / contribution breakdown for stacked bars
    long = []
    for r in st.to_dict("records"):
        for s in STREAMS: long.append({"scenario": r["scenario"], "option": r["option"], "kind": "contribution", "line": s, "pv_cr": r[f"pv_{s}_cr"]})
        for c in COSTS: long.append({"scenario": r["scenario"], "option": r["option"], "kind": "cost", "line": c, "pv_cr": -r[f"pv_cost_{c}_cr"]})
    pd.DataFrame(long).to_csv(OUT / "pv_breakdown_long.csv", index=False)
    a.cashflow_table().to_csv(OUT / "cashflows_monthly.csv", index=False)
    tor = a.tornado(); tor.to_csv(OUT / "sensitivity_tornado.csv", index=False)
    be = a.breakeven_table(); be.to_csv(OUT / "breakeven.csv", index=False)
    ind = a.indifference_table(); ind.to_csv(OUT / "indifference_points.csv", index=False)
    g1 = a.decision_grid("gross_adds", "prod_cost_per_episode_cr"); g1.to_csv(OUT / "decision_grid_adds_vs_cost.csv", index=False)
    g2 = a.decision_grid("gross_adds", "residual_rights_value_pct"); g2.to_csv(OUT / "decision_grid_adds_vs_rights.csv", index=False)
    mc = a.monte_carlo(); ms = a.mc_summary(mc); ms.to_csv(OUT / "montecarlo_summary.csv", index=False)
    mc.head(5000).melt(id_vars=["draw", "perf_original", "perf_acquired"], value_vars=list(OPTIONS), var_name="option", value_name="npv_cr").to_csv(OUT / "montecarlo_draws_sample.csv", index=False)
    cc = a.cost_curve(); cc.to_csv(OUT / "npv_by_cost_per_episode.csv", index=False)
    # Monte Carlo robustness to the performance-spread assumption
    rob = []
    for so, sa in [(0.5, 0.25), (0.75, 0.35), (1.0, 0.5)]:
        m = a.mc_summary(a.monte_carlo(sigma_original=so, sigma_acquired=sa)); m["sigma_original"] = so; m["sigma_acquired"] = sa; rob.append(m)
    rob = pd.concat(rob); rob.to_csv(OUT / "montecarlo_sigma_robustness.csv", index=False)

    # static report figures (matplotlib; these are not Tableau dashboards)
    fig, ax = plt.subplots(figsize=(7, 3.6))
    piv = st.pivot(index="scenario", columns="option", values="npv_cr").loc[["downside", "base", "upside"], list(OPTIONS)]
    piv.plot.bar(ax=ax, color=[COL[o] for o in OPTIONS], width=0.75); ax.axhline(0, color="k", lw=0.8)
    ax.set_ylabel("NPV, INR crore"); ax.set_xlabel(""); ax.set_title("NPV by deal structure and scenario"); plt.xticks(rotation=0); fig.tight_layout(); fig.savefig(FIG / "npv_by_scenario.png", dpi=160); plt.close(fig)
    fig, axes = plt.subplots(1, 3, figsize=(12, 4), sharex=False)
    for ax, o in zip(axes, OPTIONS):
        t = tor[tor.option == o].head(7).iloc[::-1]
        ax.barh(t.parameter, t.npv_at_high_cr - t.base_npv_cr, left=t.base_npv_cr, color=COL[o]); ax.barh(t.parameter, t.npv_at_low_cr - t.base_npv_cr, left=t.base_npv_cr, color="#B0B7C3")
        ax.axvline(0, color="k", lw=0.8); ax.set_title(o); ax.set_xlabel("NPV, INR crore"); ax.tick_params(labelsize=7)
    fig.suptitle("Sensitivity: NPV at low (grey) and high (colour) value of each driver"); fig.tight_layout(); fig.savefig(FIG / "tornado.png", dpi=160); plt.close(fig)
    fig, ax = plt.subplots(figsize=(7, 3.6))
    for o in OPTIONS: ax.hist(mc[o].clip(-25, 40), bins=80, alpha=0.55, color=COL[o], label=o)
    ax.axvline(0, color="k", lw=0.8); ax.set_xlabel("NPV, INR crore (clipped at -25 / +40)"); ax.set_ylabel("simulated outcomes"); ax.legend(); ax.set_title("Monte Carlo NPV distribution (20,000 draws)"); fig.tight_layout(); fig.savefig(FIG / "montecarlo.png", dpi=160); plt.close(fig)
    fig, ax = plt.subplots(figsize=(6.4, 4.2))
    cats = ["commission", "acquire", "coproduce", "none (all NPV < 0)"]; cm = {**COL, "none (all NPV < 0)": "#DDDDDD"}
    for c in cats:
        d = g1[g1.best_option == c]; ax.scatter(d.gross_adds / 1000, d.prod_cost_per_episode_cr, s=38, marker="s", color=cm[c], label=c)
    ax.set_xlabel("Incremental gross adds of the original ('000)"); ax.set_ylabel("Production cost per episode, INR crore"); ax.legend(fontsize=7, loc="upper left"); ax.set_title("Highest-NPV structure (other inputs at base)"); fig.tight_layout(); fig.savefig(FIG / "decision_map.png", dpi=160); plt.close(fig)

    pd.set_option("display.width", 220); pd.set_option("display.max_columns", 40)
    print(st[["scenario", "option", "npv_cr", "pv_cost_cr", "pv_contribution_cr", "roi_pv", "payback_month_from_launch", "peak_cash_exposure_cr"]].round(2).to_string(index=False))
    print(be[be.scenario == "base"].round(3).to_string(index=False))
    print(ind.round(3).to_string(index=False)); print(ms.round(3).to_string(index=False))
    print(rob[["sigma_original", "option", "mean_npv_cr", "median_npv_cr", "prob_npv_positive", "prob_best_option", "cvar05_npv_cr"]].round(2).to_string(index=False))
    print(tor.groupby("option").head(5)[["option", "parameter", "npv_at_low_cr", "npv_at_high_cr", "swing_cr"]].round(2).to_string(index=False))
    print(cc[cc.prod_cost_per_episode_cr.isin([0.5, 1.0, 1.5, 2.0])].pivot(index="prod_cost_per_episode_cr", columns="option", values="npv_cr").round(2).to_string())
    print(g1.best_option.value_counts(normalize=True).round(3).to_dict(), g2.best_option.value_counts(normalize=True).round(3).to_dict())

if __name__ == "__main__":
    main()
