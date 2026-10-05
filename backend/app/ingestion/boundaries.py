"""Administrative boundaries from OpenStreetMap (badge « Ouvert »)."""

import re
from dataclasses import dataclass
from typing import Any

from geoalchemy2.shape import from_shape
from pydantic import BaseModel, ConfigDict, ValidationError
from shapely.geometry import MultiPolygon
from sqlalchemy import text

from app.config_loader.territory import LevelKind, TerritoryConfig
from app.ingestion import overpass
from app.ingestion.common import (
    ImportContext,
    ImportFailure,
    ImportResult,
    normalize,
    upsert_rows,
    upsert_source,
)
from app.ingestion.osm_geometry import relation_polygon
from app.models import Badge, Territory

PLURAL_FR = {
    LevelKind.region: "régions",
    LevelKind.prefecture: "préfectures",
    LevelKind.province: "provinces",
    LevelKind.commune: "communes",
    LevelKind.arrondissement: "arrondissements",
    LevelKind.quartier: "quartiers",
    LevelKind.douar: "douars",
    LevelKind.grid: "carreaux",
}
ADMIN_PREFIX = re.compile(r"^(prefecture|province)\s+(de\s+|d\s+)?")


class BoundaryParams(BaseModel):
    model_config = ConfigDict(extra="ignore")
    admin_levels: dict[LevelKind, int]


@dataclass(eq=False)
class Unit:
    osm_id: int
    level: LevelKind
    name_fr: str
    name_ar: str | None
    geom: MultiPolygon
    parent: "Unit | None" = None
    scopes: tuple[str, ...] = ()
    is_analysis_unit: bool = False

    @property
    def external_id(self) -> str:
        return f"osm:relation/{self.osm_id}"


def _clean(name: str, prefixes: list[str]) -> str:
    """Remove a leading level word (« Arrondissement », « مقاطعة ») that OSM sometimes adds."""
    for prefix in prefixes:
        if name.lower().startswith(prefix.lower() + " ") and len(name) > len(prefix) + 1:
            return name[len(prefix) + 1 :].strip()
    return name


def match_top_units(elements: list[dict[str, Any]], wanted: set[str]) -> dict[str, int]:
    """Map each wanted (normalized) name to the OSM relation id of the matching unit."""
    matches: dict[str, int] = {}
    for element in elements:
        tags = element.get("tags", {})
        for candidate in {tags.get("name:fr"), tags.get("name")} - {None}:
            key = ADMIN_PREFIX.sub("", normalize(str(candidate)))
            if key in wanted:
                matches[key] = element["id"]
    return matches


def assemble_units(
    elements: list[dict[str, Any]],
    matches: dict[str, int],
    config: TerritoryConfig,
    params: BoundaryParams,
    top_level: LevelKind,
) -> tuple[list[Unit], list[str]]:
    """Pure step (no database): geometries, clean names, hierarchy, scopes, analysis units."""
    by_number = {n: lvl for lvl, n in params.admin_levels.items()}
    terms = config.analysis_levels.main.terms
    warnings: list[str] = []
    units: list[Unit] = []
    for element in elements:
        tags = element.get("tags", {})
        level = by_number.get(int(tags.get("admin_level", 0)))
        if level is None:
            continue
        geom = relation_polygon(element)
        name = tags.get("name:fr") or tags.get("name")
        if geom is None or not name:
            warnings.append(
                f"Limite ignorée (géométrie ou nom manquant) : relation {element['id']}."
            )
            continue
        term = terms.get(level)
        name_ar = tags.get("name:ar")
        units.append(
            Unit(
                osm_id=element["id"],
                level=level,
                name_fr=_clean(name, [term.fr] if term else []),
                name_ar=_clean(name_ar, [term.ar] if term else []) if name_ar else None,
                geom=geom,
            )
        )

    tops = [u for u in units if u.level == top_level and u.osm_id in matches.values()]
    top_area = MultiPolygon([p for u in tops for p in u.geom.geoms]).buffer(0.0005)
    # Overpass area queries can return neighbours that only touch the border: keep units
    # whose interior point lies inside the selected top-level units.
    units = [u for u in units if u in tops or top_area.contains(u.geom.representative_point())]

    # 3. Hierarchy: the parent is the closest higher level containing the unit.
    order = sorted(params.admin_levels, key=lambda lvl: params.admin_levels[lvl])
    for unit in units:
        rank = order.index(unit.level)
        point = unit.geom.representative_point()
        for higher in reversed(order[:rank]):
            parent = next(
                (u for u in units if u.level == higher and u.geom.buffer(0.0005).contains(point)),
                None,
            )
            if parent:
                unit.parent = parent
                break

    # 4. Scopes and analysis units (generic rules, driven by the territory file).
    top_by_key = {
        key: next(u for u in tops if u.osm_id == osm_id) for key, osm_id in matches.items()
    }
    for unit in units:
        root = unit
        while root.parent is not None:
            root = root.parent
        unit.scopes = tuple(
            scope.code
            for scope in config.scopes
            if any(top_by_key[normalize(m.name_fr)] is root for m in scope.members)
        )
    main_levels = set(config.analysis_levels.main.levels)
    for unit in units:
        has_main_children = any(u.parent is unit and u.level in main_levels for u in units)
        unit.is_analysis_unit = unit.level in main_levels and not has_main_children
        if unit.name_ar is None:
            warnings.append(f"Nom arabe absent dans OpenStreetMap : {unit.name_fr}.")

    return units, warnings


def run(ctx: ImportContext) -> ImportResult:
    config = ctx.territory
    try:
        params = BoundaryParams.model_validate(config.sources["boundaries"].model_dump())
    except ValidationError as exc:
        raise ImportFailure(f"Paramètres de « sources > boundaries » incorrects : {exc}") from None

    member_levels = {m.level for scope in config.scopes for m in scope.members}
    if len(member_levels) != 1:
        raise ImportFailure("Tous les « members » des périmètres doivent être du même niveau.")
    top_level = member_levels.pop()
    if top_level not in params.admin_levels:
        raise ImportFailure(f"« admin_levels » doit indiquer le niveau OSM de « {top_level} ».")
    wanted = {normalize(m.name_fr) for scope in config.scopes for m in scope.members}

    # 1. Find the top-level units (prefectures / provinces) by name.
    top_query = (
        '[out:json][timeout:180];area["ISO3166-1"="MA"]["admin_level"="2"]->.ma;'
        f'rel["boundary"="administrative"]["admin_level"="{params.admin_levels[top_level]}"](area.ma);'
        "out tags;"
    )
    top_raw = overpass.fetch(top_query, ctx.raw_dir / "osm_admin_top.json", ctx.refresh)
    matches = match_top_units(top_raw.data["elements"], wanted)
    missing = sorted(wanted - set(matches))
    if missing:
        raise ImportFailure(
            "Unités introuvables dans OpenStreetMap : "
            + ", ".join(missing)
            + ". Vérifiez l'orthographe des « name_fr » dans les périmètres."
        )

    # 2. Download the geometries of the top units and of every sub-level inside them.
    ids = ",".join(str(i) for i in sorted(matches.values()))
    sub_levels = sorted({n for lvl, n in params.admin_levels.items() if lvl != top_level})
    level_regex = "|".join(str(n) for n in sub_levels)
    geom_query = (
        f"[out:json][timeout:300];rel(id:{ids});map_to_area->.p;"
        f'(rel["boundary"="administrative"]["admin_level"~"^({level_regex})$"](area.p);rel(id:{ids}););'
        "out geom;"
    )
    raw = overpass.fetch(geom_query, ctx.raw_dir / "osm_boundaries.json", ctx.refresh)

    units, warnings = assemble_units(raw.data["elements"], matches, config, params, top_level)
    order = sorted(params.admin_levels, key=lambda lvl: params.admin_levels[lvl])

    source = upsert_source(
        ctx.session,
        f"osm_boundaries:{config.code}",
        name="OpenStreetMap — limites administratives",
        producer="Contributeurs OpenStreetMap",
        url="https://www.openstreetmap.org",
        license="ODbL 1.0",
        badge=Badge.open,
        retrieved_at=raw.retrieved_at,
        published_at=raw.osm_base,
        notes="Limites non officielles, à vérifier par une source institutionnelle "
        "(agence urbaine, HCP). Aucun code officiel disponible.",
    )
    rows = [
        {
            "study_area_id": ctx.study_area.id,
            "external_id": u.external_id,
            "official_code": None,
            "name_fr": u.name_fr,
            "name_ar": u.name_ar,
            "level": u.level.value,
            "milieu": None,
            "is_analysis_unit": u.is_analysis_unit,
            "scopes": list(u.scopes),
            "geom": from_shape(u.geom, srid=4326),
            "source_id": source.id,
            "source_meta": {"osm_admin_level": params.admin_levels[u.level]},
        }
        for u in units
    ]
    count = upsert_rows(
        ctx.session, Territory, rows, study_area_id=ctx.study_area.id, source_id=source.id
    )
    ctx.session.execute(
        text(
            "UPDATE territories SET area_km2 = ST_Area(geom::geography) / 1e6, parent_id = NULL "
            "WHERE study_area_id = :sa"
        ),
        {"sa": ctx.study_area.id},
    )
    for unit in units:
        if unit.parent:
            ctx.session.execute(
                text(
                    "UPDATE territories t SET parent_id = p.id FROM territories p "
                    "WHERE t.study_area_id = :sa AND p.study_area_id = :sa "
                    "AND t.external_id = :child AND p.external_id = :parent"
                ),
                {
                    "sa": ctx.study_area.id,
                    "child": unit.external_id,
                    "parent": unit.parent.external_id,
                },
            )

    counts = {lvl.value: sum(1 for u in units if u.level == lvl) for lvl in order}
    analysis = [u for u in units if u.is_analysis_unit]
    detail = ", ".join(
        f"{n} {PLURAL_FR[lvl] if n > 1 else lvl.value}"
        for lvl, n in ((lvl, sum(1 for u in analysis if u.level == lvl)) for lvl in order)
        if n
    )
    summary = (
        f"Limites : {len(analysis)} unités d'analyse ({detail}), "
        f"{counts.get(top_level.value, 0)} {PLURAL_FR[top_level]}"
        f"{' (depuis le cache)' if raw.from_cache else ''}."
    )
    counts["analysis_units"] = len(analysis)
    return ImportResult(summary, counts, warnings, str(raw.path), count)
