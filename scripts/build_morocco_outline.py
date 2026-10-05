"""Build the Morocco outline used by the public landing page (offline SVG).

Source: Natural Earth 1:10m admin 0 countries, Morocco point of view
(ne_10m_admin_0_countries_mar), public domain — https://www.naturalearthdata.com/
Usage (from the repo root, after downloading and unzipping the shapefile):
    uv run --with shapely --with pyshp python scripts/build_morocco_outline.py <path/to/ne_10m_admin_0_countries_mar.shp>
"""

import json
import math
import sys
from pathlib import Path

import shapefile  # pyshp
from shapely.geometry import MultiPolygon, Polygon, box, shape
from shapely.ops import unary_union

OUTPUT = Path(__file__).resolve().parents[1] / "frontend/src/content/morocco-outline.json"
LAT0 = math.radians(28.0)  # equirectangular projection centred on Morocco
SCALE = 40.0
PAD = 12.0
# City locations (WGS84), used only to place the two demo territories on the map.
CITIES = {"rabat": (-6.8416, 34.0209), "tetouan": (-5.3684, 35.5785)}


def main(shp_path: str) -> None:
    reader = shapefile.Reader(shp_path)
    fields = [f[0] for f in reader.fields[1:]]
    shapes = []
    neighbours = []
    frame = box(-19.0, 19.0, 2.0, 39.0)  # Morocco plus surroundings, for close-up views
    for record, geom in zip(reader.records(), reader.shapes(), strict=True):
        row = dict(zip(fields, record, strict=True))
        geometry = shape(geom.__geo_interface__)
        if row.get("ADM0_A3") == "MAR":
            shapes.append(geometry)
        elif geometry.intersects(frame):
            neighbours.append(geometry.intersection(frame))
    if not shapes:
        raise SystemExit("Morocco (ADM0_A3=MAR) not found in the shapefile")
    country = unary_union(shapes).simplify(0.02, preserve_topology=True)
    polygons = list(country.geoms) if isinstance(country, MultiPolygon) else [country]
    polygons = [p for p in polygons if isinstance(p, Polygon) and p.area > 0.01]

    minx, miny, maxx, maxy = unary_union(polygons).bounds

    def project(lon: float, lat: float) -> tuple[float, float]:
        x = (lon - minx) * math.cos(LAT0) * SCALE + PAD
        y = (maxy - lat) * SCALE + PAD
        return round(x, 1), round(y, 1)

    def to_path(items: list[Polygon]) -> str:
        parts = []
        for polygon in items:
            coords = [project(x, y) for x, y in polygon.exterior.coords]
            parts.append("M" + "L".join(f"{x},{y}" for x, y in coords) + "Z")
        return "".join(parts)

    parts = [to_path(polygons)]
    context = unary_union(neighbours).simplify(0.02, preserve_topology=True)
    context_polygons = list(context.geoms) if isinstance(context, MultiPolygon) else [context]
    context_polygons = [p for p in context_polygons if isinstance(p, Polygon) and p.area > 0.001]
    width, height = project(maxx, miny)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(
        json.dumps(
            {
                "source": "Natural Earth 1:10m, admin 0 (point de vue du Maroc), domaine public",
                "viewBox": [0, 0, round(width + PAD, 1), round(height + PAD, 1)],
                "path": parts[0],
                "context": to_path(context_polygons),
                "cities": {code: project(*lonlat) for code, lonlat in CITIES.items()},
            },
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"✓ {OUTPUT} ({len(polygons)} + {len(context_polygons)} context polygon(s))")


if __name__ == "__main__":
    main(sys.argv[1])
