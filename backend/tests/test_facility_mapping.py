from pathlib import Path

import pytest

from app.config_loader import ConfigError
from app.config_loader.facility_mapping import load_facility_mapping
from app.settings import REPO_ROOT

MAPPING = REPO_ROOT / "config" / "mappings" / "osm_facilities.yaml"


def test_real_mapping_is_valid_and_marked_provisional() -> None:
    mapping = load_facility_mapping(MAPPING)
    assert mapping.status == "TODO_REFERENT"
    codes = {c.code for c in mapping.enabled}
    assert {"school", "health_primary", "tram_stop", "green_space"} <= codes
    assert "garden" not in codes  # disabled pending the referent's answer (Q14)


def test_classification_follows_order_and_exclusions() -> None:
    mapping = load_facility_mapping(MAPPING)
    assert mapping.classify({"amenity": "hospital"}).code == "health_hospital"  # type: ignore[union-attr]
    assert mapping.classify({"leisure": "park"}).code == "green_space"  # type: ignore[union-attr]
    assert mapping.classify({"leisure": "park", "access": "private"}) is None
    assert mapping.classify({"amenity": "bench"}) is None


def test_badly_written_rule_is_explained(tmp_path: Path) -> None:
    text = MAPPING.read_text(encoding="utf-8").replace(
        'rules: ["amenity=hospital"]', 'rules: ["amenity hospital"]'
    )
    path = tmp_path / "osm_facilities.yaml"
    path.write_text(text, encoding="utf-8")
    with pytest.raises(ConfigError) as exc_info:
        load_facility_mapping(path)
    [issue] = exc_info.value.issues
    assert "clé=valeur" in issue.problem
    assert issue.example == 'rules: ["amenity=school"]'
