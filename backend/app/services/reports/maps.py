"""Report maps, drawn by MAJAL from its own data (no base map).

Territorial integrity (non-negotiable, see CLAUDE.md): the inset shows the Kingdom of Morocco
in its entirety, southern provinces included, from the Natural Earth « point of view of
Morocco » reference contour (data/reference/maroc-natural-earth-pov.geojson). No other
national or regional boundary is drawn.
"""

import io
import json
import math
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from geoalchemy2.shape import to_shape
from matplotlib.axes import Axes
from shapely.geometry import MultiPolygon, Polygon, shape
from shapely.geometry.base import BaseGeometry
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.models import Territory
from app.settings import get_settings

PETROL, TERRACOTTA, CREAM, SLATE = "#12343b", "#a8461f", "#f6f3ec", "#4a5560"


def kingdom_contour() -> BaseGeometry:
    path: Path = get_settings().data_dir / "reference" / "maroc-natural-earth-pov.geojson"
    return shape(json.loads(path.read_text(encoding="utf-8"))["geometry"])


def _polygons(geom: BaseGeometry) -> list[Polygon]:
    if isinstance(geom, Polygon):
        return [geom]
    if isinstance(geom, MultiPolygon):
        return list(geom.geoms)
    return [g for g in getattr(geom, "geoms", []) if isinstance(g, Polygon)]


def _draw(ax: Axes, geom: BaseGeometry, **style: Any) -> None:
    for polygon in _polygons(geom):
        xs, ys = polygon.exterior.xy
        ax.fill(xs, ys, **style)


def kingdom_inset(fig: Any, lon: float, lat: float) -> Axes:
    """Inset: the Kingdom of Morocco in its entirety, with the location of the unit."""
    inset: Axes = fig.add_axes((0.74, 0.08, 0.22, 0.34))
    inset.set_facecolor("#ffffff")
    _draw(inset, kingdom_contour(), facecolor=CREAM, edgecolor=PETROL, linewidth=0.6)
    inset.plot([lon], [lat], "o", color=TERRACOTTA, markersize=4)
    inset.set_aspect(1 / math.cos(math.radians(28)))
    inset.set_xticks([])
    inset.set_yticks([])
    return inset


def unit_map_png(session: Session, unit_id: int, lang: str = "fr") -> bytes:
    unit = session.get(Territory, unit_id)
    if unit is None:
        raise LookupError("Unité inconnue.")
    others = session.scalars(
        select(Territory).where(
            Territory.study_area_id == unit.study_area_id, Territory.is_analysis_unit
        )
    ).all()
    points = session.execute(
        text(
            "SELECT ST_X(ST_PointOnSurface(geom)), ST_Y(ST_PointOnSurface(geom)) "
            "FROM facilities WHERE territory_id = :id"
        ),
        {"id": unit_id},
    ).all()
    target = to_shape(unit.geom)
    lat = target.centroid.y
    aspect = 1 / math.cos(math.radians(lat))

    fig = plt.figure(figsize=(7.5, 5.2), dpi=200)
    ax = fig.add_axes((0.02, 0.06, 0.96, 0.9))
    ax.set_facecolor("#dfe8e6")
    for other in others:
        geom = to_shape(other.geom)
        _draw(ax, geom, facecolor=CREAM, edgecolor=PETROL, linewidth=0.4, alpha=1)
    _draw(ax, target, facecolor=TERRACOTTA, edgecolor=PETROL, linewidth=1.2, alpha=0.35)
    if points:
        ax.scatter([p[0] for p in points], [p[1] for p in points], s=4, color=PETROL, zorder=3)
    minx, miny, maxx, maxy = target.bounds
    pad = max(maxx - minx, maxy - miny) * 0.6 + 0.01
    ax.set_xlim(minx - pad, maxx + pad)
    ax.set_ylim(miny - pad, maxy + pad)
    ax.set_aspect(aspect)
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_color(SLATE)

    kingdom_inset(fig, target.centroid.x, target.centroid.y)

    note = {
        "fr": "Limites : OpenStreetMap (ODbL), à vérifier · Équipements : OpenStreetMap · Carte MAJAL",
        "ar": "Limits: OpenStreetMap (ODbL) · MAJAL",
    }[lang if lang in ("fr", "ar") else "fr"]
    fig.text(0.02, 0.015, note, fontsize=6.5, color=SLATE)
    buffer = io.BytesIO()
    fig.savefig(buffer, format="png", facecolor="white")
    plt.close(fig)
    return buffer.getvalue()
