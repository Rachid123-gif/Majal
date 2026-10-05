"""Facilities (schools, health, markets, transport, parks…) from OpenStreetMap."""

from collections import Counter
from typing import Any, cast

from geoalchemy2.shape import from_shape
from pydantic import BaseModel, ConfigDict, ValidationError
from sqlalchemy import CursorResult, text

from app.config_loader.errors import ConfigError
from app.config_loader.facility_mapping import load_facility_mapping
from app.ingestion import overpass
from app.ingestion.common import (
    ImportContext,
    ImportFailure,
    ImportResult,
    bbox_clause,
    upsert_rows,
    upsert_source,
)
from app.ingestion.osm_geometry import element_geometry
from app.models import Badge, Facility
from app.settings import get_settings


class FacilityParams(BaseModel):
    model_config = ConfigDict(extra="ignore")
    mapping: str


def run(ctx: ImportContext) -> ImportResult:
    config = ctx.territory
    try:
        params = FacilityParams.model_validate(config.sources["facilities"].model_dump())
    except ValidationError as exc:
        raise ImportFailure(f"Paramètres de « sources > facilities » incorrects : {exc}") from None
    try:
        mapping = load_facility_mapping(get_settings().config_dir.parent / params.mapping)
    except ConfigError as exc:
        raise ImportFailure(exc.format()) from None

    top_level = next(m.level for scope in config.scopes for m in scope.members)
    bbox = bbox_clause(ctx.session, ctx.study_area.id, top_level.value)
    selectors = "".join(
        f'nwr["{key}"="{value}"];'
        for category in mapping.enabled
        for key, value in category.tag_pairs()
    )
    query = f"[out:json][timeout:300]{bbox};({selectors});out geom;"
    raw = overpass.fetch(query, ctx.raw_dir / "osm_facilities.json", ctx.refresh)

    source = upsert_source(
        ctx.session,
        f"osm_facilities:{config.code}",
        name="OpenStreetMap — équipements",
        producer="Contributeurs OpenStreetMap",
        url="https://www.openstreetmap.org",
        license="ODbL 1.0",
        badge=Badge.open,
        retrieved_at=raw.retrieved_at,
        published_at=raw.osm_base,
        notes=f"Catégories : correspondance {mapping.mapping_version} ({mapping.status}). "
        "Complétude variable selon les quartiers.",
    )
    rows = []
    counts: Counter[str] = Counter()
    skipped = 0
    for element in raw.data["elements"]:
        tags = element.get("tags", {})
        category = mapping.classify(tags)
        geom = element_geometry(element)
        if category is None or geom is None:
            skipped += 1
            continue
        counts[category.code] += 1
        rows.append(
            {
                "study_area_id": ctx.study_area.id,
                "external_id": f"osm:{element['type']}/{element['id']}",
                "category": category.code,
                "subcategory": next(
                    (f"{k}={tags[k]}" for k, v in category.tag_pairs() if tags.get(k) == v), None
                ),
                "name": tags.get("name:fr") or tags.get("name"),
                "name_ar": tags.get("name:ar"),
                "geom": from_shape(geom, srid=4326),
                "source_id": source.id,
            }
        )
    if not rows:
        raise ImportFailure("Aucun équipement trouvé : vérifiez le fichier de correspondance.")
    count = upsert_rows(
        ctx.session, Facility, rows, study_area_id=ctx.study_area.id, source_id=source.id
    )
    ctx.session.execute(
        text(
            """
            UPDATE facilities f SET
              area_m2 = CASE WHEN GeometryType(f.geom) IN ('POLYGON', 'MULTIPOLYGON')
                             THEN ST_Area(f.geom::geography) END,
              territory_id = (
                SELECT t.id FROM territories t
                WHERE t.study_area_id = f.study_area_id AND t.is_analysis_unit
                  AND ST_Contains(t.geom, ST_PointOnSurface(f.geom))
                LIMIT 1)
            WHERE f.study_area_id = :sa
            """
        ),
        {"sa": ctx.study_area.id},
    )
    # The download covers a rectangle: drop what lies outside the territory's units.
    outside_result = ctx.session.execute(
        text("DELETE FROM facilities WHERE study_area_id = :sa AND territory_id IS NULL"),
        {"sa": ctx.study_area.id},
    )
    outside = cast(CursorResult[Any], outside_result).rowcount
    count -= outside
    for code in list(counts):
        counts[code] = ctx.session.execute(
            text("SELECT count(*) FROM facilities WHERE study_area_id = :sa AND category = :c"),
            {"sa": ctx.study_area.id, "c": code},
        ).scalar_one()
    warnings: list[str] = []
    labels = {c.code: c.label.fr.lower() for c in mapping.categories}
    detail = ", ".join(f"{n} {labels[code]}" for code, n in counts.most_common())
    summary = (
        f"Équipements : {count} importés ({detail})"
        f"{' (depuis le cache)' if raw.from_cache else ''}."
    )
    return ImportResult(summary, dict(counts), warnings, str(raw.path), count)
