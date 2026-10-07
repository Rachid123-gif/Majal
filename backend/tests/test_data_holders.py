"""Stage 5.1: the referential of institutions and data requests (config/data_holders/)."""

from pathlib import Path

import pytest

from app.config_loader import ConfigError
from app.config_loader.data_holders import load_data_holders, reference_errors
from app.config_loader.indicators import load_grid
from app.config_loader.taxonomy import load_taxonomy
from app.settings import REPO_ROOT

CONFIG = REPO_ROOT / "config"
HOLDERS = load_data_holders(CONFIG / "data_holders" / "rabat.yaml")
GRID = load_grid(CONFIG / "indicators" / "grille-v0.yaml")
TAXONOMY = load_taxonomy(CONFIG / "taxonomy" / "urbain.yaml")


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
