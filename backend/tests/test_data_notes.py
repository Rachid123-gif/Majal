"""Stage 5.4: data request notes (fixed template, no AI), one per institution."""

import re
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
    for forbidden in TEMPLATE.forbidden:  # no partnership, no citizen contribution, no « nous »
        assert not re.search(rf"\b{re.escape(forbidden)}\b", text, re.IGNORECASE), forbidden
    for field in ("[Nom et titre du professeur]", "[Date]"):
        assert field in text
    # A single recipient, with its full title (no group of entities as recipients).
    assert len(note["recipient"]) == 1 and note["recipient"][0].startswith("À Monsieur / Madame")
    assert note["header"] == "MAJAL — projet de recherche appliquée"
    assert "uniquement avec son autorisation" in note["header_placeholder"]
    assert note["footer"] == "Projet de note généré par MAJAL — à relire et adapter avant envoi"
    assert note["rows"], "the annex lists at least one request"
    assert to_docx(note)[:2] == b"PK"


def test_the_letter_follows_the_administrative_forms() -> None:
    note = build_note(DATA, "sante_dr_rsk", HOLDERS, TEMPLATE)
    assert note["subject"].startswith(f"Objet{NBSP}:")
    assert note["recipient"] == [
        "À Monsieur / Madame le / la Directeur / Directrice régional(e) de la Santé et de la "
        "Protection sociale de la Région Rabat-Salé-Kénitra"
    ]
    assert note["salutation"] == ("Monsieur / Madame le / la Directeur / Directrice régional(e),")
    assert note["closing"] == (
        "Veuillez agréer, Monsieur / Madame le / la Directeur / Directrice régional(e), "
        "l'expression de ma haute considération."
    )
    body = " ".join(note["paragraphs"])
    assert "gratuitement les résultats produits avec ses données" in body
    assert "convention d'échange de données" in body
    assert "loi n° 09-08" in body
    assert "je conduis le projet de recherche appliquée MAJAL" in body
    assert "J'ai l'honneur de solliciter" in body and "Je reste à votre disposition" in body
    assert "Je serais honoré de vous présenter l'outil MAJAL lors d'une rencontre" in body
    # Complementary entities are cited in the text, not as recipients.
    assert "délégations préfectorales de la Santé et de la Protection sociale" in body
    assert not re.search(r"\.[A-ZÀ-Ý]", body)  # a space after every full stop
    assert "Hautes Orientations Royales" not in body  # optional paragraph, off by default
    assert (
        "calculer 3 indicateurs aujourd'hui non disponibles et de fiabiliser 1 indicateur" in body
    )


def test_the_optional_royal_paragraph_replaces_the_first_sentence() -> None:
    template = TEMPLATE.model_copy(
        update={"royal_context": TEMPLATE.royal_context.model_copy(update={"enabled": True})}
    )
    first = build_note(DATA, "sante_dr_rsk", HOLDERS, template)["paragraphs"][0]
    assert first.startswith("Ce travail s'inscrit dans le cadre de la nouvelle génération")
    assert "reposent sur des diagnostics" not in first


def test_period_is_distinct_from_frequency() -> None:
    sante = build_note(DATA, "sante_dr_rsk", HOLDERS, TEMPLATE)["rows"][0]
    assert sante["period"] == "Situation la plus récente disponible"
    assert sante["frequency"] == f"Fréquence{NBSP}: annuelle"
    eau = build_note(DATA, "distributeur_eau_electricite", HOLDERS, TEMPLATE)["rows"][0]
    assert eau["period"] == "2020 à 2025"


def test_the_annex_uses_the_three_verbs_and_the_ranking() -> None:
    hcp = build_note(DATA, "hcp_dr_rsk", HOLDERS, TEMPLATE)
    effects = " ".join(line for row in hcp["rows"] for line in row["effect"])
    assert f"Calculer{NBSP}:" in effects
    assert f"Affiner (à l'échelle du quartier){NBSP}:" in effects
    assert [row["priority"] for row in hcp["rows"]] == ["Essentielle", "Utile"]


def test_pdf_has_one_page_of_letter_and_one_of_annex() -> None:
    pytest.importorskip("weasyprint")
    from app.services.data_needs.notes import pdf_pages

    royal = TEMPLATE.model_copy(
        update={"royal_context": TEMPLATE.royal_context.model_copy(update={"enabled": True})}
    )
    try:
        for code in CODES:
            for template in (TEMPLATE, royal):
                assert pdf_pages(build_note(DATA, code, HOLDERS, template)) == 2, code
    except OSError:  # pragma: no cover - system libraries of WeasyPrint missing outside Docker
        pytest.skip("WeasyPrint needs Pango (available in the Docker image)")
