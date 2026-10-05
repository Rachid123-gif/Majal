"""Territorial integrity of the Kingdom of Morocco (non-negotiable, see CLAUDE.md).

The display rules live in frontend/src/content/cartography-rules.json. These tests check
them, then decode the real base-map tiles (when present) and verify that no boundary left
visible by the rules crosses the interior of the Kingdom, southern provinces included.
"""

import json
import math
import re
from pathlib import Path
from typing import Any

import pytest
from shapely.geometry import LineString, MultiLineString, shape
from shapely.geometry.base import BaseGeometry

from app.settings import REPO_ROOT, get_settings

RULES_PATH = REPO_ROOT / "frontend" / "src" / "content" / "cartography-rules.json"
REFERENCE = REPO_ROOT / "data" / "reference" / "maroc-natural-earth-pov.geojson"
SUSPICIOUS = re.compile(
    r"(?i)(occidental|western|الغربية|sahraou|sahrawi|saharawi|\bRASD\b|\bSADR\b)"
)

pytestmark = pytest.mark.skipif(
    not RULES_PATH.exists(), reason="règles de cartographie absentes (conteneur backend seul)"
)


def rules() -> dict[str, Any]:
    return json.loads(RULES_PATH.read_text(encoding="utf-8"))  # type: ignore[no-any-return]


def boundary_visible(props: dict[str, Any], r: dict[str, Any]) -> bool:
    """Same semantics as BOUNDARY_FILTER in frontend/src/lib/basemapStyle.ts."""
    b = r["boundaries"]
    if float(props.get("kind_detail", 99)) > b["max_kind_detail"]:
        return False
    if b["hide_disputed"] and bool(props.get("disputed")):
        return False
    return props.get("kind") not in b["hide_kinds"]


def label_visible(props: dict[str, Any], r: dict[str, Any]) -> bool:
    """Same semantics as LABEL_FILTER in frontend/src/lib/basemapStyle.ts."""
    lab = r["labels"]
    values = [str(props.get(field, "")) for field in lab["fields"]]
    return not any(needle in value for needle in lab["hide_if_contains"] for value in values)


def test_rules_protect_the_integrity_of_the_kingdom() -> None:
    r = rules()
    assert r["boundaries"]["hide_disputed"] is True
    assert r["boundaries"]["max_kind_detail"] <= 2
    assert {"unrecognized_country", "region", "macroregion"} <= set(r["boundaries"]["hide_kinds"])
    needles = r["labels"]["hide_if_contains"]
    for name in ("Sahara occidental", "Western Sahara", "الصحراء الغربية"):
        assert name in needles
    assert not boundary_visible({"kind": "country", "kind_detail": 2, "disputed": True}, r)
    assert boundary_visible({"kind": "country", "kind_detail": 2}, r)


def test_reference_contour_includes_the_southern_provinces() -> None:
    feature = json.loads(REFERENCE.read_text(encoding="utf-8"))
    kingdom = shape(feature["geometry"])
    south, north = kingdom.bounds[1], kingdom.bounds[3]
    assert south < 21.5 and north > 35.5  # from Lagouira to Tangier
    assert kingdom.contains(shape({"type": "Point", "coordinates": [-13.2, 27.15]}))  # Laâyoune
    assert kingdom.contains(shape({"type": "Point", "coordinates": [-14.32, 22.55]}))  # Aousserd


def _lonlat(z: int, x: int, y: int, px: float, py: float, extent: int) -> tuple[float, float]:
    n = 2**z
    lon = (x + px / extent) / n * 360 - 180
    lat = math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * (y + py / extent) / n))))
    return lon, lat


def _lines(geometry: dict[str, Any], z: int, x: int, y: int, extent: int) -> BaseGeometry | None:
    coords = geometry["coordinates"]
    parts = [coords] if geometry["type"] == "LineString" else coords
    lines = [
        LineString([_lonlat(z, x, y, px, py, extent) for px, py in part])
        for part in parts
        if len(part) >= 2
    ]
    return MultiLineString(lines) if lines else None


TILE_FILES = sorted((get_settings().data_dir / "tiles").glob("*.pmtiles"))


@pytest.mark.skipif(not TILE_FILES, reason="fond de carte absent (lancez `make data`)")
@pytest.mark.parametrize("path", TILE_FILES, ids=lambda p: Path(p).stem)
def test_no_visible_boundary_or_label_divides_the_kingdom(path: Path) -> None:
    import gzip

    import mapbox_vector_tile
    from pmtiles.reader import MmapSource, Reader, all_tiles

    r = rules()
    kingdom = shape(json.loads(REFERENCE.read_text(encoding="utf-8"))["geometry"])
    interior = kingdom.buffer(-0.15)  # ≈ 15 km inside: tolerance for generalised borders
    hidden_disputed_inside = 0
    with path.open("rb") as handle:
        source = MmapSource(handle)  # type: ignore[no-untyped-call]
        reader = Reader(source)  # type: ignore[no-untyped-call]
        max_zoom = min(8, reader.header()["max_zoom"])  # type: ignore[no-untyped-call]
        for (z, x, y), data in all_tiles(source):  # type: ignore[no-untyped-call]
            if z > max_zoom:
                continue
            if data[:2] == b"\x1f\x8b":
                data = gzip.decompress(data)
            tile = mapbox_vector_tile.decode(data, default_options={"y_coord_down": True})
            boundaries = tile.get("boundaries", {})
            extent = boundaries.get("extent", 4096)
            for feature in boundaries.get("features", []):
                geom = _lines(feature["geometry"], z, x, y, extent)
                if geom is None or not geom.intersects(interior):
                    continue
                if boundary_visible(feature["properties"], r):
                    pytest.fail(
                        f"Limite visible à l'intérieur du Royaume (tuile {z}/{x}/{y}) : "
                        f"{feature['properties']}"
                    )
                if feature["properties"].get("disputed"):
                    hidden_disputed_inside += 1
            for feature in tile.get("places", {}).get("features", []):
                props = feature["properties"]
                names = " ".join(str(v) for k, v in props.items() if k.startswith("name"))
                if SUSPICIOUS.search(names) and label_visible(props, r):
                    pytest.fail(
                        f"Étiquette non conforme visible (tuile {z}/{x}/{y}) : {names[:120]}"
                    )
    if path.stem == "maroc":
        # The national tiles do contain the disputed line: the test is meaningful.
        assert hidden_disputed_inside > 0


def test_application_map_draws_the_full_kingdom_contour() -> None:
    """The map's own outer border is the reference contour (southern provinces included)."""
    app = REPO_ROOT / "frontend" / "src" / "content" / "maroc-contour.json"
    assert app.read_text(encoding="utf-8") == REFERENCE.read_text(encoding="utf-8")
