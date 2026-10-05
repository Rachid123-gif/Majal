from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.settings import get_settings


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Iterator[TestClient]:
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    get_settings.cache_clear()
    yield TestClient(create_app())
    get_settings.cache_clear()


def test_units_and_facilities_require_login(client: TestClient) -> None:
    for path in ("/api/territories/rabat/units", "/api/territories/rabat/facilities"):
        response = client.get(path)
        assert response.status_code == 401
        assert response.json()["detail"] == "Connexion requise."


def test_missing_base_map_is_reported(client: TestClient) -> None:
    assert client.get("/api/tiles/rabat/info").json() == {"available": False}
    response = client.get("/api/tiles/rabat/10/500/400.mvt")
    assert response.status_code == 404
    assert "make data" in response.json()["detail"]


def test_unknown_territory(client: TestClient) -> None:
    response = client.get("/api/tiles/atlantide/info")
    assert response.status_code == 404
    assert response.json()["detail"] == "Territoire inconnu : atlantide."
