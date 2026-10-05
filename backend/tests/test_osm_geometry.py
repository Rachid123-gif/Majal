from shapely.geometry import LineString, MultiPolygon, Point

from app.ingestion.osm_geometry import element_geometry, relation_polygon
from tests.osm_fixtures import square


def test_relation_with_inner_ring_has_a_hole() -> None:
    element = {
        "type": "relation",
        "id": 1,
        "members": [
            {"type": "way", "role": "outer", "geometry": square(0, 0, 4, 4)},
            {"type": "way", "role": "inner", "geometry": square(1, 1, 2, 2)},
        ],
    }
    shape = relation_polygon(element)
    assert isinstance(shape, MultiPolygon)
    assert shape.area == 15  # 16 minus the 1x1 enclave (like Touarga inside Rabat)


def test_outer_ring_split_over_several_ways_is_reassembled() -> None:
    ring = square(0, 0, 2, 2)
    element = {
        "type": "relation",
        "id": 2,
        "members": [
            {"type": "way", "role": "outer", "geometry": ring[:3]},
            {"type": "way", "role": "outer", "geometry": ring[2:]},
        ],
    }
    shape = relation_polygon(element)
    assert shape is not None and shape.area == 4


def test_element_types() -> None:
    assert isinstance(element_geometry({"type": "node", "lon": 1, "lat": 2}), Point)
    closed = element_geometry({"type": "way", "geometry": square(0, 0, 1, 1)})
    assert isinstance(closed, MultiPolygon)
    open_way = element_geometry({"type": "way", "geometry": square(0, 0, 1, 1)[:3]})
    assert isinstance(open_way, LineString)
