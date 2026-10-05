from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.security import SESSION_COOKIE, throttle
from app.settings import get_settings

PROF_PASSWORD = "test-prof-password"


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    monkeypatch.setenv("SESSION_SECRET", "test-secret")
    monkeypatch.setenv("DEMO_PROFESSEUR_PASSWORD", PROF_PASSWORD)
    monkeypatch.setenv("DEMO_PRESENTATEUR_PASSWORD", "")  # disabled account
    get_settings.cache_clear()
    throttle._failures.clear()
    yield TestClient(create_app())
    get_settings.cache_clear()


def login(client: TestClient, username: str, password: str) -> int:
    response = client.post("/api/auth/login", json={"username": username, "password": password})
    return response.status_code


def test_login_sets_an_http_only_session_cookie(client: TestClient) -> None:
    response = client.post(
        "/api/auth/login", json={"username": "Professeur ", "password": PROF_PASSWORD}
    )
    assert response.status_code == 200
    assert response.json()["roles"] == ["referent", "presenter"]
    cookie = response.headers["set-cookie"]
    assert SESSION_COOKIE in cookie and "HttpOnly" in cookie and "samesite=lax" in cookie.lower()
    me = client.get("/api/auth/me")
    assert me.status_code == 200
    assert me.json()["username"] == "professeur"


def test_wrong_password_is_refused_in_french(client: TestClient) -> None:
    response = client.post("/api/auth/login", json={"username": "professeur", "password": "x"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Identifiant ou mot de passe incorrect."


def test_account_without_password_is_disabled(client: TestClient) -> None:
    assert login(client, "presentateur", "") == 401


def test_unknown_user_is_refused(client: TestClient) -> None:
    assert login(client, "admin", PROF_PASSWORD) == 401


def test_me_requires_a_session(client: TestClient) -> None:
    response = client.get("/api/auth/me")
    assert response.status_code == 401
    assert response.json()["detail"] == "Connexion requise."


def test_tampered_cookie_is_rejected(client: TestClient) -> None:
    client.cookies.set(SESSION_COOKIE, "forged.token.value")
    assert client.get("/api/auth/me").status_code == 401


def test_logout_ends_the_session(client: TestClient) -> None:
    assert login(client, "professeur", PROF_PASSWORD) == 200
    assert client.post("/api/auth/logout").status_code == 204
    assert client.get("/api/auth/me").status_code == 401


def test_repeated_failures_lock_the_account_for_a_minute(client: TestClient) -> None:
    for _ in range(5):
        assert login(client, "professeur", "wrong") == 401
    assert login(client, "professeur", PROF_PASSWORD) == 429


def test_session_ends_when_password_is_removed(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    assert login(client, "professeur", PROF_PASSWORD) == 200
    monkeypatch.setenv("DEMO_PROFESSEUR_PASSWORD", "")
    get_settings.cache_clear()
    assert client.get("/api/auth/me").status_code == 401


def test_production_refuses_the_default_secret(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("SESSION_SECRET", "dev-only-insecure-secret")
    get_settings.cache_clear()
    with pytest.raises(RuntimeError):
        create_app()
    get_settings.cache_clear()
