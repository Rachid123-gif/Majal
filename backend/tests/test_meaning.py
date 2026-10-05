"""Meaning controls (config/report_templates/controles.yaml): trend words must follow the sign
of the computed value, and nothing may be stated about data that is missing.

The bad sentences below are real errors written by the models during the benchmark
(docs/benchmarks/); the good ones are the model phrases of the report outline.
"""

from typing import Any

import pytest

from app.services.reports.facts import FactSheet, build_fact_sheet
from app.services.reports.meaning import check_meaning, load_controls
from app.services.reports.writer import check_paragraphs, render
from app.settings import REPO_ROOT

CONTROLS = load_controls(REPO_ROOT / "config" / "report_templates" / "controles.yaml")
STATUSES = {
    "deficit_marked": {"fr": "Déficit marqué", "ar": "خصاص واضح"},
    "watch": {"fr": "À surveiller", "ar": "يستدعي المتابعة"},
    "ok": {"fr": "Dans la moyenne ou au-dessus", "ar": "في المتوسط أو أفضل"},
    "context": {"fr": "Contexte (sans évaluation)", "ar": "سياق (دون تقييم)"},
    "not_evaluable": {"fr": "Non évaluable", "ar": "غير قابل للتقييم"},
    "not_available": {"fr": "Non disponible", "ar": "غير متوفر"},
}
STATUS_OF = {"EMP_CHOM": "watch", "SAN_HOP": "ok"}


def indicator(code: str, fr: str, ar: str, unit: tuple[str, str], formula: str) -> dict[str, Any]:
    return {
        "code": code,
        "axis": "x",
        "label": {"fr": fr, "ar": ar},
        "unit": {"fr": unit[0], "ar": unit[1]},
        "direction": "neutral",
        "decimals": 1,
        "reference": {"type": "relative", "value": 18.9} if code == "EMP_CHOM" else None,
        "source_expected": "HCP",
        "formula": formula,
        "requested_from": None,
    }


INDICATORS = [
    indicator("DEM_POP", "Population 2024", "عدد السكان 2024", ("habitants", "نسمة"), "raw"),
    indicator(
        "DEM_TCAM",
        "Croissance annuelle moyenne 2014-2024",
        "معدل النمو السنوي المتوسط 2014-2024",
        ("% par an", "% سنوياً"),
        "cagr",
    ),
    indicator(
        "URB_CROIS",
        "Croissance de la surface bâtie 2015-2020",
        "نمو المساحة المبنية 2015-2020",
        ("%", "%"),
        "change",
    ),
    indicator("EMP_CHOM", "Taux de chômage", "معدل البطالة", ("%", "%"), "raw"),
    indicator(
        "SAN_ESSP",
        "Établissements de soins de santé primaires pour 10 000 habitants",
        "مؤسسات العلاجات الصحية الأولية لكل 10000 نسمة",
        ("", ""),
        "ratio",
    ),
    indicator(
        "SAN_HOP",
        "Distance moyenne à l'hôpital le plus proche",
        "متوسط المسافة إلى أقرب مستشفى",
        ("km", "كلم"),
        "distance_mean",
    ),
    indicator(
        "EDU_ECOLES",
        "Établissements primaires et collégiaux pour 1 000 enfants de 6 à 14 ans",
        "مؤسسات التعليم الابتدائي والإعدادي لكل 1000 طفل من 6 إلى 14 سنة",
        ("", ""),
        "ratio",
    ),
    indicator(
        "EDU_PROX",
        "Part de la population à moins de 1 km d'une école",
        "نسبة السكان على بعد أقل من 1 كلم من مدرسة",
        ("%", "%"),
        "proximity_share",
    ),
    indicator(
        "MOB_15MIN",
        "Part de la population ayant école, soins de santé primaires et marché à moins de 1 km",
        "نسبة السكان الذين تتوفر لهم مدرسة ومؤسسة للعلاجات الأولية وسوق على بعد أقل من 1 كلم",
        ("%", "%"),
        "proximity_share",
    ),
]
VALUES = {
    "DEM_POP": 168391,
    "DEM_TCAM": -1.43,
    "URB_CROIS": 0.9,
    "EMP_CHOM": 20.6,
    "SAN_ESSP": None,
    "SAN_HOP": 1.43,
    "EDU_ECOLES": None,
    "EDU_PROX": 99.6,
    "MOB_15MIN": None,
}


def make_sheet() -> FactSheet:
    diagnostic = {
        "evaluation": {
            "reference_label": {"fr": "de l'agglomération", "ar": "التجمع الحضري"},
            "label": {"fr": "Évaluation relative", "ar": "تقييم نسبي"},
            "statuses": STATUSES,
        },
        "grid": {"label": {"fr": "Grille v0", "ar": "الشبكة v0"}},
        "indicators": INDICATORS,
        "units": [
            {
                "id": 19,
                "name_fr": "Yacoub El Mansour",
                "name_ar": "يعقوب المنصور",
                "level": "arrondissement",
                "official_code": None,
                "area_km2": 16.9,
                "values": {
                    code: {
                        "value": value,
                        "status": STATUS_OF.get(code, "context")
                        if value is not None
                        else "not_available",
                        "year": 2024,
                        "sources": ["HCP"],
                    }
                    for code, value in VALUES.items()
                },
            }
        ],
    }
    identity = {
        "name_fr": "Yacoub El Mansour",
        "name_ar": "يعقوب المنصور",
        "description_fr": "arrondissement",
        "description_ar": "مقاطعة",
    }
    return build_fact_sheet(diagnostic, 19, identity)


SHEET = make_sheet()


def ref(code: str, kind: str = "value") -> str:
    return "{{" + SHEET.briefs[code].fact_ids[kind] + "}}"


def issues(text: str, lang: str = "fr") -> list[str]:
    return [i.describe() for i in check_meaning(text, SHEET, CONTROLS, lang)]  # type: ignore[arg-type]


POP, TCAM, CHOM = ref("DEM_POP"), ref("DEM_TCAM"), ref("EMP_CHOM")
CHOM_REF = ref("EMP_CHOM", "reference")

GOOD = [
    # The model phrases of the outline (config/report_templates/diagnostic_commune.yaml).
    (
        "fr",
        f"La population de l'arrondissement s'établit à {POP} en 2024. Elle recule de {TCAM} en moyenne depuis 2014.",
    ),
    (
        "fr",
        f"Le taux de chômage atteint {CHOM}, contre {CHOM_REF} ; l'arrondissement se situe dans la catégorie « à surveiller ».",
    ),
    (
        "fr",
        "Les données disponibles ne permettent pas d'évaluer l'offre de soins de santé primaires. La carte sanitaire est à demander à la délégation de la Santé.",
    ),
    ("ar", f"يبلغ عدد سكان المقاطعة {POP} سنة 2024، ويتراجع بمعدل {TCAM} في المتوسط منذ 2014."),
    (
        "ar",
        f"يبلغ معدل البطالة {CHOM}، مقابل {CHOM_REF}؛ وتندرج المقاطعة ضمن فئة «يستدعي المتابعة».",
    ),
    (
        "ar",
        "لا تسمح المعطيات المتوفرة بتقييم العرض من العلاجات الصحية الأولية. ويُطلب الحصول على الخريطة الصحية من المندوبية الإقليمية للصحة.",
    ),
    # Label words are not trend words; « en baisse » follows the sign.
    (
        "fr",
        f"La population a connu une croissance annuelle moyenne de {TCAM} entre 2014 et 2024, en baisse.",
    ),
    ("fr", f"La surface bâtie progresse de {ref('URB_CROIS')} entre 2015 et 2020."),
    ("ar", f"سجل معدل النمو السنوي المتوسط {TCAM}، أي انخفاض في عدد السكان."),
    # Missing data, said as missing.
    (
        "fr",
        "Les établissements de soins de santé primaires pour 10 000 habitants manquent de données.",
    ),
    (
        "fr",
        "La part de la population ayant école, soins de santé primaires et marché à moins de 1 km n'est pas disponible.",
    ),
    (
        "ar",
        "تُعدّ بيانات مؤسسات التعليم الابتدائي والإعدادي غير متوفرة، ويُطلب من الجهات المعنية توفيرها.",
    ),
    # An available indicator sharing a theme word: « santé » and « écoles » are measured.
    (
        "fr",
        f"La distance moyenne à l'hôpital le plus proche, {ref('SAN_HOP')}, facilite l'accès aux soins de santé.",
    ),
    ("fr", "Les habitants ont accès à des écoles à proximité."),
]

BAD = [
    # Trend opposite to the sign (aya-expanse:8b).
    (
        "fr",
        "L'évolution de ces indicateurs confirme une tendance à l'augmentation de la population.",
        "est faux pour « Croissance annuelle moyenne",
    ),
    ("ar", "شهد عدد السكان نمواً مطرداً خلال الفترة.", "est faux pour"),
    (
        "fr",
        f"La population recule de {TCAM}, mais la surface bâtie est en baisse.",
        "est faux pour « Croissance de la surface bâtie",
    ),
    # Trend for an indicator observed once (qwen3:8b).
    (
        "fr",
        f"Le taux de chômage {CHOM} est en hausse.",
        "aucune évolution n'est mesurée pour « Taux de chômage »",
    ),
    # Statements about missing data (aya-expanse:8b).
    (
        "fr",
        "Les habitants bénéficient de l'accès à des écoles et des marchés à proximité.",
        "« marché",
    ),
    ("ar", "في مجال الصحة، تتوفر مؤسسات علاجية أولية قريبة من السكان.", "علاجية أولية"),
    (
        "ar",
        "تتوفر مؤسسات تعليمية ابتدائية وإعدادية لتلبية احتياجات الأطفال، على الرغم من أن البيانات الدقيقة غير متوفرة.",
        "مؤسسات تعليمية",
    ),
    ("fr", "L'absence de centres de santé pénalise les habitants.", "centres de santé"),
    # Arabic: two numbers side by side (qwen3:8b).
    ("ar", f"يبلغ عدد سكانها في سنة 2024 {POP}.", "deux nombres collés"),
]


@pytest.mark.parametrize(("lang", "text"), GOOD)
def test_correct_sentences_pass(lang: str, text: str) -> None:
    assert issues(text, lang) == []


@pytest.mark.parametrize(("lang", "text", "expected"), BAD)
def test_false_statements_are_rejected(lang: str, text: str, expected: str) -> None:
    found = issues(text, lang)
    assert found, text
    assert any(expected in issue for issue in found), found


def test_stable_is_accepted_only_within_the_band() -> None:
    assert issues(f"La population est stable ({TCAM} par an).")  # -1,43 % : not stable


def test_fallback_texts_pass_every_check() -> None:
    from app.services.reports.template import load_template
    from app.services.reports.writer import fallback_section

    template = load_template(REPO_ROOT / "config" / "report_templates" / "diagnostic_commune.yaml")
    for section in template.sections:
        if section.mode != "ai":
            continue
        for lang in ("fr", "ar"):
            result = fallback_section(SHEET, section, lang, "", None, None)
            assert check_paragraphs(result.paragraphs, SHEET, lang, CONTROLS) == [], section.code


def test_render_drops_the_sign_after_a_decrease_verb_and_repeated_units() -> None:
    text, _ = render(f"Elle recule de {TCAM} par an en moyenne.", SHEET, "fr")
    assert text == "Elle recule de 1,4 % par an en moyenne."
    text, _ = render(f"Elle évolue de {TCAM}.", SHEET, "fr")
    assert text == "Elle évolue de -1,4 % par an."
    text, _ = render(f"ويتراجع بمعدل {TCAM} في المتوسط", SHEET, "ar")
    assert text == "ويتراجع بمعدل 1,4 % سنوياً في المتوسط"


def test_final_check_accepts_the_value_without_its_sign() -> None:
    from app.services.reports.numbers import check_rendered

    text, used = render(f"Elle recule de {TCAM} en moyenne.", SHEET, "fr")
    values = [f.text["fr"] for u in used if (f := SHEET.get(u)) is not None]
    assert check_rendered(text, values, SHEET.years) == []


@pytest.mark.parametrize(
    ("lang", "text"),
    [
        ("fr", "L'arrondissement présente une vulnérabilité notable en matière d'emploi."),
        ("fr", "La situation est préoccupante."),
        ("ar", "شهدت المقاطعة تطوراً ملحوظاً في عدد سكانها."),
    ],
)
def test_subjective_judgements_are_rejected(lang: str, text: str) -> None:
    assert any("jugement subjectif" in issue for issue in issues(text, lang))


def test_spaced_fact_references_are_normalized() -> None:
    from app.services.reports.numbers import normalize_refs

    assert normalize_refs("معدل البطالة F 011 و F-012") == "معدل البطالة {{F011}} و {{F012}}"


def test_status_must_be_the_computed_one() -> None:
    hop = ref("SAN_HOP")
    assert (
        issues(
            f"Le taux de chômage atteint {CHOM} ; il se situe dans la catégorie « à surveiller »."
        )
        == []
    )
    found = issues(
        f"La distance moyenne à l'hôpital le plus proche s'établit à {hop} ; elle est à surveiller."
    )
    assert any("a le statut « Dans la moyenne ou au-dessus »" in i for i in found), found
    found = issues(f"يبلغ معدل البطالة {CHOM}، ما يشير إلى خصاص واضح.", "ar")
    assert any("a le statut « À surveiller »" in i for i in found), found


def test_sign_is_dropped_when_the_decrease_verb_is_a_few_words_before() -> None:
    text, _ = render(f"ويتراجع معدل النمو السنوي المتوسط بين 2014 و2024 بمعدل {TCAM}.", SHEET, "ar")
    assert "بمعدل 1,4 %" in text
    text, _ = render(f"La population recule. Elle atteint {TCAM}.", SHEET, "fr")
    assert "-1,4 %" in text  # another sentence: the sign stays
