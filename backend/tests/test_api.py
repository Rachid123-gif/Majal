from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.db import get_engine
from app.main import create_app
from app.settings import get_settings


@pytest.fixture
def client_without_db(monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    # Port 1 is never a PostgreSQL server: the API must stay up and say so in French.
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://majal:majal@127.0.0.1:1/majal")
    get_settings.cache_clear()
    get_engine.cache_clear()
    yield TestClient(create_app())
    get_settings.cache_clear()
    get_engine.cache_clear()


def test_health_reports_missing_database(client_without_db: TestClient) -> None:
    response = client_without_db.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "degraded"
    assert body["database"]["ok"] is False
    assert "injoignable" in body["database"]["message"]
    assert body["config"] == {"ok": True, "territories": 2, "message": "Configuration valide"}


def test_territories_are_listed_from_config(client_without_db: TestClient) -> None:
    response = client_without_db.get("/api/territories")
    assert response.status_code == 200
    by_code = {t["code"]: t for t in response.json()}
    assert by_code["rabat"]["name"] == {"fr": "Rabat", "ar": "الرباط"}
    assert by_code["tetouan"]["study_area"]["fr"] == "Province de Tétouan"
    rabat_default = [s["code"] for s in by_code["rabat"]["scopes"] if s["default"]]
    assert rabat_default == ["agglomeration"]
