# Methodology
## Structure
`src/ott_model/model.py` builds a monthly cash-flow schedule per option from the parameters in `docs/assumptions_register.csv`. `model/ott_content_investment_model.xlsx` implements the same schedule in Excel formulas; `tests/test_excel_matches_python.py` recalculates the workbook and requires agreement to 1e-6 in all three scenarios.

## Revenue (contribution) logic
- **Incremental subscriber acquisition:** title-driven gross adds arrive 60/25/15% over the launch month and the next two. Each cohort decays at the monthly churn rate. Contribution = active subscribers x net ARPU x contribution margin.
- **Retention:** a share of the existing base watches the title; for a fixed number of months a small share of them who would have churned do not. They then decay at the normal churn rate.
- **Advertising:** only non-paying ad-tier viewers generate ad revenue (hours x ad load x fill x CPM x margin). Ads shown to paying subscribers are treated as part of blended ARPU, which prevents double counting.
- **Rights:** secondary licensing 18 months after launch and a residual value at the end of the horizon, both proportional to production cost and to the platform's rights share.
- The platform's total subscription revenue is never attributed to the title.

## How the three structures differ
| | Commission | Acquire | Co-produce |
|---|---|---|---|
| Cash out | production + producer fee + overrun over 12 months | licence fee at launch | platform share of production + overrun |
| Launch | month 12 | month 1 | month 12 |
| Audience | 1.0 x plan | multiplier (0.40 base) | 1.0 x plan |
| Rights window | full horizon | licence term (24 months), then nothing | exclusive 18 months, then 50% of subscriber contribution |
| Secondary / residual | 100% | none | platform share (30%) |

## Analyses
- **Scenarios:** downside / base / upside overrides in `docs/scenarios.csv`.
- **Break-even:** root of NPV in one driver, others held at scenario values.
- **Indifference:** value of a driver at which two structures have equal NPV.
- **Sensitivity:** each uncertain driver moved to its register low and high, one at a time.
- **Decision grid:** best structure across two drivers.
- **Monte Carlo (20,000 draws, seed 7):** uncertain cost, price, churn and deal inputs drawn independently from triangular(low, base, high); audience drivers and the discount rate held at base; title performance from a mean-one lognormal (sigma 0.75 for an unmade original, 0.35 for an existing title whose record is visible). Commission and co-production share the same performance draw because they are the same title. The lognormal reflects the skew typical of hit-driven content; its spread is an assumption and is stress-tested at sigma 0.5 and 1.0 (`montecarlo_sigma_robustness.csv`). The same seed and draw count are used for every sigma setting. Because triangular distributions are skewed where base is not the midpoint (cost-side ranges skew upwards), simulated means sit below base-case values.

## Modelling asymmetries to be aware of
- An acquired title's attributed subscriber contribution stops at licence expiry; originals keep theirs to the horizon.
- In co-production the platform's share of secondary and residual rights (30%) is a separate input from its cost share (50%), and it bears all marketing and localisation.
- Title performance scales secondary and residual rights values for originals; an acquired title has neither.
- Subscribers earn a full month of contribution in the month they join.

## Discounting
12% annual, converted to a monthly rate; month 0 is the decision date, so the 12-month production lag of originals is penalised.
