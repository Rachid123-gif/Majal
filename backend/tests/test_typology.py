from typing import Any

from app.services.indicators.typology import compute_typology, load_typology
from app.settings import REPO_ROOT

CONFIG = load_typology(REPO_ROOT / "config" / "indicators" / "typologie.yaml")
LABELS = {v.code: {"fr": v.code, "ar": v.code} for v in CONFIG.variables}


def unit(
    uid: int, dens: float, growth: float, access: float, missing: bool = False
) -> dict[str, Any]:
    values = {
        "DEM_DENS": dens,
        "DEM_TCAM": growth,
        "URB_CROIS": growth * 2,
        "MOB_TC": access,
        "EDU_PROX": access,
        "ENV_VERT300": access / 2,
        "SAN_HOP": 10 / max(access, 1),
    }
    if missing:
        values["MOB_TC"] = None  # type: ignore[assignment]
    return {"id": uid, "values": {k: {"value": v} for k, v in values.items()}}


UNITS = (
    [unit(i, 20000 + i, 0.1, 95) for i in range(1, 7)]  # dense, well served
    + [unit(10 + i, 50 + i, 1.0, 10) for i in range(6)]  # sparse, poorly served
    + [unit(20 + i, 3000, 8.0, 30) for i in range(6)]  # fast growth
    + [unit(99, 100, 1, 1, missing=True)]
)


def test_typology_is_reproducible_and_explained() -> None:
    first = compute_typology(CONFIG, UNITS, LABELS)
    assert first == compute_typology(CONFIG, UNITS, LABELS)  # fixed seed
    assert first["available"] and first["unclassified"] == [99]
    profiles = {first["units"][uid]["profile"] for uid in (1, 2, 3)}
    assert profiles == {"centres_consolides"}
    assert first["units"][21]["profile"] == "fronts_urbanisation"
    assert first["units"][1]["traits"]  # every unit is explained in words


def test_groups_without_convincing_resemblance_stay_unnamed() -> None:
    strict = CONFIG.model_copy(update={"min_match_score": 1000})
    result = compute_typology(strict, UNITS, LABELS)
    assert all("profil à nommer" in g["label"]["fr"] for g in result["groups"])
