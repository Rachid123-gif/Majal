from functools import lru_cache
from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """Runtime settings, read from environment variables (and `.env` at the repo root)."""

    model_config = SettingsConfigDict(env_file=REPO_ROOT / ".env", extra="ignore")

    app_env: str = "development"
    database_url: str = "postgresql+psycopg://majal:majal@localhost:5432/majal"
    config_dir: Path = REPO_ROOT / "config"
    data_dir: Path = REPO_ROOT / "data"
    # Public Overpass servers, tried in turn (the main one is often overloaded).
    overpass_urls: list[str] = [
        "https://overpass-api.de/api/interpreter",
        "https://overpass.private.coffee/api/interpreter",
    ]
    cors_origins: list[str] = ["http://localhost:3000"]

    # Sessions: cookie signed with this secret (set a long random value in .env).
    session_secret: str = "dev-only-insecure-secret"
    session_max_age_hours: int = 12
    # Demo accounts (stage 0 bis). An empty password disables the account.
    demo_professeur_password: str = ""
    demo_presentateur_password: str = ""

    @field_validator("session_secret")
    @classmethod
    def empty_secret_means_default(cls, value: str) -> str:
        return value or "dev-only-insecure-secret"


@lru_cache
def get_settings() -> Settings:
    return Settings()
