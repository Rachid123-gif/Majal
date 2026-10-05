"""Shared helpers for importers: context, results, upserts, name matching."""

import re
import unicodedata
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, cast

from sqlalchemy import Table, delete, select, text, tuple_
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.config_loader.territory import TerritoryConfig
from app.models import DataSource, StudyArea
from app.models.base import Base


class ImportFailure(RuntimeError):
    """Error explained in French, shown as is to the user."""


@dataclass
class ImportContext:
    session: Session
    territory: TerritoryConfig
    study_area: StudyArea
    raw_dir: Path
    refresh: bool = False


@dataclass
class ImportResult:
    summary: str
    counts: dict[str, int] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    raw_file: str | None = None
    rows: int = 0


def normalize(text: str) -> str:
    """Accent-, case- and punctuation-insensitive form used to match names."""
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def upsert_source(
    session: Session,
    code: str,
    *,
    name: str,
    producer: str,
    url: str,
    license: str,
    badge: str,
    retrieved_at: datetime,
    notes: str,
    published_at: datetime | None = None,
) -> DataSource:
    source = session.scalars(select(DataSource).where(DataSource.code == code)).one_or_none()
    if source is None:
        source = DataSource(code=code)
        session.add(source)
    source.name = name
    source.producer = producer
    source.url = url
    source.license = license
    source.default_badge = badge
    source.retrieved_at = retrieved_at
    source.published_at = published_at
    source.notes = notes
    session.flush()
    return source


def upsert_rows(
    session: Session,
    model: type[Base],
    rows: Sequence[dict[str, Any]],
    *,
    study_area_id: int,
    source_id: int,
    batch: int = 1000,
) -> int:
    """Insert or update by (study_area_id, external_id); remove rows no longer in the source.

    Re-running an import therefore never creates duplicates.
    """
    table = cast(Table, model.__table__)
    update_columns = (
        [c for c in rows[0] if c not in ("study_area_id", "external_id")] if rows else []
    )
    for start in range(0, len(rows), batch):
        chunk = rows[start : start + batch]
        statement = insert(table).values(chunk)
        statement = statement.on_conflict_do_update(
            index_elements=["study_area_id", "external_id"],
            set_={c: statement.excluded[c] for c in update_columns},
        )
        session.execute(statement)
    keep = {row["external_id"] for row in rows}
    existing = session.execute(
        select(table.c.external_id).where(
            table.c.study_area_id == study_area_id, table.c.source_id == source_id
        )
    ).scalars()
    stale = [external_id for external_id in existing if external_id not in keep]
    for start in range(0, len(stale), batch):
        session.execute(
            delete(table).where(
                tuple_(table.c.study_area_id, table.c.external_id).in_(
                    [(study_area_id, e) for e in stale[start : start + batch]]
                )
            )
        )
    return len(rows)


def bbox_clause(session: Session, study_area_id: int, level: str, pad: float = 0.01) -> str:
    """Overpass global bbox of the imported top-level units (much faster than area queries)."""
    row = session.execute(
        text(
            "SELECT ST_YMin(e), ST_XMin(e), ST_YMax(e), ST_XMax(e) FROM ("
            "SELECT ST_Extent(geom) AS e FROM territories "
            "WHERE study_area_id = :sa AND level = :level) q"
        ),
        {"sa": study_area_id, "level": level},
    ).one()
    if row[0] is None:
        raise ImportFailure(
            "Les limites administratives doivent être importées avant cette étape "
            "(lancez `make data`)."
        )
    s, w, n, e = row
    return f"[bbox:{s - pad:.5f},{w - pad:.5f},{n + pad:.5f},{e + pad:.5f}]"
