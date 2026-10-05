"""Synthetic Overpass elements: two prefectures, communes, arrondissements, a neighbour."""

from typing import Any


def square(x0: float, y0: float, x1: float, y1: float) -> list[dict[str, float]]:
    return [
        {"lon": x0, "lat": y0},
        {"lon": x1, "lat": y0},
        {"lon": x1, "lat": y1},
        {"lon": x0, "lat": y1},
        {"lon": x0, "lat": y0},
    ]


def relation(
    osm_id: int, level: int, name: str, ring: list[dict[str, float]], **tags: str
) -> dict[str, Any]:
    return {
        "type": "relation",
        "id": osm_id,
        "tags": {"boundary": "administrative", "admin_level": str(level), "name:fr": name, **tags},
        "members": [{"type": "way", "role": "outer", "geometry": ring}],
    }


TOP = [
    {"type": "relation", "id": 1, "tags": {"admin_level": "5", "name:fr": "Préfecture de Rabat"}},
    {"type": "relation", "id": 2, "tags": {"admin_level": "5", "name:fr": "Préfecture de Salé"}},
    {"type": "relation", "id": 3, "tags": {"admin_level": "5", "name:fr": "Province de Kénitra"}},
]

GEOMETRY = [
    relation(1, 5, "Préfecture de Rabat", square(0, 0, 2, 2), **{"name:ar": "عمالة الرباط"}),
    relation(2, 5, "Préfecture de Salé", square(2, 0, 4, 2), **{"name:ar": "عمالة سلا"}),
    # Rabat commune, split into two arrondissements (one name carries the level word).
    relation(10, 8, "Rabat", square(0, 0, 2, 2), **{"name:ar": "الرباط"}),
    relation(11, 10, "Arrondissement Hassan", square(0, 0, 1, 2), **{"name:ar": "مقاطعة حسان"}),
    relation(12, 10, "Souissi", square(1, 0, 2, 2), **{"name:ar": "مقاطعة السويسي"}),
    # Salé prefecture: two communes without arrondissements, one without an Arabic name.
    relation(20, 8, "Ameur", square(2, 0, 3, 2), **{"name:ar": "عامر"}),
    relation(21, 8, "Shoul", square(3, 0, 4, 2)),
    # A neighbour returned by the area query because it touches the border: must be dropped.
    relation(30, 8, "Voisine", square(4, 0, 5, 2)),
]
