"""Citizen listening API: login required, banner returned, import reserved to the professor
and administrator accounts. Database tests are skipped without PostGIS."""

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.db import check_database
from app.main import create_app
from app.settings import get_settings

PROF, PRES = "test-prof-password", "test-pres-password"


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    monkeypatch.setenv("SESSION_SECRET", "test-secret")
    monkeypatch.setenv("DEMO_PROFESSEUR_PASSWORD", PROF)
    monkeypatch.setenv("DEMO_PRESENTATEUR_PASSWORD", PRES)
    get_settings.cache_clear()
    yield TestClient(create_app())
    get_settings.cache_clear()


def login(client: TestClient, username: str, password: str) -> None:
    assert (
        client.post(
            "/api/auth/login", json={"username": username, "password": password}
        ).status_code
        == 200
    )


def test_citizen_endpoints_require_login(client: TestClient) -> None:
    assert client.get("/api/territories/rabat/citizens").status_code == 401
    assert (
        client.post(
            "/api/territories/rabat/citizens/import?filename=a.csv", content=b"x"
        ).status_code
        == 401
    )


def test_import_is_reserved_to_professor_and_administrator(client: TestClient) -> None:
    login(client, "presentateur", PRES)
    response = client.post(
        "/api/territories/rabat/citizens/import?filename=a.csv", content=b"texte\nbonjour\n"
    )
    assert response.status_code == 403
    assert "professeur et administrateur" in response.json()["detail"]


def test_a_wrong_file_is_explained(client: TestClient) -> None:
    login(client, "professeur", PROF)
    response = client.post(
        "/api/territories/rabat/citizens/import?filename=a.csv", content=b"id\n1\n"
    )
    assert response.status_code == 422
    assert "colonne « texte »" in response.json()["detail"]


@pytest.mark.skipif(not check_database().ok, reason="base PostGIS non disponible")
def test_dashboard_carries_the_fictitious_banner(client: TestClient) -> None:
    login(client, "presentateur", PRES)
    response = client.get("/api/territories/rabat/citizens")
    if response.status_code == 404:
        pytest.skip("territoire non importé")
    data = response.json()
    if not data["consultations"]:
        pytest.skip("aucune contribution importée (make citizens)")
    assert data["fictitious"] is True
    assert data["banner"]["fr"].startswith("Contributions fictives")
    assert all(
        t["share"] is None or data["summary"]["total"] >= 20 for t in data["summary"]["themes"]
    )


def test_review_is_reserved_to_professor_and_administrator(client: TestClient) -> None:
    login(client, "presentateur", PRES)
    assert client.get("/api/territories/rabat/citizens/review").status_code == 403
    response = client.post(
        "/api/territories/rabat/citizens/contributions/1/review",
        json={"themes": ["voirie"], "tonality": "plainte", "territory_id": None},
    )
    assert response.status_code == 403
    assert "professeur et administrateur" in response.json()["detail"]
