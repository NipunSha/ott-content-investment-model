"""The Excel workbook is recalculated with the `formulas` library and compared with Python."""
import pytest
formulas = pytest.importorskip("formulas")
from ott_model import load_params, load_scenarios, apply_scenario, evaluate, OPTIONS
from ott_model.excel_export import build


@pytest.fixture(scope="module")
def xl(tmp_path_factory):
    path = build(tmp_path_factory.mktemp("xl") / "model.xlsx")
    return formulas.ExcelModel().load(str(path)).finish(), path.name


@pytest.mark.parametrize("scenario", ["base", "downside", "upside"])
def test_excel_summary_equals_python(xl, scenario):
    model, book = xl
    sol = model.calculate(inputs={f"'[{book}]INPUTS'!B2": scenario})
    p = apply_scenario(load_params(), load_scenarios()[scenario])
    rows = {"npv_cr": 5, "pv_cost_cr": 6, "pv_contribution_cr": 7, "undiscounted_cost_cr": 14, "peak_cash_exposure_cr": 15, "payback_month_from_launch": 16}
    for j, o in enumerate(OPTIONS):
        want = evaluate(o, p)
        for key, r in rows.items():
            got = sol[f"'[{book}]SUMMARY'!{'BCD'[j]}{r}"].value[0, 0]
            expect = want[key] if want[key] is not None else -1
            assert float(got) == pytest.approx(expect, abs=1e-6), (scenario, o, key)
