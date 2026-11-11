# Tableau dashboard specification: OTT Content Investment Decision
**Status: specification only. No Tableau workbook has been built or tested.** Data sources are the CSVs in `tableau/data/`, produced by `scripts/run_all.py`.

Palette: commission #1F3A5F, acquire #C8553D, co-produce #2A9D8F, neutral #B0B7C3. One global filter: `scenario` (single select, default base).

| # | Page | Business question | Sheet(s) | Data | Marks |
|---|---|---|---|---|---|
| 1 | Investment overview | Which structure creates value, and how much cash is at risk? | KPI strip (NPV, PV cost, peak exposure, payback) per option | summary_by_option_scenario | Text table, 3 columns |
| 2 | Structure comparison | How does the ranking change across scenarios? | Grouped bar NPV by scenario x option | summary_by_option_scenario | Bar, zero line |
| 3 | Cost and contribution | Where does the money go and come from? | Diverging stacked bar of PV by line | pv_breakdown_long | Stacked bar, costs negative |
| 4 | Cash profile | How deep and how long is the cash trough? | Cumulative net cash by month | cashflows_monthly | Line, reference line at 0 and at launch |
| 5 | Break-even | What must be true for NPV = 0? | Bullet chart current vs break-even | breakeven | Bar + reference mark; filter parameter |
| 6 | Sensitivity | Which assumptions matter most, and at what cost per episode does each structure work? | Tornado per option; NPV-by-cost line | sensitivity_tornado, npv_by_cost_per_episode | Gantt bar sorted by swing; line with zero reference |
| 7 | Decision map and risk | Under which conditions does each structure win, and how risky is it? | Heat map of best_option; box plot of simulated NPV | decision_grid_*, montecarlo_draws_sample, montecarlo_summary | Square, box plot |

## Wireframe (not a screenshot)
```
+--------------------------------------------------------------+
| OTT Content Investment Decision        [Scenario: base  v]   |
+--------------------+--------------------+--------------------+
| COMMISSION         | ACQUIRE            | CO-PRODUCE         |
| NPV  -3.3          | NPV  -1.6          | NPV  +0.7          |
| Cost 13.7 Peak 13.9| Cost 5.3  Peak 5.0 | Cost 7.9  Peak 7.8 |
+--------------------+--------------------+--------------------+
| NPV by scenario (grouped bar)   | Cumulative cash (lines)    |
+---------------------------------+----------------------------+
| Tornado (option selector)       | Decision map (heat map)    |
+---------------------------------+----------------------------+
```

## Assembly steps
1. Tableau > Connect > Text file > `summary_by_option_scenario.csv`; add the other CSVs as separate data sources (do not join; grains differ).
2. Create the calculated fields in `calculated_fields.md`.
3. Build one worksheet per row of the table above; assign the fixed palette to `option`.
4. Add `scenario` as a filter on sheets 1–5 and apply to all worksheets using related data sources.
5. Assemble the pages; add the caption "Hypothetical case - inputs are assumptions" to every page.
