"""Anti-invention control: at least 15 trap cases (BRIEF §9.5)."""

import pytest

from app.services.reports.numbers import check_rendered, check_text, definitional_phrases

FACTS = {"F001", "F002", "F003"}
YEARS = {2014, 2024}
DEFINITIONAL = definitional_phrases(
    [
        "Part des moins de 15 ans",
        "Part de la population à moins de 500 m d'un arrêt de bus ou de tramway",
        "Établissements de soins de santé primaires pour 10 000 habitants",
        "Établissements primaires et collégiaux pour 1 000 enfants de 6 à 14 ans",
        "نسبة السكان دون 15 سنة",
    ]
)


def issues(text: str) -> list[str]:
    return [i.kind for i in check_text(text, FACTS, YEARS, DEFINITIONAL)]


@pytest.mark.parametrize(
    "text",
    [
        "La population atteint {{F001}}.",
        "Le chômage reste élevé ({{F002}}), au-dessus de la moyenne {{F003}}.",
        "Entre 2014 et 2024, la population a diminué.",
        "La part des moins de 15 ans s'établit à {{F002}}.",
        "Seuls {{F003}} des habitants vivent à moins de 500 m d'un arrêt de bus ou de tramway.",
        "Les données sur les établissements pour 1 000 enfants de 6 à 14 ans ne sont pas disponibles.",
        "Un quartier dense, une population jeune.",
        "بلغ عدد السكان {{F001}} سنة 2024.",
        "نسبة السكان دون 15 سنة تبلغ {{F002}}.",
    ],
)
def test_clean_texts_pass(text: str) -> None:
    assert issues(text) == []


@pytest.mark.parametrize(
    ("text", "kind"),
    [
        ("La population atteint 168 391 habitants.", "number"),  # invented number
        ("Le taux de chômage est de 20,6.", "number"),  # copied value
        ("Le taux de chômage est de 21 %.", "number"),  # rounded differently
        ("Le chômage touche un habitant sur cinq.", "word"),  # number in words
        ("La population a doublé en dix ans.", "word"),  # number in words
        ("Près de la moitié des ménages sont raccordés.", "word"),  # fraction in words
        ("Le taux atteint {{F002}}, soit trois points de plus.", "word"),
        ("La part est de vingt pour cent.", "word"),  # « pour cent » + number word
        ("Le taux est en hausse de quelques pour cent.", "percent"),  # recalculated percentage
        ("La croissance est de 1,4 % par an.", "number"),
        ("بلغ معدل البطالة ٢٠٫٦ في المائة.", "number"),  # Arabic-Indic digits
        ("بلغ عدد السكان ۱۶۸۳۹۱ نسمة.", "number"),  # Persian digits
        ("تضاعف عدد السكان مرتين خلال عشر سنوات.", "word"),  # Arabic number word
        ("نصف الأسر غير مرتبطة بالشبكة.", "word"),  # Arabic fraction
        ("La commune se classe au 3e rang.", "number"),  # invented rank
        ("Elle occupe la deuxième place.", "word"),  # ordinal in words
        ("Le taux atteint {{F099}}.", "unknown_fact"),  # unknown fact id
        ("Les moins de 16 ans représentent {{F002}}.", "number"),  # not a label threshold
        ("En 2019, la population était plus faible.", "number"),  # year absent from facts
    ],
)
def test_traps_are_caught(text: str, kind: str) -> None:
    assert kind in issues(text)


def test_final_check_on_rendered_text() -> None:
    rendered = "La population atteint 168 391 habitants, contre 150 000 en 2014."
    found = check_rendered(rendered, ["168 391 habitants"], YEARS, DEFINITIONAL)
    assert [i.token for i in found] == ["150 000"]


def test_fact_references_are_normalized_without_letting_numbers_through() -> None:
    from app.services.reports.numbers import normalize_refs

    assert normalize_refs("taux {{F012, F013}} ici") == "taux {{F012}}, {{F013}} ici"
    assert normalize_refs("[F012] et {F013}") == "{{F012}} et {{F013}}"
    assert normalize_refs("valeur F012.") == "valeur {{F012}}."
    assert normalize_refs("{{F012}}") == "{{F012}}"
    # A number stays a number: the check still catches it.
    assert check_text(normalize_refs("soit 12 % [F012]"), {"F012"}, set(), [])
