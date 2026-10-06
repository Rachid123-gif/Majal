"""Named places from OpenStreetMap (neighbourhoods, squares…): the gazetteer used to locate
what citizens mention. Each place is attached to the analysis unit that contains it."""

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
from app.ingestion.osm_geometry import element_geometry
from app.models import Badge, Place


class PlaceParams(BaseModel):
    model_config = ConfigDict(extra="ignore")
    place: list[str] = Field(min_length=1)


def _names(tags: dict[str, Any]) -> tuple[str | None, str | None, list[str]]:
    name = tags.get("name:fr") or tags.get("name")
    name_ar = tags.get("name:ar")
    alternatives = {
        tags[k]
        for k in ("name", "name:fr", "name:en", "alt_name", "old_name", "short_name", "name:zgh")
        if tags.get(k)
    }
    for key in ("alt_name", "old_name"):
        for value in (tags.get(key) or "").split(";"):
            if value.strip():
                alternatives.add(value.strip())
    alternatives.discard(name or "")
    return name, name_ar, sorted(alternatives)


def run(ctx: ImportContext) -> ImportResult:
    config = ctx.territory
    try:
        params = PlaceParams.model_validate(config.sources["places"].model_dump())
    except ValidationError as exc:
        raise ImportFailure(f"Paramètres de « sources > places » incorrects : {exc}") from None
    top_level = next(m.level for scope in config.scopes for m in scope.members)
    bbox = bbox_clause(ctx.session, ctx.study_area.id, top_level.value)
    pattern = "|".join(params.place)
    query = (
        f"[out:json][timeout:300]{bbox};"
        f'(node["place"~"^({pattern})$"]["name"];way["place"~"^({pattern})$"]["name"];);'
        "out geom;"
    )
    raw = overpass.fetch(query, ctx.raw_dir / "osm_places.json", ctx.refresh)
    source = upsert_source(
        ctx.session,
        f"osm_places:{config.code}",
        name="OpenStreetMap — lieux nommés (quartiers, places)",
        producer="Contributeurs OpenStreetMap",
        url="https://www.openstreetmap.org",
        license="ODbL 1.0",
        badge=Badge.open,
        retrieved_at=raw.retrieved_at,
        published_at=raw.osm_base,
        notes="Sert à rattacher les lieux cités par les citoyens à une unité d'analyse.",
    )
    rows = []
    counts: Counter[str] = Counter()
    for element in raw.data["elements"]:
        tags = element.get("tags", {})
        name, name_ar, alternatives = _names(tags)
        geometry = element_geometry(element)
        if not name or geometry is None:
            continue
        counts[tags["place"]] += 1
        rows.append(
            {
                "study_area_id": ctx.study_area.id,
                "external_id": f"osm:{element['type']}/{element['id']}",
                "kind": tags["place"],
                "name": name,
                "name_ar": name_ar,
                "alt_names": alternatives,
                "geom": from_shape(geometry.representative_point(), srid=4326),
                "source_id": source.id,
            }
        )
    if not rows:
        raise ImportFailure("Aucun lieu nommé trouvé dans la zone.")
    count = upsert_rows(
        ctx.session, Place, rows, study_area_id=ctx.study_area.id, source_id=source.id
    )
    # Attach each place to the analysis unit that contains it; drop those outside the territory.
    ctx.session.execute(
        text(
            "UPDATE places p SET territory_id = t.id FROM territories t "
            "WHERE p.study_area_id = :sa AND t.study_area_id = :sa AND t.is_analysis_unit "
            "AND ST_Contains(t.geom, p.geom)"
        ),
        {"sa": ctx.study_area.id},
    )
    removed = cast(
        CursorResult[Any],
        ctx.session.execute(
            text("DELETE FROM places WHERE study_area_id = :sa AND territory_id IS NULL"),
            {"sa": ctx.study_area.id},
        ),
    ).rowcount
    count -= removed
    summary = (
        f"Lieux nommés : {count} rattachés à une unité"
        f"{' (depuis le cache)' if raw.from_cache else ''}."
    )
    return ImportResult(summary, dict(counts), [], str(raw.path), count)
