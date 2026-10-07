"""Presentation mode: the scenario file (config/presentation/<territory>.yaml)."""

from app.api.presentation import load_scenario
from app.settings import REPO_ROOT

SCENARIO = load_scenario(REPO_ROOT / "config" / "presentation" / "rabat.yaml")


def test_rabat_scenario_has_the_nine_validated_steps() -> None:
    assert SCENARIO.steps == [
        "home",
        "stakes",
        "map",
        "sheet",
        "compare",
        "citizens",
        "report",
        "data_needs",
        "proposal",
    ]


def test_units_and_closing_slide_of_the_scenario() -> None:
    assert SCENARIO.sheet.unit == SCENARIO.report.unit == "Layayda"
    assert SCENARIO.compare.units == ["Layayda", "Agdal-Riyad", "Oumazza"]
    assert (SCENARIO.citizens.scale, SCENARIO.citizens.unit) == ("commune", "Salé")
    assert [i.fr for i in SCENARIO.proposal.items] == [
        "Un pilote sur votre territoire",
        "Une convention d'échange de données, encadrée et confidentielle",
        "La restitution gratuite des résultats à votre institution",
    ]
    assert SCENARIO.proposal.contact == ["[Nom et titre du professeur]", "[email]", "[téléphone]"]
    assert SCENARIO.stakes.sentence.fr.startswith("Chaque territoire doit produire un diagnostic.")
