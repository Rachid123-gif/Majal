"""Turn Overpass `out geom` elements into Shapely geometries."""

from typing import Any

from shapely.geometry import LineString, MultiPolygon, Point, Polygon
from shapely.geometry.base import BaseGeometry
from shapely.ops import polygonize, unary_union


def _line(points: list[dict[str, float]]) -> LineString | None:
    coords = [(p["lon"], p["lat"]) for p in points if p]
    return LineString(coords) if len(coords) >= 2 else None


def _area_from_lines(lines: list[LineString]) -> BaseGeometry | None:
    if not lines:
        return None
    polygons = list(polygonize(unary_union(lines)))
    return unary_union(polygons) if polygons else None


def relation_polygon(element: dict[str, Any]) -> MultiPolygon | None:
    """Assemble a (multi)polygon from a relation's outer and inner ways."""
    outer: list[LineString] = []
    inner: list[LineString] = []
    for member in element.get("members", []):
        if member.get("type") != "way" or "geometry" not in member:
            continue
        line = _line(member["geometry"])
        if line is None:
            continue
        (inner if member.get("role") == "inner" else outer).append(line)
    shape = _area_from_lines(outer)
    if shape is None:
        return None
    holes = _area_from_lines(inner)
    if holes is not None:
        shape = shape.difference(holes)
    return as_multipolygon(shape)


def as_multipolygon(shape: BaseGeometry) -> MultiPolygon | None:
    if shape.is_empty:
        return None
    if not shape.is_valid:
        shape = shape.buffer(0)
    if isinstance(shape, Polygon):
        return MultiPolygon([shape])
    if isinstance(shape, MultiPolygon):
        return shape
    polygons = [g for g in getattr(shape, "geoms", []) if isinstance(g, Polygon)]
    return MultiPolygon(polygons) if polygons else None


def element_geometry(element: dict[str, Any]) -> BaseGeometry | None:
    """Point for nodes, polygon for closed ways and multipolygons, line otherwise."""
    kind = element.get("type")
    if kind == "node":
        return Point(element["lon"], element["lat"])
    if kind == "way" and "geometry" in element:
        line = _line(element["geometry"])
        if line is None:
            return None
        if line.is_closed and len(line.coords) >= 4:
            return as_multipolygon(Polygon(line.coords))
        return line
    if kind == "relation":
        return relation_polygon(element)
    return None


def way_line(element: dict[str, Any]) -> LineString | None:
    return _line(element.get("geometry", []))
