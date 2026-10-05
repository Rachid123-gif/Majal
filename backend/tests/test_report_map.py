"""Territorial integrity on the report maps (non-negotiable, see CLAUDE.md).

The inset of every report map shows the Kingdom of Morocco in its entirety, southern
provinces included, from the reference contour, and no other boundary.
"""

import json

import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as PatchPolygon
from shapely.geometry import Point, shape
from shapely.ops import unary_union

from app.services.reports.maps import kingdom_contour, kingdom_inset
from app.settings import REPO_ROOT

REFERENCE = REPO_ROOT / "data" / "reference" / "maroc-natural-earth-pov.geojson"


def test_report_maps_use_the_reference_contour() -> None:
    reference = shape(json.loads(REFERENCE.read_text(encoding="utf-8"))["geometry"])
    assert kingdom_contour().equals(reference)


def test_inset_draws_the_whole_kingdom_and_nothing_else() -> None:
    fig = plt.figure()
    inset = kingdom_inset(fig, -6.85, 34.0)  # Rabat
    patches = [p for p in inset.patches if isinstance(p, PatchPolygon)]
    drawn = unary_union(
        [
            shape({"type": "Polygon", "coordinates": [p.get_xy().tolist()]}).buffer(0)
            for p in patches
        ]
    )
    plt.close(fig)
    kingdom = kingdom_contour()
    # Exactly the reference: same surface, nothing added (no other country or region).
    assert abs(drawn.area - kingdom.area) / kingdom.area < 1e-6
    assert drawn.symmetric_difference(kingdom).area / kingdom.area < 1e-6
    # A single filled shape covers the southern provinces: no line splits the Kingdom.
    for lon, lat, name in [
        (-13.2, 27.15, "Laâyoune"),
        (-14.5, 24.0, "Oued Ed-Dahab"),
        (-14.32, 22.55, "Aousserd"),
    ]:
        assert drawn.contains(Point(lon, lat)), name
    assert drawn.bounds[1] < 21.5  # southern edge near Lagouira
