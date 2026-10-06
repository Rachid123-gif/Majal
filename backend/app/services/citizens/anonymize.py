"""Anonymisation of citizen contributions, BEFORE any processing by a language model.

Rules (config/citizens/anonymisation.yaml): e-mail addresses, Moroccan phone numbers, national
identity card numbers (CIN), number plates, precise addresses, then person names (first-name
list, and any name introduced by a cue such as « je m'appelle » / « اسمي »). Known place names
are protected first, so that « Avenue Hassan II » is never masked. An optional pass by the local
model may report remaining names; they are masked only if they appear verbatim in the text
and are not known places.

The report says what was masked (type, position, method), never the masked value itself.
"""

import re
import unicodedata
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any, Literal

from pydantic import Field

from app.config_loader.territory import StrictModel
from app.config_loader.validation import load_model
from app.services.llm.base import LLMError, LLMProvider

Kind = Literal["person", "phone", "email", "national_id", "plate", "address"]
ORDER: tuple[Kind, ...] = ("email", "phone", "national_id", "plate", "address", "person")


class Placeholder(StrictModel):
    fr: str
    ar: str


class FirstNames(StrictModel):
    latin: list[str] = Field(default_factory=list)
    arabic: list[str] = Field(default_factory=list)
    ambiguous: list[str] = Field(default_factory=list)


class CueLists(StrictModel):
    fr: list[str] = Field(default_factory=list)
    ar: list[str] = Field(default_factory=list)
    darija: list[str] = Field(default_factory=list)

    def all(self) -> list[str]:
        return self.fr + self.ar + self.darija


class Cues(StrictModel):
    strong: CueLists
    weak: CueLists


class AnonymisationConfig(StrictModel):
    placeholders: dict[Kind, Placeholder]
    first_names: FirstNames
    cues: Cues


def load_anonymisation(path: Path) -> AnonymisationConfig:
    return load_model(path, AnonymisationConfig, {"first_names": "first_names:\n  latin: [Karim]"})


@lru_cache(maxsize=2)
def cached_config(path: Path) -> AnonymisationConfig:
    return load_anonymisation(path)


# ------------------------------------------------------------------ patterns

AR = "ء-ي"
_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹", "01234567890123456789")
SEP = r"[\s.\-]?"
PATTERNS: dict[Kind, re.Pattern[str]] = {
    "email": re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+", re.UNICODE),
    # +212 / 00212 / 0, then 5, 6 or 7, then 8 digits with optional separators.
    "phone": re.compile(rf"(?<![\w+])(?:\+212{SEP}|00212{SEP}|0)[5-7](?:{SEP}\d){{8}}(?!\d)"),
    # Moroccan CIN: one or two letters followed by 5 or 6 digits.
    "national_id": re.compile(r"(?<![\w])[A-Z]{1,2}\d{5,6}(?![\w])"),
    # Plates: 12345-أ-6 (Arabic letter between two numbers), also with Latin letters or « | ».
    "plate": re.compile(rf"(?<!\d)\d{{1,5}}\s*[-|/]\s*(?:[{AR}]|[A-Z])\s*[-|/]\s*\d{{1,2}}(?!\d)"),
    "address": re.compile(
        r"(?:\b(?:n°|no|numéro)\s*\d+\s*,?\s*(?:de la |de l'|du |des )?"
        r"(?:rue|avenue|av\.|bd|boulevard|impasse|lotissement|résidence|immeuble|bloc|derb)\s+"
        r"[^,.;:\n]{1,40}"
        # A one-letter preposition may be glued in front (« فالرقم 00 … »): kept out of the span.
        rf"|(?<![{AR}])[وفبل]?(?P<ar>(?:ال)?رقم\s*\d+\s*،?\s*(?:زنقة|شارع|درب|زقاق|إقامة|عمارة|تجزئة)"
        rf"\s+[{AR}]+(?:\s+[{AR}]+)?))",
        re.IGNORECASE,
    ),
}


@dataclass
class Masked:
    kind: Kind
    start: int
    end: int
    method: str  # rule | cue | list | model

    def to_json(self) -> dict[str, Any]:
        return {"type": self.kind, "start": self.start, "end": self.end, "method": self.method}


@dataclass
class Result:
    text: str
    masked: list[Masked] = field(default_factory=list)

    def report(self) -> dict[str, Any]:
        counts: dict[str, int] = {}
        for item in self.masked:
            counts[item.kind] = counts.get(item.kind, 0) + 1
        return {"counts": counts, "items": [m.to_json() for m in self.masked]}


def _normalize(text: str) -> str:
    """Same length as the input: positions stay valid."""
    return unicodedata.normalize("NFC", text).translate(_DIGITS)


def _overlaps(spans: list[tuple[int, int]], start: int, end: int) -> bool:
    return any(start < b and a < end for a, b in spans)


def _word(name: str, arabic: bool) -> re.Pattern[str]:
    n = re.escape(name)
    if arabic:
        return re.compile(rf"(?<![{AR}])[وفبل]?{n}(?![{AR}])")
    return re.compile(rf"(?<![\w-]){n}(?![\w-])")


def _is_arabic(text: str) -> bool:
    return bool(re.search(f"[{AR}]", text))


def find_spans(
    text: str, config: AnonymisationConfig, protected: list[str] | None = None
) -> list[Masked]:
    source = _normalize(text)
    taken: list[tuple[int, int]] = []
    # Known places are protected (never masked as a name).
    for place in sorted({p for p in protected or [] if p}, key=len, reverse=True):
        for match in re.finditer(re.escape(_normalize(place)), source, re.IGNORECASE):
            taken.append(match.span())
    shielded = list(taken)
    found: list[Masked] = []

    def add(kind: Kind, start: int, end: int, method: str) -> None:
        if not _overlaps([(m.start, m.end) for m in found], start, end):
            found.append(Masked(kind, start, end, method))

    for kind in ORDER[:-1]:
        for match in PATTERNS[kind].finditer(source):
            span = (
                match.span("ar")
                if "ar" in match.re.groupindex and match.group("ar")
                else match.span()
            )
            if not _overlaps([(m.start, m.end) for m in found], *span):
                add(kind, *span, "rule")

    blocked = shielded + [(m.start, m.end) for m in found]
    names = config.first_names
    ambiguous = set(names.ambiguous)

    # 1. Names after a cue.
    lower = source.casefold()
    for strength in ("strong", "weak"):
        for cue in getattr(config.cues, strength).all():
            for match in re.finditer(
                rf"(?<![\w{AR}]){re.escape(cue.casefold())}(?![\w{AR}])", lower
            ):
                rest = source[match.end() :]
                token = re.match(rf"\s*[:,]?\s*([A-ZÀ-Ý][\w'-]+|[{AR}]+)", rest)
                if not token:
                    continue
                word = token.group(1)
                start = match.end() + token.start(1)
                end = start + len(word)
                listed = word in names.latin or word in names.arabic or word in ambiguous
                strong_ok = strength == "strong" and (
                    listed or not _is_arabic(word) or cue in config.cues.strong.ar
                )
                if (strong_ok or listed) and not _overlaps(blocked, start, end):
                    add("person", start, end, "cue")
                    blocked.append((start, end))

    # 2. Listed (unambiguous) first names anywhere.
    for name in names.latin + names.arabic:
        if name in ambiguous:
            continue
        for match in _word(name, _is_arabic(name)).finditer(source):
            start = match.end() - len(name)
            if not _overlaps(blocked, start, match.end()):
                add("person", start, match.end(), "list")
                blocked.append((start, match.end()))
    return sorted(found, key=lambda m: m.start)


def apply(text: str, spans: list[Masked], config: AnonymisationConfig, lang: str = "fr") -> str:
    out = text
    for item in sorted(spans, key=lambda m: m.start, reverse=True):
        label = getattr(config.placeholders[item.kind], "ar" if lang == "ar" else "fr")
        out = out[: item.start] + label + out[item.end :]
    return out


def anonymize(text: str, config: AnonymisationConfig, protected: list[str] | None = None) -> Result:
    spans = find_spans(text, config, protected)
    return Result(apply(text, spans, config), spans)


# ------------------------------------------------------------------ optional model pass

NAMES_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {"names": {"type": "array", "items": {"type": "string"}}},
    "required": ["names"],
}
NAMES_SYSTEM = (
    "Tu aides à anonymiser un texte. Liste les prénoms et noms de PERSONNES qui restent dans le "
    "texte, exactement comme ils sont écrits. Ne liste ni les lieux, ni les quartiers, ni les "
    "rues, ni les institutions. Si aucun nom de personne ne reste, renvoie une liste vide. "
    'Réponds en JSON : {"names": ["…"]}.'
)


def model_pass(
    result: Result,
    original: str,
    provider: LLMProvider | None,
    config: AnonymisationConfig,
    protected: list[str] | None = None,
) -> Result:
    """Ask the local model for remaining names in the already masked text. A name is masked
    only if it appears verbatim in the original text, outside known places and masked spans."""
    if provider is None:
        return result
    try:
        answer = provider.generate_json(NAMES_SYSTEM, result.text, NAMES_SCHEMA, temperature=0)
    except LLMError:
        return result
    names = (answer.data or {}).get("names") or []
    source = _normalize(original)
    places = [_normalize(p).casefold() for p in protected or [] if p]
    spans = list(result.masked)
    for name in names:
        if not isinstance(name, str) or len(name.strip()) < 2:
            continue
        name = _normalize(name.strip())
        if any(name.casefold() in place for place in places):
            continue
        for match in _word(name, _is_arabic(name)).finditer(source):
            start = match.end() - len(name)
            if not _overlaps([(m.start, m.end) for m in spans], start, match.end()):
                spans.append(Masked("person", start, match.end(), "model"))
    spans.sort(key=lambda m: m.start)
    return Result(apply(original, spans, config), spans)
