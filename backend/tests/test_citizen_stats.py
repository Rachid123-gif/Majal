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


def test_commune_scale_groups_units_and_judges_indicators_by_population() -> None:
    contributions = rows([C("A", ["espaces_verts"], unit=27), C("B", ["espaces_verts"], unit=22)])
    groups = {26: {"name_fr": "Salé", "name_ar": "سلا", "population": 300, "members": [27, 22]}}
    summary = stats.summary(contributions, TAXONOMY, groups, group_of={27: 26, 22: 26})
    assert summary["units"][0]["count"] == 2 and summary["units"][0]["members"] == [27, 22]
    members = [
        {
            "name_fr": "Layayda",
            "population": 200,
            "values": {"ENV_VERT": {"value": 0.2, "status": "deficit_marked"}},
        },
        {
            "name_fr": "Tabriquet",
            "population": 100,
            "values": {"ENV_VERT": {"value": 3.0, "status": "ok"}},
        },
    ]
    result = stats.crossing(
        contributions, TAXONOMY, {}, {"ENV_VERT": {"label": {"fr": "x"}}}, {}, members=members
    )
    row = next(r for r in result["rows"] if r["theme"] == "espaces_verts")
    aggregate = row["indicators"][0]["aggregate"]
    assert aggregate["population_share"] == round(200 / 300, 4)  # 67 % ≥ 50 %: unfavourable
    assert row["indicators"][0]["value"] is None  # no aggregated value is invented
    assert row["indicators"][0]["unfavourable"] is True


def test_moderate_demand_with_a_deficit_is_not_called_absence_of_demand() -> None:
    items = rows(
        [C(str(i), ["espaces_verts"]) for i in range(5)]
        + [C(f"x{i}", ["voirie"]) for i in range(30)]
    )
    deficit = {"ENV_VERT": {"value": 0.2, "status": "deficit_marked"}}
    result = stats.crossing(items, TAXONOMY, deficit, {"ENV_VERT": {"label": {"fr": "x"}}}, {})
    row = next(r for r in result["rows"] if r["theme"] == "espaces_verts")
    assert row["verdict"] == "moderate_deficit"  # 5 of 35: some demand, not « strong »


def test_unknown_indicators_are_not_reported_as_favourable_at_commune_scale() -> None:
    members = [
        {
            "name_fr": "A",
            "population": 10,
            "values": {"SAN_ESSP": {"value": None, "status": "not_available"}},
        },
        {
            "name_fr": "B",
            "population": 10,
            "values": {"SAN_ESSP": {"value": None, "status": "not_available"}},
        },
    ]
    result = stats.crossing(
        rows([C("A", ["sante"], unit=1)] * 5), TAXONOMY, {}, {}, {}, members=members
    )
    indicator = next(r for r in result["rows"] if r["theme"] == "sante")["indicators"][0]
    assert indicator["aggregate"]["units"] == 0 and indicator["aggregate"]["missing_units"] == 2
    assert indicator["aggregate"]["population_share"] is None and not indicator["unfavourable"]


def test_labels_repeat_the_real_status_of_the_indicator() -> None:
    items = rows(
        [C(str(i), ["espaces_verts"]) for i in range(5)]
        + [C(f"x{i}", ["voirie"]) for i in range(30)]
    )
    meta = {"ENV_VERT": {"label": {"fr": "x"}}}
    marked = {"ENV_VERT": {"value": 0.2, "status": "deficit_marked"}}
    watch = {"ENV_VERT": {"value": 2.0, "status": "watch"}}
    row = next(
        r
        for r in stats.crossing(items, TAXONOMY, marked, meta, {})["rows"]
        if r["theme"] == "espaces_verts"
    )
    assert row["verdict_label"]["fr"] == "Demande modérée et déficit marqué"
    row = next(
        r
        for r in stats.crossing(items, TAXONOMY, watch, meta, {})["rows"]
        if r["theme"] == "espaces_verts"
    )
    assert row["verdict_label"]["fr"] == "Demande modérée et indicateur à surveiller"


def test_absence_of_demand_needs_thirty_contributions_in_the_unit() -> None:
    watch = {"EMP_CHOM": {"value": 20.8, "status": "watch"}}
    meta = {"EMP_CHOM": {"label": {"fr": "Chômage"}}}

    def emploi(total: int) -> dict[str, Any]:
        items = rows([C(f"x{i}", ["voirie"]) for i in range(total)])
        result = stats.crossing(items, TAXONOMY, watch, meta, {})
        return next(r for r in result["rows"] if r["theme"] == "emploi_jeunesse")

    few = emploi(25)  # Layayda: 25 contributions
    assert few["verdict"] == "absence_unknown"
    assert few["verdict_label"]["fr"] == (
        "Trop peu de contributions pour juger de l'absence de demande"
    )
    enough = emploi(30)
    assert enough["verdict"] == "data_only"
    assert enough["verdict_label"]["fr"] == "Indicateur à surveiller, sans demande exprimée"


def test_commune_is_in_marked_deficit_only_if_those_units_reach_the_share() -> None:
    members = [
        {"name_fr": "A", "population": 60, "values": {"ENV_VERT": {"value": 1, "status": "watch"}}},
        {
            "name_fr": "B",
            "population": 40,
            "values": {"ENV_VERT": {"value": 1, "status": "deficit_marked"}},
        },
    ]
    items = rows([C(str(i), ["espaces_verts"], unit=1) for i in range(5)])
    result = stats.crossing(items, TAXONOMY, {}, {"ENV_VERT": {}}, {}, members=members)
    row = next(r for r in result["rows"] if r["theme"] == "espaces_verts")
    assert row["indicators"][0]["severity"] == "watch"  # 40 % in marked deficit < 50 %
    assert "à surveiller" in row["verdict_label"]["fr"]
