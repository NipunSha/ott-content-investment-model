# Commission, acquire or co-produce? Executive investment recommendation

*Hypothetical case: a mid-sized Indian subscription platform with 5 million paying subscribers evaluating one six-episode scripted series. All monetary values are INR crore, present value at a 12% discount rate unless stated. Inputs marked "assumption" in `docs/assumptions_register.csv` are scenario inputs, not market quotes.*

## The decision in one paragraph

On directly attributable economics, none of the three structures is comfortably profitable at base-case assumptions, which describe a premium series at INR 1.5 crore an episode. Co-production is the only one that clears zero (NPV +0.7), commissioning loses 3.3 and acquisition loses 1.6. The ranking is driven far more by how many subscribers the title brings in and what it costs per episode than by anything on the advertising or rights side. Commissioning only beats co-production if the platform expects to earn more than roughly the full production cost again from owned rights after year three, or if the title performs at more than three times plan. Acquisition is never the highest-value choice in expectation, but it is the cheapest way to be wrong.

## What each option costs and returns (base case)

| | Commission | Acquire | Co-produce |
|---|---|---|---|
| PV of costs | 13.7 | 5.3 | 7.9 |
| PV of contribution | 10.4 | 3.6 | 8.6 |
| NPV | -3.3 | -1.6 | +0.7 |
| Peak cash exposure | 13.9 | 5.0 | 7.8 |
| Payback after launch | not within 36 months | not within 36 months | month 17 |
| Months from decision to launch | 12 | 1 | 12 |

Subscriber acquisition supplies about three-quarters or more of contribution in every structure. Retention of existing subscribers adds 0.2–0.6 and advertising to non-paying viewers 0.1–0.3. Advertising would need roughly 18–21 times the assumed ad-tier audience to bring commissioning or acquisition to break-even on its own; at the assumed CPM it changes the case at the margin only.

## Break-even conditions

| Structure | Incremental subscribers needed | vs base assumption | Net ARPU needed (INR/month) | Cost per episode at which NPV = 0 |
|---|---|---|---|---|
| Commission | 255,000 | 1.42x | 97 | 1.06 |
| Acquire | 109,000 (title's own adds) | 1.51x | 103 | fee of 30% of production cost instead of 45% |
| Co-produce | 164,000 | 0.91x | 64 | 1.65 |

A commissioned six-episode series at INR 1.5 crore an episode therefore has to bring in about a quarter of a million subscribers who would not otherwise have joined, at INR 70 net ARPU and 8% monthly churn. If churn among those subscribers is 5% rather than 8%, commissioning breaks even at the base subscriber number; the quality of the subscribers a title attracts matters as much as their count.

## Cost per episode decides whether there is a case at all

| NPV at cost per episode of | 0.5 | 1.0 | 1.5 (base) | 2.0 |
|---|---|---|---|---|
| Commission | +4.2 | +0.5 | -3.3 | -7.1 |
| Acquire | +1.6 | -0.0 | -1.6 | -3.3 |
| Co-produce | +5.1 | +2.9 | +0.7 | -1.6 |

The base case of INR 1.5 crore sits above the INR 0.3–1 crore range that trade press reports for current commissioning. At INR 1 crore an episode, commissioning is marginally positive and co-production clearly so; at INR 0.5 crore all three structures create value. Acquisition scales with the same input because its licence fee is modelled as a share of the title's production cost. The ranking of structures does not change across this range.

## Scenarios

| NPV | Downside | Base | Upside |
|---|---|---|---|
| Commission | -10.4 | -3.3 | +7.0 |
| Acquire | -3.7 | -1.6 | +1.9 |
| Co-produce | -4.7 | +0.7 | +9.1 |

Acquisition loses least when the title underperforms; co-production gains most when it works. Commissioning has the widest range and is dominated by co-production in all three scenarios under the base deal terms.

## Risk-adjusted view (20,000 simulated outcomes)

| | Mean NPV | Median | P(NPV > 0) | Worst-5% average | Share of draws where it is the best option |
|---|---|---|---|---|---|
| Commission | -4.2 | -6.3 | 24% | -19.3 | 5% |
| Acquire | -2.4 | -2.4 | 17% | -8.0 | 47% |
| Co-produce | +0.1 | -1.9 | 38% | -10.5 | 48% |

Three points are easy to miss. First, the median outcome is negative for every structure: scripted originals are a hit-driven bet in which the mean is carried by a minority of outcomes. Second, acquisition is "best" in 47% of draws mostly because it loses less when titles disappoint, not because it wins: it is profitable in only 17% of them. Third, co-production's expected value is indistinguishable from zero. Its advantage is relative, not absolute. Widening or narrowing the assumed spread of title performance moves co-production's share of "best" draws between 38% and 62% without changing the ordering of mean NPV. Simulated means sit below the base case because the cost-side ranges (overrun, marketing, cost per episode) are skewed upwards.

## When each structure makes sense

**Co-produce** if terms like those assumed here are obtainable: a partner funding around half of production in return for the title leaving exclusivity after about 18 months and 70% of downstream rights. On those terms it keeps most of the audience upside for half the capital. Its base-case NPV of +0.7 is small relative to the uncertainty in the inputs, so the finding is that it is the least unattractive structure for a premium single season, not that it is reliably profitable. It stops being preferable if the partner's terms push the platform's cost share above about 92%, which is commissioning by another name. The model does not test whether these terms are attractive to the partner; that is a negotiation fact, not a modelling output.

**Commission** when ownership itself is the objective: a franchise candidate where sequels, remakes or long library life are plausibly worth more than the first season's production cost (indifference at 108% of production cost versus an assumed 10%), or when no partner is available and the platform has evidence that the title's audience will be large and unusually loyal. A single season judged over three years rarely justifies full ownership.

**Acquire** when the constraint is capital or time rather than expected value: one-twelfth of the lead time, roughly a third of the cash at risk, and the smallest tail loss. It breaks even on its own at a licence fee near 30% of the title's production cost, and matches co-production only if its audience pull exceeds about 66% of an equivalent original.

**Do none of them** if the platform cannot expect at least ~165,000 incremental subscribers from the title, unless the purpose is strategic (catalogue credibility, language entry) and is recorded as such rather than justified by this model.

## What this analysis cannot tell you

- The subscriber, churn, CPM, cost and fee inputs are assumptions. The only observed anchors are FICCI-EY market totals, published plan prices and unaudited trade-press cost ranges (see `docs/source_register.csv`).
- Subscriber attribution is the weakest link in any title-level P&L. The model takes incremental subscribers as an input; it does not estimate them.
- Catalogue effects, brand value, bundling deals and the option value of a second season are outside the model except through the single residual-rights input.
- Co-production looks better than commissioning partly by construction: the partner pays 50% of cost for 70% of secondary and residual rights and later exploitation, while the platform keeps the full launch audience and pays all marketing and localisation. Whether a partner accepts that is untested.
- Net ARPU of INR 70 is anchored on list prices and an industry average; subscribers drawn in by a single title may pay less.
- Deal terms are stylised. Real contracts include minimum guarantees, holdbacks and bonuses that shift risk between parties.
