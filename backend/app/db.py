from dataclasses import dataclass
from functools import lru_cache

from sqlalchemy import Engine, create_engine, text
from sqlalchemy.exc import SQLAlchemyError

from app.settings import get_settings


@lru_cache
def get_engine() -> Engine:
    return create_engine(
        get_settings().database_url,
        pool_pre_ping=True,
        connect_args={"connect_timeout": 2},
    )


@dataclass(frozen=True)
class DatabaseStatus:
    ok: bool
    postgis: str | None
    pgvector: str | None
    message: str


def check_database() -> DatabaseStatus:
    """Check that the database answers and that PostGIS and pgvector are installed."""
    try:
        with get_engine().connect() as conn:
            postgis = conn.execute(text("SELECT postgis_lib_version()")).scalar_one()
            pgvector = conn.execute(
                text("SELECT extversion FROM pg_extension WHERE extname = 'vector'")
            ).scalar_one_or_none()
    except SQLAlchemyError as exc:
        return DatabaseStatus(
            False, None, None, f"Base de données injoignable : {exc.__class__.__name__}"
        )
    if pgvector is None:
        return DatabaseStatus(False, postgis, None, "Extension pgvector absente")
    return DatabaseStatus(True, postgis, pgvector, "Base de données opérationnelle")
