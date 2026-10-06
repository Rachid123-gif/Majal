"""Anonymisation before any AI processing (BRIEF §9.6, §14): tested on the traps of the
fictitious set and on a list of difficult cases. All personal data below is fictitious
(phones 06 00…, CIN ZZ…/ZY…, @example.com addresses)."""

from typing import Any

import pytest
import yaml

from app.services.citizens.anonymize import anonymize, load_anonymisation, model_pass
from app.services.llm.base import LLMResult
from app.settings import REPO_ROOT

CONFIG = load_anonymisation(REPO_ROOT / "config" / "citizens" / "anonymisation.yaml")
SET = yaml.safe_load(
    (REPO_ROOT / "data" / "fictif" / "rabat" / "contributions.yaml").read_text(encoding="utf-8")
)["contributions"]
PLACES = sorted(
    {c["place"] for c in SET if c.get("place")}
    | {c["unit"] for c in SET}
    | {"Avenue Hassan II", "Avenue Mohammed V", "Moulay Ismail", "Hay Al Fath", "Agdal"}
)


def masked_values(text: str) -> list[str]:
    return [text[m.start : m.end] for m in anonymize(text, CONFIG, PLACES).masked]


def test_every_trap_of_the_fictitious_set_is_masked_and_nothing_else() -> None:
    expected = found = correct = 0
    for c in SET:
        values = masked_values(c["text"])
        truth = [p["value"] for p in c["pii"]]
        expected += len(truth)
        found += len(values)
        correct += sum(1 for v in values if any(v == t or v in t or t in v for t in truth))
        for t in truth:
            assert any(t == v or t in v for v in values), (c["id"], t, values)
    assert expected >= 30
    assert correct == found  # precision 100 %: no word of the 140 texts is masked wrongly


@pytest.mark.parametrize(
    ("text", "kind", "value"),
    [
        ("Appelez le 06-00-00-00-07 svp", "phone", "06-00-00-00-07"),
        ("Mon numéro : +212 6 00 00 00 08.", "phone", "+212 6 00 00 00 08"),
        ("رقمي 00212600000009", "phone", "00212600000009"),
        ("Fixe : 05 00 00 00 12", "phone", "05 00 00 00 12"),
        ("التيليفون ٠٦٠٠٠٠٠٠١١ فقط", "phone", "٠٦٠٠٠٠٠٠١١"),
        ("Tél. 0700000010", "phone", "0700000010"),
        ("CIN ZY000001 à la mairie", "national_id", "ZY000001"),
        ("écrire à x.y+test@example.com merci", "email", "x.y+test@example.com"),
        ("contact@example.org", "email", "contact@example.org"),
        ("السيارة 00000-أ-01 متوقفة", "plate", "00000-أ-01"),
        ("plaque 00000 | ب | 9", "plate", "00000 | ب | 9"),
        (
            "j'habite au numéro 0, impasse des Lilas, près du parc",
            "address",
            "numéro 0, impasse des Lilas",
        ),
        ("أسكن برقم 00 شارع المثال", "address", "رقم 00 شارع المثال"),
        ("Je m'appelle Zinebette et je vis ici", "person", "Zinebette"),
        ("اسمي ريحانة وأسكن هنا", "person", "ريحانة"),
        ("smiti Kawtar, mn l7ouma", "person", "Kawtar"),
        ("Mon voisin Hicham a signalé la fuite", "person", "Hicham"),
        ("صاحبي يوسف شاف كلشي", "person", "يوسف"),
        ("أنا سعيد، أسكن في الحي", "person", "سعيد"),
        ("Signé : Rachida", "person", "Rachida"),
    ],
)
def test_difficult_cases_are_masked(text: str, kind: str, value: str) -> None:
    result = anonymize(text, CONFIG, PLACES)
    spans = [(m.kind, text[m.start : m.end]) for m in result.masked]
    assert (kind, value) in spans, spans
    assert value not in result.text


@pytest.mark.parametrize(
    "text",
    [
        "Les trottoirs de l'Avenue Hassan II sont abîmés.",
        "À Yacoub El Mansour, les bus sont rares.",
        "Le marché de Moulay Ismail est fermé.",
        "Il y a 45 élèves par classe depuis 2024.",
        "La route RP4025 est coupée, à 5 km du centre.",
        "Le loyer a augmenté de 300 dh ; le bus de 06h30 est plein.",
        "أنا ساكن هنا منذ سنوات",
        "حسن التنظيم مطلوب في السوق",
        "زنقة الأمل مظلمة",
        "Je suis inquiet pour la sécurité des enfants.",
        "Je suis Rbati depuis 30 ans et je n'ai jamais vu ça.",
        "Je suis Marocaine, enseignante, et je demande un jardin.",
        "أنا طالب في الجامعة",
        "أنا رباطي منذ صغري",
        "ana tajer f souk",
        "شارع محمد الخامس مزدحم",
    ],
)
def test_ordinary_words_and_places_are_not_masked(text: str) -> None:
    assert anonymize(text, CONFIG, [*PLACES, "شارع محمد الخامس"]).masked == []


def test_the_report_never_contains_the_masked_values() -> None:
    text = "Je m'appelle Samira, joignable au 06 00 00 00 02 ou samira@example.com."
    result = anonymize(text, CONFIG, PLACES)
    report = result.report()
    assert report["counts"] == {"person": 1, "phone": 1, "email": 1}
    serialized = str(report)
    assert "Samira" not in serialized and "06 00" not in serialized and "@" not in serialized
    assert result.text == "Je m'appelle [NOM], joignable au [TÉLÉPHONE] ou [E-MAIL]."


class NamesProvider:
    name, model, local = "fake", "fake", True

    def __init__(self, names: list[str]) -> None:
        self.names = names
        self.prompts: list[str] = []

    def generate_json(
        self, system: str, prompt: str, schema: dict[str, Any], temperature: float = 0.2
    ) -> LLMResult:
        self.prompts.append(prompt)
        return LLMResult({"names": self.names}, "", 0.01, 5)


def test_the_model_pass_only_masks_names_that_are_really_in_the_text() -> None:
    text = "Zakia habite près de l'Agdal ; mon voisin Hicham aussi."
    first = anonymize(text, CONFIG, PLACES)
    provider = NamesProvider(["Zakia", "Agdal", "Inventé"])
    result = model_pass(first, text, provider, CONFIG, PLACES)
    assert "Hicham" not in provider.prompts[0]  # the model only sees the masked text
    assert result.text == "[NOM] habite près de l'Agdal ; mon voisin [NOM] aussi."
    assert [m.method for m in result.masked] == ["model", "cue"]
