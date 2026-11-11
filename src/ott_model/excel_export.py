"""Write the model as an Excel workbook with live formulas (no hard-coded results in the
calculation sheets). The Python model remains the reference; `Check` compares both."""
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.utils import get_column_letter as col
from .params import load_register, load_scenarios, ADDS_CURVE, ROOT
from .model import OPTIONS
from . import analysis

N_ROWS = 49  # months 0..48 covers the longest timeline (12 months production + 36 months)
FIRST = 7
HEAD = Font(bold=True, color="FFFFFF"); FILL = PatternFill("solid", fgColor="1F3A5F")
INPUT_FILL = PatternFill("solid", fgColor="FFF2CC")


def _header(ws, row, labels):
    for j, h in enumerate(labels, 1):
        c = ws.cell(row=row, column=j, value=h); c.font = HEAD; c.fill = FILL
        c.alignment = Alignment(wrap_text=True, vertical="top")


def build(path=ROOT / "model" / "ott_content_investment_model.xlsx"):
    reg, scen = load_register(), load_scenarios()
    wb = Workbook()
    ws = wb.active; ws.title = "Inputs"
    ws["A1"] = "OTT content investment model - inputs (hypothetical case; see docs/assumptions_register.csv)"; ws["A1"].font = Font(bold=True, size=13)
    ws["A2"] = "Scenario"; ws["B2"] = "base"; ws["B2"].fill = INPUT_FILL
    dv = DataValidation(type="list", formula1='"base,downside,upside"', allow_blank=False); ws.add_data_validation(dv); dv.add("B2")
    ws["C2"] = "<- choose base / downside / upside. Yellow cells are editable inputs; column G feeds the model."
    _header(ws, 4, ["id", "parameter", "unit", "base", "downside", "upside", "ACTIVE", "type", "basis"])
    ref = {}
    r = 5
    rows = [(x["id"], x["parameter"], x["unit"], float(x["base"]), x["type"], x["basis"]) for x in reg]
    rows += [(f"adds_curve_m{i}", f"Share of title-driven adds and viewing in month {i} after launch", "ratio", v, "STRUCTURAL", "Fixed launch curve") for i, v in enumerate(ADDS_CURVE)]
    for pid, name, unit, base, typ, basis in rows:
        ws.cell(r, 1, pid); ws.cell(r, 2, name); ws.cell(r, 3, unit)
        ws.cell(r, 4, base).fill = INPUT_FILL
        ws.cell(r, 5, scen["downside"].get(pid, None)); ws.cell(r, 6, scen["upside"].get(pid, None))
        if pid in scen["downside"]: ws.cell(r, 5).fill = INPUT_FILL
        if pid in scen["upside"]: ws.cell(r, 6).fill = INPUT_FILL
        # blank scenario cell -> fall back to base
        ws.cell(r, 7, f'=IF($B$2="downside",IF(ISBLANK(E{r}),D{r},E{r}),IF($B$2="upside",IF(ISBLANK(F{r}),D{r},F{r}),D{r}))').font = Font(bold=True)
        ws.cell(r, 8, typ); ws.cell(r, 9, basis)
        ref[pid] = f"Inputs!$G${r}"
        r += 1
    for c, w in zip("ABCDEFGHI", (30, 70, 22, 12, 12, 12, 12, 18, 90)): ws.column_dimensions[c].width = w
    ws.freeze_panes = "A5"

    P = ref
    prod = f'({P["episodes"]}*{P["prod_cost_per_episode_cr"]})'
    unit = f'({P["arpu_month"]}*{P["contribution_margin_sub"]}/10000000)'
    cfg = {
        "commission": dict(L=P["production_months"], aud="1", W=P["horizon_months"], post="1", share="1", rights="1"),
        "coproduce": dict(L=P["production_months"], aud=P["copro_audience_multiplier"], W=P["exclusive_window_months"], post=P["post_window_factor"], share=P["platform_cost_share"], rights=P["platform_secondary_share"]),
        "acquire": dict(L=P["acq_launch_month"], aud=P["acq_audience_multiplier"], W=P["licence_term_months"], post="0", share="0", rights="0"),
    }
    cols = ["month", "months since launch", "live (1/0)", "launch curve", "rights window factor", "new title-driven subs", "active title-driven subs",
            "new retained subs", "active retained subs", "rev: subscriber acquisition", "rev: subscriber retention", "rev: advertising (non-paying viewers)",
            "rev: secondary licensing", "rev: residual rights", "cost: production / licence", "cost: producer fee", "cost: overrun", "cost: marketing",
            "cost: localisation", "cost: delivery", "total contribution", "total cost", "net cash", "discount factor", "PV of net cash", "cumulative net cash", "payback flag"]
    last = FIRST + N_ROWS - 1
    for o in OPTIONS:
        c = cfg[o]
        sh = wb.create_sheet(o.capitalize())
        sh["A1"] = f"Monthly schedule - {o} (INR crore; month 0 = decision date)"; sh["A1"].font = Font(bold=True, size=13)
        labels = [("launch month", f'={c["L"]}'), ("audience multiplier (structure x title performance)", f'={c["aud"]}*{P["title_performance"]}'),
                  ("rights window (months)", f'={c["W"]}'), ("post-window factor", f'={c["post"]}'),
                  ("platform cost share", f'={c["share"]}'), ("platform rights share", f'={c["rights"]}'),
                  ("engaged existing subs", f'={P["existing_base_subs"]}*MIN({P["engaged_share_of_base"]}*$B$3,1)')]
        # parameters laid out across row 2/3: label in row 2, value in row 3, columns A..G
        for j, (lab, f) in enumerate(labels, 1):
            sh.cell(2, j, lab).font = Font(italic=True); sh.cell(3, j, f)
        Lc, AUD, W, POST, SH, RS, ENG = "$A$3", "$B$3", "$C$3", "$D$3", "$E$3", "$F$3", "$G$3"
        _header(sh, FIRST - 1, cols)
        for i in range(N_ROWS):
            r = FIRST + i
            prevG = f"G{r-1}*(1-{P['monthly_churn']})+" if i else ""
            prevI = f"I{r-1}*(1-{P['monthly_churn']})+" if i else ""
            f = {
                1: i,
                2: f"=A{r}-{Lc}",
                3: f"=IF(AND(B{r}>=0,B{r}<{P['horizon_months']}),1,0)",
                4: f"=IF(B{r}=0,{P['adds_curve_m0']},IF(B{r}=1,{P['adds_curve_m1']},IF(B{r}=2,{P['adds_curve_m2']},0)))",
                5: f"=IF(C{r}=0,0,IF(B{r}<{W},1,{POST}))",
                6: f"={P['gross_adds']}*{AUD}*D{r}",
                7: f"={prevG}F{r}",
                8: f"=IF(AND(B{r}>=0,B{r}<{P['retention_effect_months']}),{ENG}*{P['churn_reduction_pp']},0)",
                9: f"={prevI}H{r}",
                10: f"=G{r}*{unit}*E{r}",
                11: f"=I{r}*{unit}*E{r}",
                12: f"={P['avod_viewers']}*{AUD}*{P['hours_per_avod_viewer']}*D{r}*{P['ad_impressions_per_hour']}*{P['ad_fill_rate']}*{P['avod_cpm_inr']}/1000*{P['ad_contribution_margin']}/10000000",
                13: f"=IF(AND(C{r}=1,B{r}={P['secondary_month_after_launch']}),{prod}*{P['secondary_licensing_pct']}*{P['title_performance']}*{RS},0)",
                14: f"=IF(B{r}={P['horizon_months']}-1,{prod}*{P['residual_rights_value_pct']}*{P['title_performance']}*{RS},0)",
                20: f"=(({P['gross_adds']}*{AUD}+{ENG})*{P['hours_per_paid_viewer']}+{P['avod_viewers']}*{AUD}*{P['hours_per_avod_viewer']})*D{r}*{P['delivery_cost_per_hour_inr']}/10000000",
                21: f"=SUM(J{r}:N{r})", 22: f"=SUM(O{r}:T{r})", 23: f"=U{r}-V{r}",
                24: f"=(1+{P['discount_rate_annual']})^(-A{r}/12)", 25: f"=W{r}*X{r}",
                26: f"=W{r}" if i == 0 else f"=Z{r-1}+W{r}",
                27: f"=IF(AND(B{r}>=0,C{r}=1,Z{r}>=0),1,0)",
            }
            inprod = f"AND(A{r}>=1,A{r}<={Lc})"
            if o == "acquire":
                fee = f"{prod}*{P['licence_fee_pct_of_prod_cost']}"
                f.update({15: f"=IF(B{r}=0,{fee},0)", 16: 0, 17: 0,
                          18: f"=IF(B{r}=0,{fee}*{P['acq_marketing_pct_of_fee']},0)",
                          19: f"=IF(B{r}=0,{P['episodes']}*{P['acq_dub_languages']}*{P['dub_cost_per_episode_lang_cr']},0)"})
            else:
                f.update({15: f"=IF({inprod},{prod}*{SH}/{Lc},0)",
                          16: (f"=IF({inprod},{prod}*(1+{P['overrun_pct']})*{P['producer_fee_pct']}/{Lc},0)" if o == "commission" else 0),
                          17: f"=IF({inprod},{prod}*{SH}*{P['overrun_pct']}/{Lc},0)",
                          18: f"=IF(OR(B{r}=-1,B{r}=0),{prod}*{P['marketing_pct_of_production']}/2,0)",
                          19: f"=IF(B{r}=-1,{P['episodes']}*{P['dub_languages']}*{P['dub_cost_per_episode_lang_cr']},0)"})
            for j, v in f.items():
                sh.cell(r, j, v)
        for j in range(1, len(cols) + 1): sh.column_dimensions[col(j)].width = 15
        sh.freeze_panes = sh.cell(FIRST, 3)

    sm = wb.create_sheet("Summary", 1)
    sm["A1"] = "Summary (INR crore) - recalculates with the scenario chosen on Inputs!B2"; sm["A1"].font = Font(bold=True, size=13)
    sm["A2"] = "Hypothetical case. Inputs marked ASSUMPTION are not market quotes."
    _header(sm, 4, ["metric"] + [o for o in OPTIONS])
    R = f"{FIRST}:{{c}}{last}"
    def rng(sheet, c): return f"{sheet}!{c}{FIRST}:{c}{last}"
    metrics = [
        ("NPV", lambda s: f"=SUM({rng(s,'Y')})"),
        ("PV of costs", lambda s: f"=SUMPRODUCT({rng(s,'V')},{rng(s,'X')})"),
        ("PV of contribution", lambda s: f"=SUMPRODUCT({rng(s,'U')},{rng(s,'X')})"),
        ("ROI on PV of costs", lambda s: f"=SUM({rng(s,'Y')})/SUMPRODUCT({rng(s,'V')},{rng(s,'X')})"),
        ("PV: subscriber acquisition", lambda s: f"=SUMPRODUCT({rng(s,'J')},{rng(s,'X')})"),
        ("PV: subscriber retention", lambda s: f"=SUMPRODUCT({rng(s,'K')},{rng(s,'X')})"),
        ("PV: advertising", lambda s: f"=SUMPRODUCT({rng(s,'L')},{rng(s,'X')})"),
        ("PV: secondary licensing", lambda s: f"=SUMPRODUCT({rng(s,'M')},{rng(s,'X')})"),
        ("PV: residual rights", lambda s: f"=SUMPRODUCT({rng(s,'N')},{rng(s,'X')})"),
        ("Undiscounted cost", lambda s: f"=SUM({rng(s,'V')})"),
        ("Peak cash exposure", lambda s: f"=-MIN({rng(s,'Z')})"),
        ("Payback (months after launch; -1 = not within horizon)", lambda s: f"=IF(SUM({rng(s,'AA')})=0,-1,INDEX({rng(s,'B')},MATCH(1,{rng(s,'AA')},0)))"),
    ]
    for i, (name, fn) in enumerate(metrics):
        sm.cell(5 + i, 1, name)
        for j, o in enumerate(OPTIONS):
            sm.cell(5 + i, 2 + j, fn(o.capitalize()))
    sm.column_dimensions["A"].width = 55
    for c in "BCD": sm.column_dimensions[c].width = 16
    sm["A19"] = "Break-evens: use Data > What-If > Goal Seek on the NPV cells above, or see the Python outputs on the 'Python_outputs' sheet."

    # Static Python outputs for cross-checking and for readers without Python
    py = wb.create_sheet("Python_outputs")
    py["A1"] = "Static values exported from the Python model (not formulas). Regenerate with scripts/run_all.py."; py["A1"].font = Font(bold=True)
    st = analysis.scenario_table()[["scenario", "option", "npv_cr", "pv_cost_cr", "pv_contribution_cr", "payback_month_from_launch"]]
    _header(py, 3, list(st.columns))
    for i, row in enumerate(st.itertuples(index=False), 4):
        for j, v in enumerate(row, 1): py.cell(i, j, None if v != v else v)
    be = analysis.breakeven_table(); r0 = 4 + len(st) + 2
    _header(py, r0, list(be.columns))
    for i, row in enumerate(be.itertuples(index=False), r0 + 1):
        for j, v in enumerate(row, 1): py.cell(i, j, None if v != v else v)
    ck = wb.create_sheet("Check")
    ck["A1"] = "Excel formulas vs Python model for the selected scenario (difference should be ~0)"; ck["A1"].font = Font(bold=True)
    _header(ck, 3, ["option", "Excel NPV", "Python NPV", "difference"])
    for j, o in enumerate(OPTIONS):
        r = 4 + j
        ck.cell(r, 1, o); ck.cell(r, 2, f"=Summary!{col(2+j)}5")
        ck.cell(r, 3, f'=SUMIFS(Python_outputs!$C$4:$C${3+len(st)},Python_outputs!$A$4:$A${3+len(st)},Inputs!$B$2,Python_outputs!$B$4:$B${3+len(st)},A{r})')
        ck.cell(r, 4, f"=B{r}-C{r}")
    path.parent.mkdir(exist_ok=True)
    wb.save(path)
    return path
