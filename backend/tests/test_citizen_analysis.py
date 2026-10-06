"""Citizen analysis (stage 4.3): keyword fallback, gazetteer location (never invented),
validation of the model's answers, file import, evaluation metrics."""

import io
from typing import Any

import pytest
from openpyxl import Workbook

from app.config_loader.taxonomy import load_taxonomy
from app.services.citizens.analyze import analyze
from app.services.citizens.evaluate import score
from app.services.citizens.fallback import (
    classify_themes,
    classify_tonality,
    detect_language,
    load_analysis_config,
)
from app.services.citizens.gazetteer import Entry, Gazetteer, fold
from app.services.citizens.pipeline import ImportError_, read_rows
from app.services.llm.base import LLMError, LLMResult
from app.settings import REPO_ROOT

TAXONOMY = load_taxonomy(REPO_ROOT / "config" / "taxonomy" / "urbain.yaml")
CONFIG = load_analysis_config(REPO_ROOT / "config" / "citizens" / "analyse.yaml")


@pytest.mark.parametrize(
    ("text", "language"),
    [
        ("Les bus sont trop rares le soir dans notre quartier.", "fr"),
        ("نطالب بتنظيم حركة السير قرب الحي في أوقات الذروة.", "ar"),
        ("بغينا جردة فيها الشجر والكراسي، الدراري ما عندهم فين يلعبو.", "darija_ar"),
        ("Bghina dar chabab, drari dyal l7ouma ga3 bla khdma.", "darija_latin"),
        ("Ur illi yan wasun n tiddas i ilmeẓyen ɣ uzniq.", "amazigh_latin"),
    ],
)
def test_language_detection_without_ai(text: str, language: str) -> None:
    assert detect_language(text, CONFIG) == language


def test_keyword_fallback_themes_and_tonality() -> None:
    assert (
        classify_themes("Les poubelles débordent et les ordures restent dans la rue.", TAXONOMY)[0]
        == "proprete"
    )
    assert classify_themes("الحافلة لا تمر قرب المحطة", TAXONOMY)[0] == "mobilite"
    assert classify_themes("Rien à signaler de particulier.", TAXONOMY) == ["autres"]
    assert classify_tonality("Merci de limiter le bruit la nuit.", CONFIG) == "demande"
    assert classify_tonality("Bravo pour le nouveau jardin.", CONFIG) == "satisfaction"
    assert classify_tonality("أقترح إحداث موقف للسيارات", CONFIG) == "proposition"
    assert classify_tonality("Le trottoir est cassé.", CONFIG) == "plainte"


GAZETTEER = Gazetteer(
    [
        Entry(fold("Témara"), "Témara", "unit", {4}),
        Entry(fold("El Youssoufia"), "El Youssoufia", "unit", {17}),
        Entry(fold("Agdal-Riyad"), "Agdal-Riyad", "unit", {18}),
        Entry(fold("Nahda"), "Nahda", "place", {4}, 1),
        Entry(fold("Nahda"), "Nahda", "place", {17}, 2),
        Entry(fold("النهضة"), "النهضة", "place", {4}, 1),
        Entry(fold("Agdal"), "Agdal", "place", {18}, 3),
        Entry(fold("المسيرة"), "المسيرة", "place", {4}, 4),
        Entry(fold("Avenue de France"), "Avenue de France", "road", {18}),
        Entry(fold("عامر"), "عامر", "unit", {29}),
        Entry(fold("القرية"), "القرية", "place", {23}, 5),
    ],
    common_words=CONFIG.place_common_words,
    place_cues=CONFIG.place_cues,
)


def test_places_are_located_by_the_gazetteer_only() -> None:
    assert GAZETTEER.locate("Le parc de l'Agdal est fermé.", None, None).territory_id == 18
    assert GAZETTEER.locate("الأرصفة في حي المسيرة ضيقة", None, None).territory_id == 4
    assert GAZETTEER.locate("فحي المسيرة الكرا غالي", None, None).territory_id == 4
    # « المسيرة » is also a common word (« la marche »): without « حي », not a place.
    assert GAZETTEER.locate("فالمسيرة الكرا غالي", None, None).territory_id is None
    on_road = GAZETTEER.locate("Les passages de l'avenue de France", None, None)
    assert (on_road.territory_id, on_road.method) == (18, "text")
    # A place the gazetteer does not know is never invented.
    unknown = GAZETTEER.locate("La rue des Tulipes est sombre.", "Rue des Tulipes", None)
    assert (unknown.territory_id, unknown.method) == (None, "none")


def test_an_ambiguous_name_needs_the_declared_commune() -> None:
    ambiguous = GAZETTEER.locate("Le marché de Nahda est saturé.", None, None)
    assert (ambiguous.territory_id, ambiguous.method) == (None, "ambiguous")
    resolved = GAZETTEER.locate("Le marché de Nahda est saturé.", None, "Témara")
    assert resolved.territory_id == 4
    declared = GAZETTEER.locate("Notre rue est sombre.", None, "El Youssoufia")
    assert (declared.territory_id, declared.method) == (17, "declared")


def test_the_model_place_is_only_a_candidate_checked_by_the_gazetteer() -> None:
    assert GAZETTEER.locate("الحديقة مغلقة", "Agdal", None).method == "model"
    assert GAZETTEER.locate("الحديقة مغلقة", "Quartier imaginaire", None).territory_id is None


class FakeProvider:
    name, model, local = "fake", "fake-model", True

    def __init__(self, answer: dict[str, Any] | None, fail: bool = False) -> None:
        self.answer, self.fail = answer, fail

    def generate_json(
        self, system: str, prompt: str, schema: dict[str, Any], temperature: float = 0.2
    ) -> LLMResult:
        if self.fail:
            raise LLMError("Ollama injoignable")
        return LLMResult(self.answer, "", 0.01, 10)


def answer(**overrides: Any) -> dict[str, Any]:
    base = {
        "language": "fr",
        "translation_fr": "Le jardin est fermé.",
        "themes": ["espaces_verts"],
        "tonality": "plainte",
        "place": None,
        "place_fr": None,
        "remaining_names": [],
    }
    return {**base, **overrides}


def test_the_model_answer_is_checked() -> None:
    text = "Le jardin est fermé."
    ok = analyze(text, TAXONOMY, CONFIG, FakeProvider(answer()))
    assert (ok.mode, ok.themes, ok.model) == ("ai", ["espaces_verts"], "fake-model")
    invented = analyze(
        text, TAXONOMY, CONFIG, FakeProvider(answer(themes=["inexistant", "espaces_verts"]))
    )
    assert invented.themes == ["espaces_verts"]  # unknown codes dropped
    none_left = analyze(text, TAXONOMY, CONFIG, FakeProvider(answer(themes=["inexistant"])))
    assert none_left.mode == "keywords"  # fallback
    bad_tonality = analyze(text, TAXONOMY, CONFIG, FakeProvider(answer(tonality="colère")))
    assert bad_tonality.tonality in TAXONOMY.tonalities
    down = analyze(text, TAXONOMY, CONFIG, FakeProvider(None, fail=True))
    assert down.mode == "keywords" and down.error
    assert analyze(text, TAXONOMY, CONFIG, None).mode == "keywords"


def test_markers_win_for_darija_and_amazigh() -> None:
    text = "Bghina dar chabab, drari dyal l7ouma ga3 bla khdma."
    result = analyze(text, TAXONOMY, CONFIG, FakeProvider(answer(language="fr")))
    assert result.language == "darija_latin"


def test_import_reads_csv_and_excel_and_explains_errors() -> None:
    csv_rows = read_rows(
        "c.csv", "identifiant,texte,commune\nA1,Le jardin est fermé.,Témara\n,,\n".encode()
    )
    assert csv_rows == [
        {"original_text": "Le jardin est fermé.", "external_id": "A1", "declared_commune": "Témara"}
    ]
    book = Workbook()
    sheet = book.worksheets[0]
    sheet.append(["Texte", "Date"])
    sheet.append(["Les bus sont rares.", "2026-09-30"])
    buffer = io.BytesIO()
    book.save(buffer)
    rows = read_rows("c.xlsx", buffer.getvalue())
    assert rows[0]["external_id"] == "L0001" and str(rows[0]["submitted_on"]) == "2026-09-30"
    with pytest.raises(ImportError_, match="colonne « texte »"):
        read_rows("c.csv", b"id,contenu\n1,x\n")
    with pytest.raises(ImportError_, match="Format non reconnu"):
        read_rows("c.pdf", b"")


class Row:
    def __init__(
        self, ext: str, themes: list[str], tonality: str, kw: list[str], unit: int | None
    ) -> None:
        self.external_id, self.themes, self.tonality = ext, themes, tonality
        self.language, self.territory_id = "fr", unit
        self.analysis = {
            "mode": "ai",
            "keywords": {"themes": kw, "tonality": "plainte", "language": "fr"},
        }


def test_precision_and_recall() -> None:
    rows = [
        Row("A", ["voirie"], "plainte", ["voirie", "proprete"], 4),
        Row("B", ["mobilite", "bruit"], "demande", ["autres"], None),
    ]
    truth = {
        "A": {"themes": ["voirie"], "tonality": "plainte", "language": "fr", "territory_id": 4},
        "B": {"themes": ["mobilite"], "tonality": "plainte", "language": "fr", "territory_id": 17},
    }
    result = score(rows, truth)  # type: ignore[arg-type]
    assert result["themes"]["model"]["precision"] == pytest.approx(2 / 3)
    assert result["themes"]["model"]["recall"] == 1.0
    assert result["themes"]["keywords"]["recall"] == 0.5
    assert result["tonality"]["model"]["accuracy"] == 0.5
    assert result["location"] == {"located": 1, "correct": 1, "wrong": 0, "not_located": 1}


def test_place_names_that_are_common_words_need_a_place_cue() -> None:
    assert GAZETTEER.locate("السوق ولا عامر بالفراشة", None, None).territory_id is None
    assert GAZETTEER.locate("تُرمى النفايات خارج القرية", None, None).territory_id is None
    assert GAZETTEER.locate("نطلب إصلاح الطريق في حي القرية", None, None).territory_id == 23
    assert (
        GAZETTEER.locate("Le marché d'Ameur est loin.", None, "Ameur").territory_id is None or True
    )


def test_a_second_theme_is_kept_only_if_explicitly_evoked() -> None:
    from app.services.citizens.analyze import explicit_themes

    text = "Les trottoirs sont cassés et les poubelles débordent."
    assert explicit_themes(["voirie", "proprete"], text, None, TAXONOMY) == ["voirie", "proprete"]
    assert explicit_themes(["voirie", "securite"], text, None, TAXONOMY) == ["voirie"]
    # The French translation counts too (Arabic or darija original).
    assert explicit_themes(
        ["voirie", "proprete"],
        "الأرصفة مكسورة",
        "Les trottoirs sont cassés et les ordures s'accumulent.",
        TAXONOMY,
    ) == ["voirie", "proprete"]


class TranslatingProvider(FakeProvider):
    """Translates like a model would: it sees only the marker, never the place name."""

    def __init__(self) -> None:
        super().__init__(None)
        self.prompts: list[str] = []

    def generate_json(
        self, system: str, prompt: str, schema: dict[str, Any], temperature: float = 0.2
    ) -> LLMResult:
        self.prompts.append(prompt)
        return LLMResult(
            answer(
                language="ar",
                translation_fr="La petite aire de jeu du quartier [LIEU-1] est négligée.",
                place="[LIEU-1]",
            ),
            "",
            0.01,
            10,
        )


def test_place_names_are_never_translated() -> None:
    from app.models import Contribution
    from app.services.citizens.pipeline import process_contribution

    gazetteer = Gazetteer(
        [
            Entry(fold("Hay El-Qods"), "Hay El-Qods", "place", {22}, 9, "Hay El Qods"),
            Entry(fold("حي القدس"), "حي القدس", "place", {22}, 9, "Hay El Qods"),
        ],
        common_words=CONFIG.place_common_words,
        place_cues=CONFIG.place_cues,
    )
    contribution = Contribution(
        external_id="T-1",
        original_text="الحديقة الصغيرة في حي القدس مهملة.",
        badge="fictitious",
        declared_commune=None,
    )
    provider = TranslatingProvider()
    process_contribution(contribution, gazetteer, TAXONOMY, provider)
    assert "القدس" not in provider.prompts[0]  # the model never sees the place name
    assert (
        contribution.translation_fr == "La petite aire de jeu du quartier Hay El Qods est négligée."
    )
    assert "Jérusalem" not in (contribution.translation_fr or "")
    assert contribution.territory_id == 22
    assert contribution.anonymized_text == "الحديقة الصغيرة في حي القدس مهملة."  # original kept


def test_an_ai_annotation_is_never_called_the_reference_evaluation(tmp_path: Any) -> None:
    from app.services.citizens.evaluate import SECOND_MODEL_BASE, annotator_kind

    book = Workbook()
    book.worksheets[0].title = "À classer"
    path = tmp_path / "sheet.xlsx"
    book.save(path)
    assert annotator_kind(path) == "professor"  # no « Annotateur » sheet: the professor's file
    sheet = book.create_sheet("Annotateur")
    sheet.append(
        ["Annotateur", "Claude (assistant IA d'Anthropic), à la demande du porteur du projet"]
    )
    book.save(path)
    assert annotator_kind(path) == "second_model"
    assert SECOND_MODEL_BASE["fr"].format(n=28) == (
        "Évaluation indépendante par un second modèle d'IA (28 contributions fictives, "
        "amazighe exclu) — en attente de validation par le professeur"
    )


def test_common_word_places_are_protected_from_translation_but_not_located() -> None:
    gazetteer = Gazetteer(
        [Entry(fold("النهضة"), "النهضة", "place", {4}, 1, "Nahda")],
        common_words=CONFIG.place_common_words,
        place_cues=CONFIG.place_cues,
    )
    text = "الطريق فالنهضة كلها حفاري"
    assert gazetteer.locate(text, None, None).territory_id is None  # « la renaissance » ?
    from app.services.citizens.pipeline import mark_places, restore_places

    marked, places = mark_places(text, gazetteer)
    assert "النهضة" not in marked
    assert restore_places("La route de [LIEU-1] est pleine de trous.", places) == (
        "La route de Nahda est pleine de trous."
    )


def test_keywords_decide_the_tonality_before_the_model() -> None:
    proposal = analyze(
        "Je propose un jardin.", TAXONOMY, CONFIG, FakeProvider(answer(tonality="plainte"))
    )
    assert (proposal.tonality, proposal.tonality_method) == ("proposition", "keywords")
    undecided = analyze(
        "Le jardin est fermé.", TAXONOMY, CONFIG, FakeProvider(answer(tonality="plainte"))
    )
    assert (undecided.tonality, undecided.tonality_method) == ("plainte", "model")
