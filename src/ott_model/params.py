"""Load assumptions and scenarios from the registers in docs/ (single source of truth)."""
from pathlib import Path
import csv

ROOT = Path(__file__).resolve().parents[2]
ASSUMPTIONS = ROOT / "docs" / "assumptions_register.csv"
SCENARIOS = ROOT / "docs" / "scenarios.csv"
ADDS_CURVE = (0.60, 0.25, 0.15)  # share of title-driven adds/viewing in launch month and next two


def load_register(path=ASSUMPTIONS):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def load_params(path=ASSUMPTIONS, column="base"):
    """Return {id: float} taken from the low/base/high column of the register."""
    return {r["id"]: float(r[column]) for r in load_register(path)}


def load_ranges(path=ASSUMPTIONS):
    return {r["id"]: (float(r["low"]), float(r["base"]), float(r["high"])) for r in load_register(path)}


def load_scenarios(path=SCENARIOS):
    out = {"base": {}}
    with open(path, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            out.setdefault(r["scenario"], {})[r["parameter"]] = float(r["value"])
    return out


def apply_scenario(params, overrides):
    unknown = set(overrides) - set(params)
    if unknown:
        raise KeyError(f"Unknown parameters in scenario: {sorted(unknown)}")
    return {**params, **overrides}
