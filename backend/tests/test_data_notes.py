"""Stage 5.4: data request notes (fixed template, no AI), one per institution."""

from typing import Any

import pytest

from app.config_loader.data_holders import load_data_holders, load_module_rules
from app.config_loader.indicators import load_grid
from app.config_loader.taxonomy import load_taxonomy
from app.services.data_needs.completeness import compute
from app.services.data_needs.notes import (
    NBSP,
    build_note,
    load_note_template,
    note_text,
    to_docx,
)
from app.settings import REPO_ROOT
from tests.test_data_needs import diagnostic

CONFIG = REPO_ROOT / "config"
HOLDERS = load_data_holders(CONFIG / "data_holders" / "rabat.yaml")
TEMPLATE = load_note_template(CONFIG / "report_templates" / "note_demande.yaml")
DATA: dict[str, Any] = compute(
    diagnostic(),
    load_grid(CONFIG / "indicators" / "grille-v0.yaml"),
    HOLDERS,
    load_module_rules(CONFIG / "data_holders" / "regles.yaml"),
    load_taxonomy(CONFIG / "taxonomy" / "urbain.yaml"),
)
CODES = [i.code for i in HOLDERS.institutions]


@pytest.mark.parametrize("code", CODES)
def test_every_institution_gets_a_clean_note(code: str) -> None:
    note = build_note(DATA, code, HOLDERS, TEMPLATE)
    text = note_text(note)
    for forbidden in TEMPLATE.forbidden:  # no partnership supposed, no citizen contribution
        assert forbidden.casefold() not in text.casefold(), forbidden
    for field in ("[Nom et titre du professeur]", "[Destinataire]", "[Date]"):
        assert field in text
    assert note["header"] == "MAJAL — projet de recherche appliquée"
    assert "uniquement avec son autorisation" in note["header_placeholder"]
    assert note["footer"] == "Projet de note généré par MAJAL — à relire et adapter avant envoi"
    assert note["rows"], "the annex lists at least one request"
    assert to_docx(note)[:2] == b"PK"


def test_the_letter_follows_the_administrative_forms() -> None:
    note = build_note(DATA, "sante_dr_rsk", HOLDERS, TEMPLATE)
    assert note["subject"].startswith(f"Objet{NBSP}:")
    assert note["salutation"] == "Monsieur / Madame [titre du destinataire],"
    assert note["closing"] == "Veuillez agréer, [titre], l'expression de ma haute considération."
    body = " ".join(note["paragraphs"])
    assert "gratuitement les résultats produits avec ses données" in body
    assert "convention d'échange de données" in body
    assert "loi n° 09-08" in body
    assert (
        "calculer 3 indicateurs aujourd'hui non disponibles et de fiabiliser 1 indicateur" in body
    )


def test_the_annex_uses_the_three_verbs_and_the_ranking() -> None:
    hcp = build_note(DATA, "hcp_dr_rsk", HOLDERS, TEMPLATE)
    effects = " ".join(line for row in hcp["rows"] for line in row["effect"])
    assert f"Calculer{NBSP}:" in effects
    assert f"Affiner (à l'échelle du quartier){NBSP}:" in effects
    assert [row["priority"] for row in hcp["rows"]] == ["Essentielle", "Utile"]


def test_pdf_has_one_page_of_letter_and_one_of_annex() -> None:
    pytest.importorskip("weasyprint")
    from app.services.data_needs.notes import pdf_pages

    try:
        for code in CODES:
            assert pdf_pages(build_note(DATA, code, HOLDERS, TEMPLATE)) == 2, code
    except OSError:  # pragma: no cover - system libraries of WeasyPrint missing outside Docker
        pytest.skip("WeasyPrint needs Pango (available in the Docker image)")
