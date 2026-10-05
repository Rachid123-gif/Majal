"""Road network from OpenStreetMap (main roads and rural tracks)."""

from collections import Counter
from typing import Any, cast

from geoalchemy2.shape import from_shape
from pydantic import BaseModel, ConfigDict, Field, ValidationError
from sqlalchemy import CursorResult, text

from app.ingestion import overpass
from app.ingestion.common import (
    ImportContext,
    ImportFailure,
    ImportResult,
    bbox_clause,
    upsert_rows,
    upsert_source,
)
from app.ingestion.osm_geometry import way_line
from app.models import Badge, Road

PAVED = {
    "paved",
    "asphalt",
    "concrete",
    "concrete:plates",
    "concrete:lanes",
    "paving_stones",
    "sett",
}
UNPAVED = {
    "unpaved",
    "gravel",
    "fine_gravel",
    "dirt",
    "earth",
    "ground",
    "compacted",
    "sand",
    "mud",
}


class RoadParams(BaseModel):
    model_config = ConfigDict(extra="ignore")
    highway: list[str] = Field(min_length=1)


def run(ctx: ImportContext) -> ImportResult:
    config = ctx.territory
    try:
        params = RoadParams.model_validate(config.sources["roads"].model_dump())
    except ValidationError as exc:
        raise ImportFailure(f"Paramètres de « sources > roads » incorrects : {exc}") from None
    top_level = next(m.level for scope in config.scopes for m in scope.members)
    bbox = bbox_clause(ctx.session, ctx.study_area.id, top_level.value)
    pattern = "|".join(params.highway)
    query = f'[out:json][timeout:300]{bbox};way["highway"~"^({pattern})$"];out geom;'
    raw = overpass.fetch(query, ctx.raw_dir / "osm_roads.json", ctx.refresh)
    source = upsert_source(
        ctx.session,
        f"osm_roads:{config.code}",
        name="OpenStreetMap — réseau routier",
        producer="Contributeurs OpenStreetMap",
        url="https://www.openstreetmap.org",
        license="ODbL 1.0",
        badge=Badge.open,
        retrieved_at=raw.retrieved_at,
        published_at=raw.osm_base,
        notes="Revêtement déduit de l'étiquette « surface » quand elle existe.",
    )
    rows = []
    counts: Counter[str] = Counter()
    for element in raw.data["elements"]:
        line = way_line(element)
        if line is None:
            continue
        tags = element.get("tags", {})
        surface = tags.get("surface")
        counts[tags["highway"]] += 1
        rows.append(
            {
                "study_area_id": ctx.study_area.id,
                "external_id": f"osm:way/{element['id']}",
                "highway": tags["highway"],
                "surface": surface,
                "paved": True if surface in PAVED else False if surface in UNPAVED else None,
                "name": tags.get("name:fr") or tags.get("name"),
                "geom": from_shape(line, srid=4326),
                "source_id": source.id,
            }
        )
    if not rows:
        raise ImportFailure("Aucune route trouvée dans la zone.")
    count = upsert_rows(
        ctx.session, Road, rows, study_area_id=ctx.study_area.id, source_id=source.id
    )
    # The download covers a rectangle: drop roads that do not touch the territory.
    removed_result = ctx.session.execute(
        text(
            "DELETE FROM roads r WHERE r.study_area_id = :sa AND NOT EXISTS ("
            "SELECT 1 FROM territories t WHERE t.study_area_id = :sa AND t.level = :level "
            "AND ST_Intersects(t.geom, r.geom))"
        ),
        {"sa": ctx.study_area.id, "level": top_level.value},
    )
    removed = cast(CursorResult[Any], removed_result).rowcount
    count -= removed
    ctx.session.execute(
        text("UPDATE roads SET length_m = ST_Length(geom::geography) WHERE study_area_id = :sa"),
        {"sa": ctx.study_area.id},
    )
    km = ctx.session.execute(
        text("SELECT coalesce(sum(length_m), 0) / 1000 FROM roads WHERE study_area_id = :sa"),
        {"sa": ctx.study_area.id},
    ).scalar_one()
    summary = (
        f"Routes : {count} tronçons, "
        + f"{km:,.0f}".replace(",", "\u202f")
        + " km"
        + f"{' (depuis le cache)' if raw.from_cache else ''}."
    )
    return ImportResult(summary, dict(counts), [], str(raw.path), count)
