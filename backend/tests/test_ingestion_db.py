"""Integration test against PostGIS (skipped when the database is not running)."""

from collections.abc import Iterator
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config_loader.territory import load_territory
from app.db import check_database, get_engine
from app.ingestion import overpass
from app.ingestion.runner import run_territory
from app.settings import REPO_ROOT
from tests.osm_fixtures import GEOMETRY, TOP

CODE = "test_idempotence"

pytestmark = pytest.mark.skipif(
    not check_database().ok, reason="base PostGIS non disponible (lancez `make start`)"
)


@pytest.fixture
def session(monkeypatch: pytest.MonkeyPatch) -> Iterator[Session]:
    def fake_fetch(query: str, cache_path: Path, refresh: bool = False) -> overpass.RawResponse:
        elements: list[Any] = TOP if "out tags" in query else GEOMETRY
        data = {"elements": elements, "osm3s": {"timestamp_osm_base": "2026-07-15T15:22:01Z"}}
        return overpass.RawResponse(data, cache_path, datetime.now(UTC), from_cache=False)

    monkeypatch.setattr(overpass, "fetch", fake_fetch)
    with Session(get_engine()) as db:
        yield db
        db.execute(text("DELETE FROM study_areas WHERE code = :c"), {"c": CODE})
        db.execute(text("DELETE FROM data_sources WHERE code LIKE :c"), {"c": f"%:{CODE}"})
        db.execute(text("DELETE FROM import_runs WHERE study_area_code = :c"), {"c": CODE})
        db.commit()


def test_boundary_import_is_idempotent(session: Session, tmp_path: Path) -> None:
    rabat = load_territory(REPO_ROOT / "config" / "territories" / "rabat.yaml")
    config = rabat.model_copy(
        update={
            "code": CODE,
            "scopes": [s for s in rabat.scopes if s.code == "prefecture"]
            + [
                rabat.scopes[0].model_copy(
                    update={
                        "members": [
                            m for m in rabat.scopes[0].members if m.name_fr != "Skhirate-Témara"
                        ]
                    }
                )
            ],
            "sources": {"boundaries": rabat.sources["boundaries"]},
        }
    )
    messages: list[str] = []

    def count() -> tuple[int, int]:
        return session.execute(
            text(
                "SELECT count(*), count(*) FILTER (WHERE is_analysis_unit) FROM territories t "
                "JOIN study_areas s ON s.id = t.study_area_id WHERE s.code = :c"
            ),
            {"c": CODE},
        ).one()

    assert run_territory(session, config, report=messages.append)
    first = count()
    assert run_territory(session, config, report=messages.append)
    assert count() == first == (7, 4)  # 2 prefectures, 3 communes, 2 arrondissements
    assert all(m.startswith("✓") for m in messages if "Limites" in m)
    area = session.execute(
        text(
            "SELECT round(t.area_km2) FROM territories t JOIN study_areas s "
            "ON s.id = t.study_area_id WHERE s.code = :c AND t.name_fr = 'Hassan'"
        ),
        {"c": CODE},
    ).scalar_one()
    assert area > 20000  # a 1°x2° square near the equator, measured on the ellipsoid
    published = session.execute(
        text("SELECT published_at FROM data_sources WHERE code = :c"),
        {"c": f"osm_boundaries:{CODE}"},
    ).scalar_one()
    assert published.year == 2026 and published.month == 7
