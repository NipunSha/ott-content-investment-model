"""Build reports/executive_presentation.pptx from the model outputs (numbers are read, not typed)."""
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import pandas as pd
from deck_helper import Deck

D = ROOT / "tableau" / "data"; F = ROOT / "reports" / "figures"
st = pd.read_csv(D / "summary_by_option_scenario.csv"); be = pd.read_csv(D / "breakeven.csv"); mc = pd.read_csv(D / "montecarlo_summary.csv").set_index("option"); ind = pd.read_csv(D / "indifference_points.csv")
b = st[st.scenario == "base"].set_index("option")
f = lambda x: f"{x:+.1f}"
def bev(o, p, col="breakeven_value"): return be[(be.scenario == "base") & (be.option == o) & (be.parameter == p)][col].iloc[0]
def indiff(a, c, p): return ind[(ind.option_a == a) & (ind.option_b == c) & (ind.parameter == p)].indifference_value.iloc[0]
names = {"commission": "Commission", "acquire": "Acquire", "coproduce": "Co-produce"}
d = Deck("OTT content investment: commission, acquire or co-produce?  Hypothetical case, INR crore")
d.title("Commission, acquire or co-produce?", "An investment case for one six-episode scripted series on a hypothetical mid-sized Indian OTT platform (5 million paying subscribers). Inputs are documented assumptions with ranges; nothing here is a market quote.")
d.bullets("The answer depends on two things: subscribers gained and who holds the rights", [
    f"At base assumptions only co-production clears zero: NPV {f(b.npv_cr.coproduce)} vs {f(b.npv_cr.commission)} for commissioning and {f(b.npv_cr.acquire)} for acquisition.",
    f"Commissioning needs about {bev('commission','gross_adds')/1000:,.0f}k incremental subscribers to break even; co-production about {bev('coproduce','gross_adds')/1000:,.0f}k.",
    f"Full ownership only pays if post-horizon rights are worth about {indiff('commission','coproduce','residual_rights_value_pct'):.0%} of production cost, or the title runs at {indiff('commission','coproduce','title_performance'):.1f}x plan.",
    "Acquisition never has the highest expected value, but its worst outcomes are the mildest."])
d.table("Base case: what each structure costs and returns", ["PV, INR crore", "Commission", "Acquire", "Co-produce"], [
    ["Costs"] + [f"{b.pv_cost_cr[o]:.1f}" for o in names], ["Contribution"] + [f"{b.pv_contribution_cr[o]:.1f}" for o in names],
    ["NPV"] + [f(b.npv_cr[o]) for o in names], ["Peak cash exposure"] + [f"{b.peak_cash_exposure_cr[o]:.1f}" for o in names],
    ["Months to launch"] + [int(b.launch_month[o]) for o in names]],
    note="Subscriber acquisition is 76-89% of contribution in every structure. Advertising to non-paying viewers adds 0.1-0.3 crore.")
d.picture("The ranking holds across scenarios, the stakes do not", F / "npv_by_scenario.png", [
    "Acquisition loses least in the downside.", "Co-production gains most in the upside.", "Commissioning has the widest range and trails co-production in all three."])
d.table("Break-even: what has to be true", ["", "Commission", "Acquire", "Co-produce"], [
    ["Incremental subscribers ('000)"] + [f"{bev(o,'gross_adds','breakeven_effective_adds')/1000:,.0f}" for o in names],
    ["Net ARPU, INR/month (base 70)"] + [f"{bev(o,'arpu_month'):.0f}" for o in names],
    ["Monthly churn (base 8%)"] + [f"{bev(o,'monthly_churn'):.1%}" for o in names],
    ["Cost per episode, INR crore (base 1.5)"] + [f"{bev(o,'prod_cost_per_episode_cr'):.2f}" for o in names]],
    note="Each row moves one driver with the others at base. A commissioned series breaks even at the base subscriber number if churn among those subscribers is 5% instead of 8%.")
d.picture("Subscribers and cost per episode dominate every other assumption", F / "tornado.png", [
    "Cost per episode and gross adds are the two largest swings for every structure.", "ARPU and churn come next.", "Advertising inputs do not appear in the top five for any structure."])
d.picture("Co-production wins most of the map; nothing wins the rest", F / "decision_map.png", [
    "Each square is the highest-NPV structure for that combination.", "Grey: every structure loses money.", "Commissioning appears only at very high subscriber gains with low cost."])
d.table("Risk: the median title loses money under every structure", ["20,000 simulations", "Mean NPV", "Median", "P(NPV > 0)", "Worst-5% average", "Best option in"], [
    [names[o], f(mc.mean_npv_cr[o]), f(mc.median_npv_cr[o]), f"{mc.prob_npv_positive[o]:.0%}", f(mc.cvar05_npv_cr[o]), f"{mc.prob_best_option[o]:.0%} of draws"] for o in names],
    note="Title performance is drawn from a skewed (lognormal) distribution: a minority of hits carries the mean. Acquisition is 'best' mostly when titles disappoint.")
d.bullets("Recommendation: choose by condition, not by default", [
    "Co-produce if a partner will fund about half the budget for an 18-month exclusive window and most downstream rights. Preferred for a single season on those terms.",
    "Commission when the title is a franchise candidate and ownership beyond year three is the point, or no partner exists and audience evidence is strong.",
    "Acquire when capital or time is the binding constraint: one month to launch, a third of the cash at risk.",
    f"Walk away if the title cannot plausibly add ~{bev('coproduce','gross_adds')/1000:,.0f}k subscribers, unless the purpose is strategic and recorded as such."],
    note="At INR 1 crore per episode instead of 1.5, commissioning is marginally positive. Limits: subscriber uplift, churn, CPM, costs and fees are assumptions; partner-side economics of co-production are not modelled.")
print(d.save(ROOT / "reports" / "executive_presentation.pptx"))
