"""Validation queue: the tool proposes, the urban planner validates (stage 4)."""

from typing import Any, cast

from app.config_loader.taxonomy import load_taxonomy
from app.models import Contribution
from app.services.citizens import evaluate, review, stats
from app.services.citizens.fallback import ReviewRules
from app.services.citizens.report import validation_sentence
from app.settings import REPO_ROOT

TAXONOMY = load_taxonomy(REPO_ROOT / "config" / "taxonomy" / "urbain.yaml")
RULES = ReviewRules()


def make(
    themes: list[str],
    kw_themes: list[str],
    language: str = "ar",
    kw_language: str = "ar",
    model_language: str | None = None,
) -> Contribution:
    c = Contribution(
        external_id="RBT-900",
        original_text="texte",
        anonymized_text="texte",
        language=language,
        themes=themes,
        tonality="plainte",
        territory_id=27,
        place_id=None,
        place_text="Layayda",
        badge="fictitious",
        analysis={
            "mode": "ai",
            "model_language": model_language,
            "keywords": {"themes": kw_themes, "language": kw_language, "tonality": "plainte"},
        },
    )
    return c


def test_disagreement_on_the_main_theme_is_to_check() -> None:
    assert review.reasons(make(["securite"], ["eau_assainissement"]), RULES) == ["theme"]
    assert review.reasons(make(["securite"], ["securite", "eau_assainissement"]), RULES) == []


def test_keywords_finding_nothing_is_not_in_the_queue_but_medium_confidence() -> None:
    c = make(["voirie"], ["autres"])
    assert review.reasons(c, RULES) == []  # owner's choice (2026-10-07)
    assert stats.verbatim(c, {})["confidence"] == "medium"
    assert review.reasons(c, ReviewRules(keywords_silent_is_disagreement=True)) == [
        "theme_unconfirmed"
    ]


def test_uncertain_language_is_to_check() -> None:
    assert "language" in review.reasons(make(["voirie"], ["voirie"], "amazigh_latin"), RULES)
    c = make(["voirie"], ["voirie"], "darija_ar", "ar", model_language="darija_ar")
    assert review.reasons(c, RULES) == ["language"]


def test_a_human_correction_replaces_the_proposal_everywhere_and_is_signed() -> None:
    c = make(["securite"], ["eau_assainissement"])
    assert review.pending(c, RULES)
    review.validate(c, ["eau_assainissement"], "plainte", 22, "professeur")
    assert not review.pending(c, RULES)
    assert c.themes == ["eau_assainissement"] and c.territory_id == 22 and c.place_id is None
    assert c.ai_proposal is not None and c.ai_proposal["themes"] == ["securite"]
    # Statistics and crossing read the corrected fields.
    rows = cast("list[Contribution]", [c])
    summary = stats.summary(rows, TAXONOMY, {})
    assert summary["themes"][0]["code"] == "eau_assainissement" and summary["validated"] == 1
    verbatim = stats.verbatim(c, {})
    assert verbatim["validation_note"]["fr"] == "Validé par professeur"
    assert verbatim["sure"] == {"language": True, "theme": True}


def test_the_model_is_still_scored_on_its_own_proposal() -> None:
    c = make(["securite"], ["eau_assainissement"])
    review.validate(c, ["eau_assainissement"], "plainte", 27, "professeur")
    truth: dict[str, dict[str, Any]] = {"RBT-900": {"themes": ["eau_assainissement"]}}
    result = evaluate.score([c], truth)
    assert result["themes"]["model"]["tp"] == 0  # the model said « sécurité »


def test_human_corrections_form_a_separate_evaluation_set() -> None:
    wrong = make(["securite"], ["eau_assainissement"])
    review.validate(wrong, ["eau_assainissement"], "plainte", 27, "professeur")
    confirmed = make(["voirie"], ["autres"])
    review.validate(confirmed, ["voirie"], "plainte", 27, "admin")
    result = review.human_evaluation([wrong, confirmed, make(["voirie"], ["voirie"])])
    assert result is not None
    assert result["n"] == 2 and result["accounts"] == ["admin", "professeur"]
    assert result["main_theme"] == {"accuracy": 0.5, "n": 2, "correct": 1}
    assert "non représentatif" in result["base"]["fr"]
    assert review.human_evaluation([make(["voirie"], ["voirie"])]) is None


def test_section_7_states_who_validated() -> None:
    sentence = validation_sentence({"count": 2, "by": ["professeur"]}, "fr")
    assert sentence == (
        "Classement vérifié par une personne pour 2 contributions (validé par professeur)."
    )
