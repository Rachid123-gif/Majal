"""Stage 5.2: completeness, what each institution's data would allow, follow-up of requests."""

from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.config_loader.data_holders import load_data_holders, load_module_rules
from app.config_loader.indicators import load_grid
from app.config_loader.taxonomy import load_taxonomy
from app.main import create_app
from app.services.data_needs.completeness import compute, indicator_statuses
from app.settings import REPO_ROOT, get_settings

CONFIG = REPO_ROOT / "config"
HOLDERS = load_data_holders(CONFIG / "data_holders" / "rabat.yaml")
RULES = load_module_rules(CONFIG / "data_holders" / "regles.yaml")
GRID = load_grid(CONFIG / "indicators" / "grille-v0.yaml")
TAXONOMY = load_taxonomy(CONFIG / "taxonomy" / "urbain.yaml")

AVAILABLE = {
    "DEM_POP": "official",
    "MOB_TC": "estimated",
    "ENV_VERT": "open",
    "SAN_HOP": "estimated",
    "EDU_PROX": "estimated",
}
MISSING = ["SAN_ESSP", "SAN_PROX", "MOB_15MIN", "EDU_ECOLES", "URB_DOC"]


def diagnostic() -> dict[str, Any]:
    by_code = {i.code: i for i in GRID.indicators}
    codes = list(AVAILABLE) + MISSING
    indicators = [{"code": c, "axis": by_code[c].axis, "label": {"fr": c}} for c in codes]

    def values(sidi: bool) -> dict[str, Any]:
        out: dict[str, Any] = {c: {"value": 1.0, "badge": b} for c, b in AVAILABLE.items()}
        out.update({c: {"value": None, "reason": "manquant"} for c in MISSING})
        if sidi:
            out["MOB_TC"] = {"value": None, "reason": "limite incomplète"}
        return out

    return {
        "indicators": indicators,
        "units": [{"id": 1, "values": values(False)}, {"id": 2, "values": values(True)}],
    }


def test_status_is_the_least_reliable_badge_and_missing_is_never_zero() -> None:
    statuses = indicator_statuses(diagnostic())
    assert statuses["DEM_POP"]["status"] == "official"
    assert statuses["ENV_VERT"]["status"] == "open"
    assert statuses["SAN_ESSP"]["status"] == "missing"
    assert statuses["MOB_TC"]["missing_units"] == 1  # one unit not evaluable


def test_completeness_by_axis() -> None:
    result = compute(diagnostic(), GRID, HOLDERS, RULES, TAXONOMY)
    sante = next(a for a in result["axes"] if a["code"] == "sante")
    assert (sante["available"], sante["total"]) == (1, 3)
    assert result["summary"] == {"total": 10, "available": 5, "missing": 5}


def test_sentence_counts_only_indicators_missing_today() -> None:
    result = compute(diagnostic(), GRID, HOLDERS, RULES, TAXONOMY)
    sante = next(i for i in result["institutions"] if i["code"] == "sante_dr_rsk")
    assert sante["effects"]["computed"] == ["MOB_15MIN", "SAN_ESSP", "SAN_PROX"]
    assert sante["sentence"]["fr"] == (
        "Avec les données de la Direction régionale de la Santé, MAJAL pourrait calculer "
        "3 indicateurs supplémentaires et fiabiliser 1 indicateur."
    )
    hcp = next(i for i in result["institutions"] if i["code"] == "hcp_dr_rsk")
    assert "(avec les données de l'AREF)" in hcp["sentence"]["fr"]


def test_par_ou_commencer_starts_with_the_official_boundaries() -> None:
    result = compute(diagnostic(), GRID, HOLDERS, RULES, TAXONOMY)
    assert result["requests"][0]["code"] == "limites_officielles"
    assert result["requests"][0]["priority_label"]["fr"] == "Essentielle"
    assert result["requests"][-1]["priority"] == "context"


def test_follow_up_is_reserved_to_professor_and_administrator(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("SESSION_SECRET", "test-secret")
    monkeypatch.setenv("DEMO_PRESENTATEUR_PASSWORD", "test-pres-password")
    get_settings.cache_clear()
    client = TestClient(create_app())
    assert client.get("/api/territories/rabat/data-needs").status_code == 401
    response = client.post(
        "/api/auth/login", json={"username": "presentateur", "password": "test-pres-password"}
    )
    assert response.status_code == 200
    response = client.put(
        "/api/territories/rabat/data-needs/institutions/hcp_dr_rsk/tracking",
        json={"status": "sent", "date": "2026-10-07"},
    )
    assert response.status_code == 403
    assert "professeur et administrateur" in response.json()["detail"]
    get_settings.cache_clear()


def test_three_effects_follow_the_current_status() -> None:
    result = compute(diagnostic(), GRID, HOLDERS, RULES, TAXONOMY)
    limits = next(r for r in result["requests"] if r["code"] == "limites_officielles")
    # Open or estimated today: « fiabiliser » (DEM_POP is not concerned by the boundaries).
    assert set(limits["effects"]["reliable"]) == {"MOB_TC", "ENV_VERT", "SAN_HOP", "EDU_PROX"}
    assert limits["effects"]["computed"] == [] and limits["effects"]["finer"] == []
    hcp = next(i for i in result["institutions"] if i["code"] == "hcp_dr_rsk")
    assert hcp["effects"]["finer"] == ["DEM_POP"]  # already official: « affiner »
    assert "affiner 1 indicateur à l'échelle du quartier" in hcp["sentence"]["fr"]
