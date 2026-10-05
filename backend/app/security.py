"""Demo accounts and signed session cookies.

Version D: two demo accounts whose passwords live in `.env`. Version P will store users
in the database with hashed passwords (tables `users`, `roles`).
"""

import hashlib
import hmac
import time
from dataclasses import dataclass
from enum import StrEnum

from fastapi import HTTPException, Request
from itsdangerous import BadSignature, URLSafeTimedSerializer

from app.settings import Settings, get_settings

SESSION_COOKIE = "majal_session"
MAX_FAILURES = 5
LOCKOUT_SECONDS = 60


class Role(StrEnum):
    presenter = "presenter"
    referent = "referent"
    admin = "admin"
    # Version P roles, not granted yet: analyst, decision_maker, public_reader.


@dataclass(frozen=True)
class Account:
    username: str
    display_name_fr: str
    display_name_ar: str
    roles: tuple[Role, ...]


ACCOUNTS = {
    "professeur": Account(
        "professeur",
        "Professeur — référent scientifique",
        "الأستاذ — المرجع العلمي",
        (Role.referent, Role.presenter),
    ),
    "presentateur": Account("presentateur", "Présentateur", "المقدِّم", (Role.presenter,)),
}


def _password_for(username: str, settings: Settings) -> str:
    return {
        "professeur": settings.demo_professeur_password,
        "presentateur": settings.demo_presentateur_password,
    }.get(username, "")


def _digest(value: str) -> bytes:
    return hashlib.sha256(value.encode("utf-8")).digest()


class LoginThrottle:
    """Small in-memory guard against password guessing (per username)."""

    def __init__(self) -> None:
        self._failures: dict[str, list[float]] = {}

    def locked(self, username: str, now: float) -> bool:
        recent = [t for t in self._failures.get(username, []) if now - t < LOCKOUT_SECONDS]
        self._failures[username] = recent
        return len(recent) >= MAX_FAILURES

    def fail(self, username: str, now: float) -> None:
        self._failures.setdefault(username, []).append(now)

    def reset(self, username: str) -> None:
        self._failures.pop(username, None)


throttle = LoginThrottle()


def authenticate(username: str, password: str) -> Account:
    settings = get_settings()
    username = username.strip().lower()
    now = time.monotonic()
    if throttle.locked(username, now):
        raise HTTPException(
            status_code=429,
            detail="Trop de tentatives. Patientez une minute avant de réessayer.",
        )
    expected = _password_for(username, settings)
    account = ACCOUNTS.get(username)
    # Compare digests in constant time; an empty expected password disables the account.
    if (
        account is None
        or not expected
        or not hmac.compare_digest(_digest(password), _digest(expected))
    ):
        throttle.fail(username, now)
        raise HTTPException(status_code=401, detail="Identifiant ou mot de passe incorrect.")
    throttle.reset(username)
    return account


def _serializer(settings: Settings) -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(settings.session_secret, salt="majal-session")


def create_session_token(account: Account) -> str:
    return _serializer(get_settings()).dumps({"u": account.username})


def account_from_request(request: Request) -> Account | None:
    token = request.cookies.get(SESSION_COOKIE)
    if not token:
        return None
    settings = get_settings()
    try:
        data = _serializer(settings).loads(token, max_age=settings.session_max_age_hours * 3600)
    except BadSignature:
        return None
    username = data.get("u") if isinstance(data, dict) else None
    if not isinstance(username, str) or not _password_for(username, settings):
        return None  # account removed or disabled since the session was opened
    return ACCOUNTS.get(username)


def require_account(request: Request) -> Account:
    account = account_from_request(request)
    if account is None:
        raise HTTPException(status_code=401, detail="Connexion requise.")
    return account
