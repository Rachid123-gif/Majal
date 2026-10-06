"""Run the importers declared in a territory file, in order, and log each run."""

from collections.abc import Callable
from datetime import UTC, datetime

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.config_loader.territory import TerritoryConfig
from app.ingestion import boundaries, facilities, ghsl, hcp_census, places, roads
from app.ingestion.common import ImportContext, ImportFailure, ImportResult
from app.ingestion.overpass import OverpassError
from app.models import ImportRun, StudyArea
from app.settings import get_settings

Importer = Callable[[ImportContext], ImportResult]

# Importers run inside the backend. `basemap_pmtiles` is run by `make data` with the
# go-pmtiles tool (scripts/fetch_basemap.sh), because it needs its own container.
IMPORTERS: dict[str, Importer] = {
    "osm_boundaries": boundaries.run,
    "osm_facilities": facilities.run,
    "osm_roads": roads.run,
    "osm_places": places.run,
    "hcp_census": hcp_census.run,
    "ghsl_grids": ghsl.run,
}
EXTERNAL_IMPORTERS = {"basemap_pmtiles"}
# The census comes right after the boundaries: the population grid is scaled to its totals.
ORDER = [
    "osm_boundaries",
    "hcp_census",
    "osm_facilities",
    "osm_roads",
    "osm_places",
    "ghsl_grids",
]


def upsert_study_area(session: Session, config: TerritoryConfig) -> StudyArea:
    area = session.scalars(select(StudyArea).where(StudyArea.code == config.code)).one_or_none()
    if area is None:
        area = StudyArea(code=config.code)
        session.add(area)
    area.name_fr = config.name.fr
    area.name_ar = config.name.ar
    area.indicator_profile = config.profiles.indicators
    area.taxonomy_profile = config.profiles.taxonomy
    area.config = config.model_dump(mode="json")
    session.flush()
    return area


def run_territory(
    session: Session,
    config: TerritoryConfig,
    *,
    refresh: bool = False,
    only: set[str] | None = None,
    report: Callable[[str], None] = print,
) -> bool:
    """Return True when every importer succeeded."""
    importers = [s.importer for s in config.sources.values()]
    unknown = sorted(set(importers) - set(IMPORTERS) - EXTERNAL_IMPORTERS)
    if unknown:
        report(f"✗ Importeur inconnu dans {config.code}.yaml : {', '.join(unknown)}")
        return False
    planned = [i for i in ORDER if i in importers and (only is None or i in only)]
    if not planned:
        report(f"- {config.name.fr} : aucune source à importer pour l'instant.")
        return True

    study_area = upsert_study_area(session, config)
    session.commit()
    raw_dir = get_settings().data_dir / "raw" / config.code
    ok = True
    for name in planned:
        run = ImportRun(study_area_code=config.code, importer=name, status="running")
        session.add(run)
        session.commit()
        ctx = ImportContext(session, config, study_area, raw_dir, refresh)
        try:
            result = IMPORTERS[name](ctx)
        except (ImportFailure, OverpassError) as exc:
            session.rollback()
            run = session.merge(run)
            run.status, run.summary = "failed", str(exc)
            run.finished_at = datetime.now(UTC)
            session.commit()
            report(f"✗ {config.name.fr} — {exc}")
            ok = False
            break  # later importers depend on earlier ones
        run.status, run.summary = "success", result.summary
        run.counts, run.warnings = result.counts, result.warnings
        run.raw_file, run.rows = result.raw_file, result.rows
        run.finished_at = datetime.now(UTC)
        session.commit()
        suffix = ""
        if result.warnings:
            n = len(result.warnings)
            suffix = f" {n} avertissement{'s' if n > 1 else ''} :"
        report(f"✓ {config.name.fr} — {result.summary}{suffix}")
        for warning in result.warnings[:10]:
            report(f"    · {warning}")
        if len(result.warnings) > 10:
            report(f"    · … et {len(result.warnings) - 10} autres (voir import_runs).")
    return ok


def study_area_bbox(session: Session, code: str, pad: float = 0.03) -> tuple[float, ...] | None:
    row = session.execute(
        text(
            "SELECT ST_XMin(e), ST_YMin(e), ST_XMax(e), ST_YMax(e) FROM ("
            " SELECT ST_Extent(t.geom) AS e FROM territories t"
            " JOIN study_areas s ON s.id = t.study_area_id WHERE s.code = :code) q"
        ),
        {"code": code},
    ).one()
    if row[0] is None:
        return None
    return (row[0] - pad, row[1] - pad, row[2] + pad, row[3] + pad)
