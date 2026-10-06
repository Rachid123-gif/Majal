"""Dashboard rules (stage 4.4): main theme only unless asked, counts below the percentage
threshold, sure verbatims first with the original next to the translation, permanent banner."""

from typing import Any, cast

from app.config_loader.taxonomy import load_taxonomy
from app.models import Contribution
from app.services.citizens import stats
from app.settings import REPO_ROOT

TAXONOMY = load_taxonomy(REPO_ROOT / "config" / "taxonomy" / "urbain.yaml")
UNITS = {4: {"name_fr": "Témara", "name_ar": "تمارة", "population": 297098}}


class C:
    def __init__(
        self,
        ext: str,
        themes: list[str],
        language: str = "fr",
        kw_lang: str = "fr",
        kw_themes: list[str] | None = None,
        unit: int | None = 4,
    ) -> None:
        self.external_id, self.themes, self.language = ext, themes, language
        self.tonality, self.territory_id, self.badge = "plainte", unit, "fictitious"
        self.anonymized_text = f"texte {ext}"
        self.translation_fr = None if language == "fr" else f"traduction {ext}"
        self.place_text = None
        self.analysis: dict[str, Any] = {
            "mode": "ai",
            "keywords": {"language": kw_lang, "themes": kw_themes or themes[:1]},
        }


def rows(items: list[Any]) -> list[Contribution]:
    return cast("list[Contribution]", items)


def test_main_theme_only_unless_secondary_themes_are_asked_for() -> None:
    items = rows([C("A", ["voirie", "proprete"]), C("B", ["voirie"]), C("C", ["mobilite"])])
    main = stats.summary(items, TAXONOMY, UNITS)
    assert {t["code"]: t["count"] for t in main["themes"]} == {"voirie": 2, "mobilite": 1}
    assert main["secondary_note"] is None
    both = stats.summary(items, TAXONOMY, UNITS, secondary=True)
    assert {t["code"]: t["count"] for t in both["themes"]}["proprete"] == 1
    assert "moins fiables" in both["secondary_note"]["fr"]


def test_counts_not_percentages_below_twenty_contributions() -> None:
    few = stats.summary(rows([C(str(i), ["voirie"]) for i in range(19)]), TAXONOMY, UNITS)
    assert few["themes"][0]["share"] is None
    many = stats.summary(rows([C(str(i), ["voirie"]) for i in range(20)]), TAXONOMY, UNITS)
    assert many["themes"][0]["share"] == 1.0
    assert many["units"][0]["main_theme"] == "voirie"  # at least 5 contributions
    four = stats.summary(rows([C(str(i), ["voirie"]) for i in range(4)]), TAXONOMY, UNITS)
    assert four["units"][0]["main_theme"] is None  # too few to conclude


def test_sure_verbatims_first_with_original_and_translation_note() -> None:
    unsure = C("A", ["voirie"], language="darija_ar", kw_lang="ar", kw_themes=["proprete"])
    sure = C("B", ["voirie"], language="darija_ar", kw_lang="darija_ar")
    chosen = stats.verbatims(rows([unsure, sure]), "voirie", UNITS, limit=2)
    assert [v["id"] for v in chosen] == ["B", "A"]
    assert chosen[0]["original"] == "texte B" and chosen[0]["translation_fr"] == "traduction B"
    assert chosen[0]["translation_note"]["fr"] == "Traduction automatique"
    assert chosen[0]["sure"] == {"language": True, "theme": True}


def test_amazigh_verbatims_carry_the_approximation_note() -> None:
    row = C("Z", ["mobilite"], language="amazigh_latin", kw_lang="amazigh_latin")
    verbatim = stats.verbatims(rows([row]), "mobilite", UNITS)[0]
    assert "approximative" in verbatim["language_note"]["fr"]


def test_the_banner_text_is_the_owners() -> None:
    assert stats.FICTITIOUS_BANNER["fr"] == (
        "Contributions fictives — illustration du fonctionnement de l'outil. "
        "Elles ne reflètent pas l'opinion réelle des habitants."
    )
