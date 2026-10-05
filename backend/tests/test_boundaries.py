from app.config_loader.territory import LevelKind, load_territory
from app.ingestion.boundaries import BoundaryParams, assemble_units, match_top_units
from app.ingestion.common import normalize
from app.settings import REPO_ROOT
from tests.osm_fixtures import GEOMETRY, TOP

CONFIG = load_territory(REPO_ROOT / "config" / "territories" / "rabat.yaml")
PARAMS = BoundaryParams(
    admin_levels={LevelKind.prefecture: 5, LevelKind.commune: 8, LevelKind.arrondissement: 10}
)


def test_normalize_ignores_accents_case_and_dashes() -> None:
    assert normalize("Skhirate-Témara") == normalize("skhirate temara")


def test_prefectures_are_matched_by_name_without_prefix() -> None:
    matches = match_top_units(TOP, {"rabat", "sale"})
    assert matches == {"rabat": 1, "sale": 2}


def test_units_are_assembled_with_hierarchy_scopes_and_analysis_flags() -> None:
    matches = {"rabat": 1, "sale": 2, "skhirate temara": 1}  # third scope member reuses Rabat
    units, warnings = assemble_units(GEOMETRY, matches, CONFIG, PARAMS, LevelKind.prefecture)
    by_name = {u.name_fr: u for u in units}

    assert "Voisine" not in by_name  # neighbour touching the border is dropped
    # Level words added by OSM are removed, in French and in Arabic.
    assert by_name["Hassan"].name_ar == "حسان"
    # Rabat is split into arrondissements: they are the analysis units, not the commune.
    assert not by_name["Rabat"].is_analysis_unit
    assert by_name["Hassan"].is_analysis_unit and by_name["Souissi"].is_analysis_unit
    assert by_name["Ameur"].is_analysis_unit
    assert by_name["Hassan"].parent is by_name["Rabat"]
    assert by_name["Rabat"].parent is by_name["Préfecture de Rabat"]
    # Scopes come from the territory file: Rabat belongs to both, Salé to the agglomeration.
    assert set(by_name["Hassan"].scopes) == {"agglomeration", "prefecture"}
    assert by_name["Ameur"].scopes == ("agglomeration",)
    assert any("Shoul" in w for w in warnings)  # missing Arabic name is reported
