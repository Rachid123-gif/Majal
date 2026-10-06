"""Report writing: retries, fallback without AI, rendering, sovereign mode."""

from typing import Any

import pytest

from app.services.llm import SovereignModeError, get_provider
from app.services.llm.base import LLMError, LLMResult
from app.services.reports.facts import FactSheet, build_fact_sheet, format_number
from app.services.reports.template import load_template
from app.services.reports.writer import check_paragraphs, render, write_section
from app.settings import REPO_ROOT, Settings

TEMPLATE = load_template(REPO_ROOT / "config" / "report_templates" / "diagnostic_commune.yaml")
SECTION = next(s for s in TEMPLATE.sections if s.code == "vulnerabilites")

DIAGNOSTIC: dict[str, Any] = {
    "evaluation": {
        "reference_label": {"fr": "de l'agglomération", "ar": "التجمع"},
        "label": {"fr": "Évaluation relative", "ar": "تقييم نسبي"},
        "statuses": {
            s: {"fr": s, "ar": s}
            for s in (
                "deficit_marked",
                "watch",
                "ok",
                "context",
                "not_evaluable",
                "not_available",
                "not_applicable",
            )
        },
    },
    "grid": {"label": {"fr": "Grille v0", "ar": "الشبكة v0"}},
    "indicators": [
        {
            "code": "EMP_CHOM",
            "axis": "emploi",
            "label": {"fr": "Taux de chômage", "ar": "معدل البطالة"},
            "unit": {"fr": "%", "ar": "%"},
            "direction": "lower_better",
            "decimals": 1,
            "reference": {"type": "relative", "value": 18.9},
            "source_expected": "HCP",
            "formula": "raw",
            "requested_from": None,
        },
        {
            "code": "EMP_ANALPH",
            "axis": "emploi",
            "label": {"fr": "Taux d'analphabétisme", "ar": "معدل الأمية"},
            "unit": {"fr": "%", "ar": "%"},
            "direction": "lower_better",
            "decimals": 1,
            "reference": None,
            "source_expected": "HCP",
            "formula": "raw",
            "requested_from": "HCP",
        },
    ],
    "units": [
        {
            "id": 7,
            "name_fr": "Hassan",
            "name_ar": "حسان",
            "level": "arrondissement",
            "official_code": "44210105",
            "area_km2": 8.2,
            "values": {
                "EMP_CHOM": {
                    "value": 20.6,
                    "status": "watch",
                    "rank": 17,
                    "rank_of": 23,
                    "year": 2024,
                    "badge": "official",
                    "sources": ["HCP"],
                    "ratio": 1.09,
                    "gap_pct": 9.0,
                },
                "EMP_ANALPH": {
                    "value": None,
                    "status": "not_available",
                    "rank": None,
                    "reason": "x",
                },
            },
        }
    ],
}
IDENTITY = {
    "name_fr": "Hassan",
    "name_ar": "حسان",
    "description_fr": "arrondissement",
    "description_ar": "مقاطعة",
}


def sheet() -> FactSheet:
    return build_fact_sheet(DIAGNOSTIC, 7, dict(IDENTITY))


class FakeProvider:
    name, model, local = "fake", "fake", True

    def __init__(self, answers: list[Any]) -> None:
        self.answers = answers
        self.prompts: list[str] = []

    def generate_json(
        self, system: str, prompt: str, schema: dict[str, Any], temperature: float = 0.2
    ) -> LLMResult:
        self.prompts.append(prompt)
        answer = self.answers.pop(0)
        if isinstance(answer, Exception):
            raise answer
        return LLMResult(answer, str(answer), 0.01, 10)


def test_french_number_format() -> None:
    assert format_number(168391, 0) == "168 391"
    assert format_number(20.64, 1) == "20,6"


def test_model_text_is_rendered_with_the_facts() -> None:
    s = sheet()
    value = s.briefs["EMP_CHOM"].fact_ids["value"]
    provider = FakeProvider([{"paragraphs": [f"Le chômage atteint {{{{{value}}}}}."]}])
    result = write_section(provider, s, SECTION, TEMPLATE, "fr")
    assert result.mode == "ai" and result.attempts == 1
    text, used = render(result.paragraphs[0], s, "fr")
    assert text == "Le chômage atteint 20,6 %." and used == [value]


def test_invented_number_triggers_a_retry_with_the_error() -> None:
    s = sheet()
    value = s.briefs["EMP_CHOM"].fact_ids["value"]
    provider = FakeProvider(
        [
            {"paragraphs": ["Le chômage atteint 20,6 %."]},
            {"paragraphs": [f"Le chômage atteint {{{{{value}}}}}."]},
        ]
    )
    result = write_section(provider, s, SECTION, TEMPLATE, "fr")
    assert result.mode == "ai" and result.attempts == 2
    assert "20,6" in provider.prompts[1]  # the model is told exactly what was wrong


def test_invalid_json_three_times_falls_back_to_templates() -> None:
    s = sheet()
    result = write_section(
        FakeProvider([None, {"x": 1}, {"paragraphs": []}]), s, SECTION, TEMPLATE, "fr"
    )
    assert result.mode == "fallback" and result.attempts == 3
    assert check_paragraphs(result.paragraphs, s) == []  # fallback obeys the same rule
    text, _ = render(result.paragraphs[0], s, "fr")
    assert "20,6 %" in text and "non disponible" in text


def test_unreachable_model_falls_back_in_arabic() -> None:
    result = write_section(
        FakeProvider([LLMError("Ollama injoignable")]), sheet(), SECTION, TEMPLATE, "ar"
    )
    assert result.mode == "fallback"
    assert "معدل البطالة" in result.paragraphs[0]


def test_no_provider_means_fallback() -> None:
    assert write_section(None, sheet(), SECTION, TEMPLATE, "fr").mode == "fallback"


def test_sovereign_mode_refuses_external_ai() -> None:
    with pytest.raises(SovereignModeError):
        get_provider(Settings(llm_provider="anthropic", sovereign_mode=True, anthropic_api_key="k"))


def test_sovereign_mode_is_the_default_and_local_ai_is_allowed() -> None:
    settings = Settings(_env_file=None)
    assert settings.sovereign_mode is True
    provider = get_provider(Settings(llm_provider="ollama"))
    assert provider is not None and provider.local is True


def test_render_drops_a_unit_repeated_after_the_value() -> None:
    from app.services.reports.facts import Fact

    sheet = FactSheet(unit={}, identity={})
    sheet.facts.append(
        Fact(
            id="F001",
            kind="value",
            indicator="DEM_POP",
            label={"fr": "Population", "ar": "السكان"},
            text={"fr": "168 391 habitants", "ar": "168 391 نسمة"},
        )
    )
    text, used = render("soit {{F001}} habitants au total", sheet, "fr")
    assert text == "soit 168 391 habitants au total" and used == ["F001"]
    text, _ = render("يبلغ {{F001}} نسمة", sheet, "ar")
    assert text == "يبلغ 168 391 نسمة"


CITIZENS_SECTION = next(s for s in TEMPLATE.sections if s.code == "citoyens")


def citizen_sheet(total: int) -> FactSheet:
    from app.services.reports.facts import add_citizen_facts

    s = sheet()
    themes = (
        [
            {
                "code": "voirie",
                "label": {"fr": "Voirie et trottoirs", "ar": "الطرق والأرصفة"},
                "count": 3,
            }
        ]
        if total
        else []
    )
    add_citizen_facts(
        s, {"total": total, "themes": themes, "fictitious": True, "too_few": total < 5}
    )
    return s


def test_section_7_counts_are_facts_and_the_fallback_cites_them() -> None:
    s = citizen_sheet(4)
    result = write_section(None, s, CITIZENS_SECTION, TEMPLATE, "fr")
    text = " ".join(result.paragraphs)
    assert result.mode == "fallback"
    assert (
        "Contributions localisées dans l'unité : {{" in text and "Voirie et trottoirs ({{" in text
    )
    assert "trop peu nombreuses pour conclure" in text
    assert check_paragraphs(result.paragraphs, s, "fr", meaning=False) == []
    rendered = render(result.paragraphs[0], s, "fr")[0]
    assert "4 contributions" in rendered and "3 contributions" in rendered


def test_section_7_without_consultation_or_without_contribution() -> None:
    no_consultation = write_section(None, sheet(), CITIZENS_SECTION, TEMPLATE, "fr")
    assert no_consultation.mode == "auto" and "Aucune consultation" in no_consultation.paragraphs[0]
    empty = write_section(None, citizen_sheet(0), CITIZENS_SECTION, TEMPLATE, "ar")
    assert empty.mode == "auto" and "لم يتم تحديد أي مساهمة" in empty.paragraphs[0]
