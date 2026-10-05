from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel

from app import __version__
from app.config_loader import ConfigError, load_territories
from app.db import check_database
from app.settings import get_settings

router = APIRouter(tags=["health"])


class DatabaseHealth(BaseModel):
    ok: bool
    postgis: str | None
    pgvector: str | None
    message: str


class ConfigHealth(BaseModel):
    ok: bool
    territories: int
    message: str


class Health(BaseModel):
    status: Literal["ok", "degraded"]
    version: str
    database: DatabaseHealth
    config: ConfigHealth


@router.get("/health")
def health() -> Health:
    db = check_database()
    try:
        count = len(load_territories(get_settings().config_dir / "territories"))
        config = ConfigHealth(ok=True, territories=count, message="Configuration valide")
    except ConfigError as exc:
        config = ConfigHealth(ok=False, territories=0, message=exc.format())
    return Health(
        status="ok" if db.ok and config.ok else "degraded",
        version=__version__,
        database=DatabaseHealth(**db.__dict__),
        config=config,
    )
