"""The urban taxonomy (config/taxonomy/urbain.yaml) is valid and its crossing points to real
indicators of the grid."""

from app.config_loader.indicators import load_grid
from app.config_loader.taxonomy import load_taxonomy
from app.settings import REPO_ROOT

CONFIG = REPO_ROOT / "config"


def test_urban_taxonomy_covers_the_brief_and_links_real_indicators() -> None:
    taxonomy = load_taxonomy(CONFIG / "taxonomy" / "urbain.yaml")
    grid = {i.code for i in load_grid(CONFIG / "indicators" / "grille-v0.yaml").indicators}
    assert len(taxonomy.themes) == 19  # BRIEF §9.6, profile « urbain »
    assert set(taxonomy.tonalities) == {"demande", "plainte", "proposition", "satisfaction"}
    for theme in taxonomy.themes:
        assert set(theme.indicators) <= grid, theme.code
        if theme.code != "autres":
            assert theme.keywords.fr and theme.keywords.ar, theme.code


def test_themes_without_indicator_say_which_data_to_ask_for() -> None:
    taxonomy = load_taxonomy(CONFIG / "taxonomy" / "urbain.yaml")
    voirie = taxonomy.theme("voirie")
    assert voirie is not None and voirie.indicators == []  # MOB_ROUTE: profile « mixte » only
    for theme in taxonomy.themes:
        if theme.indicators:
            continue
        if theme.code in ("securite", "autres"):
            assert theme.data_request is None  # no indicator planned
        else:
            assert theme.data_request is not None, theme.code
    assert taxonomy.crossing.min_contributions == 5
    assert taxonomy.crossing.percent_min_total == 20
