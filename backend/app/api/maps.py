"""Map data: offline base-map tiles, analysis units and facilities (GeoJSON)."""

import gzip
import json
from functools import lru_cache
from pathlib import Path
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Response
from pmtiles.reader import MmapSource, Reader
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config_loader import ConfigError, load_territories
from app.config_loader.facility_mapping import load_facility_mapping
from app.config_loader.territory import TerritoryConfig
from app.db import get_engine
from app.security import Account, require_account
from app.settings import get_settings

router = APIRouter(tags=["maps"])


def _territory(code: str) -> TerritoryConfig:
    try:
        territories = load_territories(get_settings().config_dir / "territories")
    except ConfigError as exc:
        raise HTTPException(status_code=503, detail=exc.format()) from None
    if code not in territories:
        raise HTTPException(status_code=404, detail=f"Territoire inconnu : {code}.")
    return territories[code]


# ---------- Base map tiles (no login: open OpenStreetMap data, needed before login too) ----------


@lru_cache(maxsize=8)
def _reader(path: Path, mtime: float) -> tuple[Reader, Any]:
    handle = path.open("rb")
    return Reader(MmapSource(handle)), handle  # type: ignore[no-untyped-call]


def _tiles_path(code: str) -> Path:
    return get_settings().data_dir / "tiles" / f"{code}.pmtiles"


@router.get("/api/tiles/{code}/info")
def tiles_info(code: str) -> dict[str, Any]:
    _territory(code)
    path = _tiles_path(code)
    if not path.exists():
        return {"available": False}
    reader, _ = _reader(path, path.stat().st_mtime)
    header = reader.header()  # type: ignore[no-untyped-call]
    meta_file = path.with_suffix(".json")
    meta = json.loads(meta_file.read_text()) if meta_file.exists() else {}
    return {
        "available": True,
        "minzoom": header["min_zoom"],
        "maxzoom": header["max_zoom"],
        "bounds": [
            header["min_lon_e7"] / 1e7,
            header["min_lat_e7"] / 1e7,
            header["max_lon_e7"] / 1e7,
            header["max_lat_e7"] / 1e7,
        ],
        "build": meta.get("build"),
        "retrieved_at": meta.get("retrieved_at"),
        "attribution": "© OpenStreetMap contributors · Protomaps",
    }


NATIONAL = "maroc"  # national base map (Kingdom of Morocco, low zoom), see fetch_basemap.sh


def _tile_bytes(path: Path, z: int, x: int, y: int) -> bytes | None:
    if not path.exists():
        return None
    reader, _ = _reader(path, path.stat().st_mtime)
    data: bytes | None = reader.get(z, x, y)  # type: ignore[no-untyped-call]
    return data


@router.get("/api/tiles/{code}/{z}/{x}/{y}.mvt")
def tile(code: str, z: int, x: int, y: int) -> Response:
    path = _tiles_path(code)
    if not code.replace("_", "").isalnum() or not path.exists():
        raise HTTPException(status_code=404, detail="Fond de carte absent (lancez `make data`).")
    # The territory extract first, then the national map of the Kingdom when zoomed out.
    data = _tile_bytes(path, z, x, y) or _tile_bytes(_tiles_path(NATIONAL), z, x, y)
    if not data:
        return Response(status_code=204)
    if data[:2] == b"\x1f\x8b":
        data = gzip.decompress(data)
    return Response(
        data,
        media_type="application/vnd.mapbox-vector-tile",
        headers={"Cache-Control": "public, max-age=86400"},
    )


# ---------- Units and facilities (login required) ----------


def _source(session: Session, code: str) -> dict[str, Any] | None:
    row = (
        session.execute(
            text(
                "SELECT name, producer, license, default_badge, retrieved_at, published_at, notes "
                "FROM data_sources WHERE code = :code"
            ),
            {"code": code},
        )
        .mappings()
        .one_or_none()
    )
    if row is None:
        return None
    return {
        "name": row["name"],
        "producer": row["producer"],
        "license": row["license"],
        "badge": row["default_badge"],
        "retrieved_at": row["retrieved_at"].isoformat() if row["retrieved_at"] else None,
        "data_date": row["published_at"].isoformat() if row["published_at"] else None,
        "notes": row["notes"],
    }


@router.get("/api/territories/{code}/units")
def units(
    code: str,
    _: Annotated[Account, Depends(require_account)],
    scope: str | None = None,
) -> dict[str, Any]:
    config = _territory(code)
    scope_code = scope or config.default_scope.code
    if scope_code not in {s.code for s in config.scopes}:
        raise HTTPException(status_code=404, detail=f"Périmètre inconnu : {scope_code}.")
    terms = {
        level.value: {"fr": term.fr, "ar": term.ar}
        for level, term in config.analysis_levels.main.terms.items()
    }
    with Session(get_engine()) as session:
        rows = session.execute(
            text(
                """
                SELECT t.id, t.name_fr, t.name_ar, t.level, t.area_km2, t.official_code,
                       p.name_fr AS parent_fr, p.name_ar AS parent_ar,
                       ST_AsGeoJSON(ST_SimplifyPreserveTopology(t.geom, 0.0001), 6) AS geometry,
                       ST_X(ST_PointOnSurface(t.geom)) AS label_lon,
                       ST_Y(ST_PointOnSurface(t.geom)) AS label_lat,
                       COALESCE((
                         SELECT jsonb_object_agg(category, n) FROM (
                           SELECT f.category, count(*) AS n FROM facilities f
                           WHERE f.territory_id = t.id GROUP BY f.category) c
                       ), '{}'::jsonb) AS facilities
                FROM territories t
                JOIN study_areas s ON s.id = t.study_area_id
                LEFT JOIN territories p ON p.id = t.parent_id
                WHERE s.code = :code AND t.is_analysis_unit AND t.scopes ? :scope
                ORDER BY t.name_fr
                """
            ),
            {"code": code, "scope": scope_code},
        ).mappings()
        features = [
            {
                "type": "Feature",
                "id": row["id"],
                "geometry": json.loads(row["geometry"]),
                "properties": {
                    "id": row["id"],
                    "name_fr": row["name_fr"],
                    "name_ar": row["name_ar"],
                    "level": row["level"],
                    "term": terms.get(row["level"]),
                    "parent_fr": row["parent_fr"],
                    "parent_ar": row["parent_ar"],
                    "area_km2": row["area_km2"],
                    "official_code": row["official_code"],
                    "facilities": row["facilities"],
                    "label": [round(row["label_lon"], 6), round(row["label_lat"], 6)],
                },
            }
            for row in rows
        ]
        bbox = session.execute(
            text(
                "SELECT ST_XMin(e), ST_YMin(e), ST_XMax(e), ST_YMax(e) FROM ("
                "SELECT ST_Extent(t.geom) e FROM territories t JOIN study_areas s "
                "ON s.id = t.study_area_id WHERE s.code = :code AND t.is_analysis_unit "
                "AND t.scopes ? :scope) q"
            ),
            {"code": code, "scope": scope_code},
        ).one()
        source = _source(session, f"osm_boundaries:{code}")
    return {
        "type": "FeatureCollection",
        "features": features,
        "meta": {
            "imported": bool(features),
            "scope": scope_code,
            "scopes": [
                {"code": s.code, "label": s.label.model_dump(), "default": s.default}
                for s in config.scopes
            ],
            "bbox": list(bbox) if bbox[0] is not None else None,
            "source": source,
        },
    }


@router.get("/api/territories/{code}/facilities")
def facilities(
    code: str,
    _: Annotated[Account, Depends(require_account)],
    scope: str | None = None,
) -> dict[str, Any]:
    config = _territory(code)
    scope_code = scope or config.default_scope.code
    categories: list[dict[str, Any]] = []
    source_ref = config.sources.get("facilities")
    if source_ref is not None:
        mapping_path = source_ref.model_dump().get("mapping")
        if mapping_path:
            try:
                mapping = load_facility_mapping(get_settings().config_dir.parent / mapping_path)
            except ConfigError as exc:
                raise HTTPException(status_code=503, detail=exc.format()) from None
            categories = [
                {"code": c.code, "label": c.label.model_dump(), "color": c.color, "group": c.group}
                for c in mapping.enabled
            ]
    with Session(get_engine()) as session:
        rows = session.execute(
            text(
                """
                SELECT f.id, f.category, f.name, f.name_ar, f.territory_id,
                       ST_X(ST_PointOnSurface(f.geom)) AS lon,
                       ST_Y(ST_PointOnSurface(f.geom)) AS lat
                FROM facilities f
                JOIN study_areas s ON s.id = f.study_area_id
                JOIN territories t ON t.id = f.territory_id
                WHERE s.code = :code AND t.scopes ? :scope
                """
            ),
            {"code": code, "scope": scope_code},
        ).mappings()
        features: list[dict[str, Any]] = [
            {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [round(r["lon"], 6), round(r["lat"], 6)],
                },
                "properties": {
                    "id": r["id"],
                    "category": r["category"],
                    "territory_id": r["territory_id"],
                    "name": r["name"],
                    "name_ar": r["name_ar"],
                },
            }
            for r in rows
        ]
        source = _source(session, f"osm_facilities:{code}")
    counts: dict[str, int] = {}
    for feature in features:
        category = feature["properties"]["category"]
        counts[category] = counts.get(category, 0) + 1
    for category in categories:
        category["count"] = counts.get(category["code"], 0)
    return {
        "type": "FeatureCollection",
        "features": features,
        "meta": {"categories": categories, "source": source},
    }
