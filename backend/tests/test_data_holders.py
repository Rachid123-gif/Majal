"""Stage 5.1: the referential of institutions and data requests (config/data_holders/)."""

from pathlib import Path

import pytest

from app.config_loader import ConfigError
from app.config_loader.data_holders import load_data_holders, load_module_rules, reference_errors
from app.config_loader.indicators import load_grid
from app.config_loader.taxonomy import load_taxonomy
from app.settings import REPO_ROOT

CONFIG = REPO_ROOT / "config"
HOLDERS = load_data_holders(CONFIG / "data_holders" / "rabat.yaml")
GRID = load_grid(CONFIG / "indicators" / "grille-v0.yaml")
TAXONOMY = load_taxonomy(CONFIG / "taxonomy" / "urbain.yaml")
RULES = load_module_rules(CONFIG / "data_holders" / "regles.yaml")


def test_every_reference_exists_in_the_grid_and_the_taxonomy() -> None:
    codes = {i.code for i in GRID.indicators}
    assert reference_errors(HOLDERS, codes, {t.code for t in TAXONOMY.themes}) == []


def test_every_name_is_marked_to_be_checked_by_the_professor() -> None:
    assert all(i.to_verify for i in HOLDERS.institutions)


def test_the_owners_list_of_institutions_is_there() -> None:
    assert {i.code for i in HOLDERS.institutions} == {
        "wilaya_rsk",
        "commune_rabat",
        "commune_sale",
        "communes_skhirate_temara",
        "conseil_region_rsk",
        "agence_urbaine_rabat_sale",
        "hcp_dr_rsk",
        "sante_dr_rsk",
        "aref_rsk",
        "distributeur_eau_electricite",
        "eci_al_assima",
        "operateur_tramway",
        "agence_bouregreg",
        "culture_dr_rsk",
        "developpement_durable_dr_rsk",
        "interieur_dgct",
        "jeunesse_dr_rsk",
        "entraide_nationale",
    }


def test_every_indicator_not_available_in_rabat_has_a_request() -> None:
    enabled = {code for r in HOLDERS.requests for code in r.enables}
    # Not available in the Rabat diagnostic (stage 2): missing input or OSM census too thin.
    assert {"EDU_ECOLES", "SAN_ESSP", "SAN_PROX", "MOB_15MIN", "URB_DOC"} <= enabled
    requested = {i.code for i in GRID.indicators if getattr(i, "requested_from", None)}
    assert requested <= enabled


def test_every_estimated_or_open_indicator_of_the_urban_profile_can_be_improved() -> None:
    covered = {c for r in HOLDERS.requests for c in r.enables + r.improves}
    for indicator in GRID.indicators:
        if "urbain" not in indicator.profiles:
            continue
        source = indicator.source_expected or ""
        if "estimé" in source or "ouvert" in source:
            assert indicator.code in covered, indicator.code


def test_every_citizen_theme_marked_data_to_ask_for_has_a_request() -> None:
    asked = {t for r in HOLDERS.requests for t in r.themes}
    for theme in TAXONOMY.themes:
        if theme.data_request is not None:
            assert theme.code in asked, theme.code


def test_requests_never_mention_citizen_contributions() -> None:
    for request in HOLDERS.requests:
        text = f"{request.data.fr} {request.value.fr} {request.detail.fr}".casefold()
        assert "contribution" not in text and "citoyen" not in text, request.code


def test_an_unknown_institution_is_explained_in_french(tmp_path: Path) -> None:
    source = (CONFIG / "data_holders" / "rabat.yaml").read_text(encoding="utf-8")
    broken = tmp_path / "rabat.yaml"
    broken.write_text(
        source.replace("holders: [interieur_dgct]", "holders: [ministere_inconnu]"),
        encoding="utf-8",
    )
    with pytest.raises(ConfigError) as error:
        load_data_holders(broken)
    assert "ministere_inconnu" in error.value.format()
    assert "absente de la liste" in error.value.format()


def test_priority_is_computed_from_what_the_data_changes() -> None:
    from app.services.data_needs.priority import priority

    by_code = {r.code: priority(r, RULES) for r in HOLDERS.requests}
    assert by_code["etablissements_sante"] == "essential"  # enables 3 indicators
    assert by_code["limites_officielles"] == "essential"  # official boundaries
    assert by_code["reseau_bus"] == "useful"  # improves an estimated indicator
    assert by_code["proprete"] == "useful"  # citizen theme without indicator
    assert by_code["projets_programmes_pti"] == "context"
    assert by_code["projets_bouregreg"] == "context"  # programmed projects, even if it improves


def test_requests_are_ranked_by_priority_first() -> None:
    from app.services.data_needs.priority import priority, ranked

    order = [list(RULES.priorities).index(priority(r, RULES)) for r in ranked(HOLDERS, RULES)]
    assert order == sorted(order)
    # Then by total indicators concerned: the official boundaries (10) come first.
    assert [r.code for r in ranked(HOLDERS, RULES)[:2]] == [
        "limites_officielles",
        "etablissements_sante",
    ]


def test_priority_rules_are_read_from_the_configuration(tmp_path: Path) -> None:
    from app.services.data_needs.priority import priority

    source = (CONFIG / "data_holders" / "regles.yaml").read_text(encoding="utf-8")
    # Without the « context first » rule, Bouregreg (which improves green spaces) is useful.
    edited = tmp_path / "regles.yaml"
    edited.write_text(
        source.replace("  - priority: context\n    when_any: [context]\n", ""), encoding="utf-8"
    )
    rules = load_module_rules(edited)
    assert len(rules.priority_rules) == 2
    bouregreg = next(r for r in HOLDERS.requests if r.code == "projets_bouregreg")
    assert priority(bouregreg, rules) == "useful"


def test_the_two_added_institutions_receive_their_own_request() -> None:
    holders = {h for r in HOLDERS.requests for h in r.holders}
    assert {"jeunesse_dr_rsk", "entraide_nationale"} <= holders
    sport = next(r for r in HOLDERS.requests if r.code == "equipements_sport_culture")
    assert sport.complementary == ["jeunesse_dr_rsk", "entraide_nationale"]
