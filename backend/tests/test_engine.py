"""Calculation rules of the engine, tested without a database."""

from typing import Any

from app.config_loader import load_territory
from app.config_loader.indicators import IndicatorDefinition
from app.config_loader.territory import Localized, QualityFlag
from app.services.indicators.engine import Datum, Engine, Unit, load_method
from app.settings import REPO_ROOT

CONFIG = load_territory(REPO_ROOT / "config" / "territories" / "rabat.yaml")
METHOD = load_method(CONFIG)


def engine(units: list[Unit], raw: dict[tuple[int, str, int], Datum] | None = None) -> Engine:
    e = Engine.__new__(Engine)
    e.config, e.method, e.units, e.raw, e.cache = CONFIG, METHOD, units, raw or {}, {}
    e.counts, e.category_totals, e.facility_year = {}, {}, 2026
    e.facility_source = e.boundary_source = e.grid_source = "test"
    return e


def unit(uid: int, flag: QualityFlag | None = None) -> Unit:
    return Unit(uid, f"U{uid}", None, "commune", 10.0, None, ["agglomeration"], flag)


def indicator(code: str) -> IndicatorDefinition:
    return next(i for i in METHOD.grid.indicators if i.code == code)


def entries(values: dict[int, float | None]) -> dict[int, dict[str, Any]]:
    return {uid: {"value": v, "status": "not_evaluable", "rank": None} for uid, v in values.items()}


def pop(value: float) -> Datum:
    return Datum(value, 2024, "official", "direct", "HCP")


def test_reference_is_the_population_weighted_mean() -> None:
    units = [unit(1), unit(2)]
    e = engine(units)
    reference = e.reference(
        indicator("EMP_CHOM"),
        entries({1: 10.0, 2: 20.0}),
        {1: pop(100), 2: pop(300)},
        "agglomeration",
    )
    assert reference is not None
    assert reference["value"] == 17.5


def test_relative_statuses_use_the_80_and_95_percent_thresholds() -> None:
    e = engine([unit(1), unit(2), unit(3)])
    per_unit = entries({1: 7.9, 2: 9.0, 3: 9.6})  # reference 10, « plus = mieux »
    e.evaluate(indicator("EMP_ACTF"), per_unit, {"type": "relative", "value": 10.0})
    assert [per_unit[i]["status"] for i in (1, 2, 3)] == ["deficit_marked", "watch", "ok"]


def test_lower_is_better_mirrors_the_thresholds() -> None:
    e = engine([unit(1), unit(2), unit(3)])
    per_unit = entries({1: 12.1, 2: 11.0, 3: 10.4})  # reference 10, « moins = mieux »
    e.evaluate(indicator("EMP_CHOM"), per_unit, {"type": "relative", "value": 10.0})
    assert [per_unit[i]["status"] for i in (1, 2, 3)] == ["deficit_marked", "watch", "ok"]
    assert round(per_unit[1]["gap_pct"]) == 21


def test_missing_value_is_never_zero_and_excluded_units_are_not_ranked() -> None:
    flag = QualityFlag(
        official_code="1", exclude_from_ranking=True, warning=Localized(fr="x", ar="س")
    )
    units = [unit(1), unit(2), unit(3, flag)]
    e = engine(units)
    per_unit = entries({1: 5.0, 2: None, 3: 50.0})
    e.rank(indicator("EMP_CHOM"), per_unit, "agglomeration")
    assert per_unit[1]["rank"] == 1 and per_unit[1]["rank_of"] == 1
    assert per_unit[2]["rank"] is None and per_unit[2]["value"] is None
    assert per_unit[3]["rank"] is None and per_unit[3]["excluded_from_ranking"]


def test_badge_is_the_weakest_input_and_reliability_adds_up() -> None:
    e = engine([unit(1)])
    official = Datum(1, 2024, "official", "direct", "HCP")
    estimated = Datum(1, 2024, "estimated", "modeled", "grille")
    assert e.badge([official, estimated]) == "estimated"
    # official (40) + recent (25) + complete (20) + direct (15)
    assert e.reliability([official], "direct", provisional=False) == 100


def test_growth_rate_and_land_consumption() -> None:
    u = unit(1)
    raw = {
        (1, "population", 2014): pop(1000),
        (1, "population", 2024): pop(2000),
        (1, "built_up_km2", 2015): Datum(1.0, 2015, "open", "derived", "GHSL"),
        (1, "built_up_km2", 2020): Datum(1.1, 2020, "open", "derived", "GHSL"),
    }
    e = engine([u], raw)
    growth = e.compute(u, indicator("DEM_TCAM"))
    assert round(growth.value, 2) == 7.18  # (2000/1000)^(1/10) - 1
    consumption = e.compute(u, indicator("URB_CONSO"))
    assert consumption.method == "modeled"
    assert consumption.extra["added_built_m2"] == 100000
    assert 200 < consumption.value < 400  # m² per additional inhabitant


def test_requested_input_is_reported_as_missing() -> None:
    u = unit(1)
    e = engine([u], {(1, "population", 2024): pop(1000)})
    try:
        e.compute(u, indicator("EDU_ECOLES"))
    except Exception as exc:  # MissingInput
        assert "schools_primary_middle" in str(exc)
    else:
        raise AssertionError("EDU_ECOLES should not be computable without education data")
