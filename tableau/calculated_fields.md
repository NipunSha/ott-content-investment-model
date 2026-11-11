# Calculated fields
| Name | Data source | Formula | Purpose |
|---|---|---|---|
| Option label | all | `CASE [option] WHEN 'commission' THEN 'Commission' WHEN 'acquire' THEN 'Acquire' ELSE 'Co-produce' END` | Display names |
| NPV sign | summary | `IF [npv_cr] >= 0 THEN 'Creates value' ELSE 'Destroys value' END` | KPI colour |
| Payback label | summary | `IF ISNULL([payback_month_from_launch]) THEN 'Not within horizon' ELSE STR([payback_month_from_launch]) + ' months' END` | KPI text |
| Tornado start | tornado | `MIN([npv_at_low_cr],[npv_at_high_cr])` | Gantt start |
| Tornado length | tornado | `ABS([npv_at_high_cr]-[npv_at_low_cr])` | Gantt size |
| Break-even gap % | breakeven | `([breakeven_value]-[current_value])/[current_value]` | Distance to break-even |
| Adds (thousands) | decision grid | `[gross_adds]/1000` | Axis |
| Loss flag | MC draws | `IF [npv_cr] < 0 THEN 1 ELSE 0 END` | Share of losing draws = AVG |
