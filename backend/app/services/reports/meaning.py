"""Meaning controls: what the number check cannot see (config/report_templates/controles.yaml).

A model can state something false without writing a number. Two checks run on the model's
raw text (with its {{Fxxx}} references), sentence by sentence:

1. Trends: a trend word (hausse, baisse, stable…) is attached to the nearest indicator mention
   (fact reference, exact label or theme keyword). For an indicator that measures an evolution
   the word must match the sign of the computed value; for any other indicator no evolution is
   measured, so a trend word is refused.
2. Missing data: a clause that mentions the theme of an indicator that is not available (and of
   no available one) may only say that the data is missing.

Arabic: one-letter prefixes (و، ف، ب، ل، ك), the article and common suffixes are accepted
around each word; short vowels and tatweel are ignored.
"""

import re
import unicodedata
from dataclasses import dataclass
from functools import lru_cache
from itertools import pairwise
from pathlib import Path
from typing import Literal

from pydantic import Field

from app.config_loader.territory import StrictModel, Text
from app.config_loader.validation import load_model
from app.services.reports.facts import FactSheet
from app.services.reports.numbers import PLACEHOLDER, Issue

Lang = Literal["fr", "ar"]


class Words(StrictModel):
    fr: list[str] = Field(default_factory=list)
    ar: list[str] = Field(default_factory=list)

    def get(self, lang: Lang) -> list[str]:
        return self.fr if lang == "fr" else self.ar


class TrendWords(StrictModel):
    up: Words
    down: Words
    stable: Words


class TrendIndicator(StrictModel):
    stable_band: float = Field(ge=0)
    # Level indicators whose evolution this one measures (population → its growth rate).
    covers: list[str] = Field(default_factory=list)


class TrendControl(StrictModel):
    window: int = Field(default=100, ge=10, le=400)
    words: TrendWords
    neutral_phrases: Words = Field(default_factory=Words)
    indicators: dict[str, TrendIndicator] = Field(default_factory=dict)


class MissingControl(StrictModel):
    strong_markers: Words
    weak_markers: Words
    data_nouns: Words
    clause_breaks: Words = Field(default_factory=Words)


class Controls(StrictModel):
    controls_version: Text
    status: Text
    trend: TrendControl
    missing: MissingControl
    subjective: Words = Field(default_factory=Words)
    topics: dict[str, Words] = Field(default_factory=dict)


def load_controls(path: Path) -> Controls:
    return load_model(
        path,
        Controls,
        {"window": "window: 100", "stable_band": "DEM_TCAM: { stable_band: 0.1 }"},
    )


@lru_cache(maxsize=4)
def cached_controls(path: Path) -> Controls:
    return load_controls(path)


# ------------------------------------------------------------------ text matching

_AR_LETTER = "ء-ي"
_AR_MARKS = re.compile("[ً-ْـ]")  # short vowels, shadda, sukun, tatweel


def normalize(text: str, lang: Lang) -> str:
    """Lower case (French), no short vowels (Arabic): normalize texts and words alike."""
    text = unicodedata.normalize("NFC", text).replace("’", "'")
    if lang == "ar":
        return _AR_MARKS.sub("", text)
    # Lower case, but fact references keep their form ({{F012}}).
    return re.sub(r"\{\{\s*f(\d{3})\s*\}\}", r"{{F\1}}", text.casefold())


def word_pattern(word: str, lang: Lang) -> re.Pattern[str]:
    w = re.escape(normalize(word, lang).strip())
    if lang == "ar":
        return re.compile(
            rf"(?<![{_AR_LETTER}])[وفبلك]?(?:ال)?{w}(?:ه|ها|ة|ت|ا|ات|ان|ين)?(?![{_AR_LETTER}])"
        )
    # French: start of word, any ending (« augment » covers augmente, augmentation…).
    return re.compile(rf"(?<!\w){w}")


def _find(words: list[str], text: str, lang: Lang) -> list[tuple[int, int, str]]:
    hits = []
    for word in words:
        for match in word_pattern(word, lang).finditer(text):
            hits.append((match.start(), match.end(), word))
    return hits


def _mask(text: str, start: int, end: int) -> str:
    return text[:start] + " " * (end - start) + text[end:]


def _any(words: list[str], text: str, lang: Lang) -> bool:
    return any(word_pattern(w, lang).search(text) for w in words)


SENTENCE = re.compile(r"(?<=[.!?؟;؛])\s+|\n+")


@dataclass
class Mention:
    start: int
    codes: frozenset[str]
    token: str
    via: Literal["ref", "label", "keyword"]


def mentions(
    text: str, sheet: FactSheet, controls: Controls, lang: Lang
) -> tuple[list[Mention], str]:
    """Indicator mentions in a normalized text, and the text with labels masked."""
    found: list[Mention] = []
    for match in PLACEHOLDER.finditer(text):
        fact = sheet.get(match.group(1))
        if fact is not None and fact.indicator:
            found.append(Mention(match.start(), frozenset({fact.indicator}), match.group(0), "ref"))
        text = _mask(text, match.start(), match.end())
    # Longest labels first, so that a long label is not split by a shorter one inside it.
    briefs = sorted(sheet.briefs.values(), key=lambda b: -len(b.label[lang]))
    for brief in briefs:
        label = normalize(brief.label[lang], lang)
        start = text.find(label)
        while start != -1:
            found.append(Mention(start, frozenset({brief.code}), brief.label[lang], "label"))
            text = _mask(text, start, start + len(label))
            start = text.find(label, start + len(label))
    owners: dict[str, set[str]] = {}
    for code, words in controls.topics.items():
        for word in words.get(lang):
            owners.setdefault(normalize(word, lang), set()).add(code)
    for word, all_codes in sorted(owners.items(), key=lambda item: -len(item[0])):
        codes = all_codes & sheet.briefs.keys()  # indicators absent from this sheet do not count
        if not codes:
            continue
        for match in word_pattern(word, lang).finditer(text):
            found.append(Mention(match.start(), frozenset(codes), word, "keyword"))
            text = _mask(text, match.start(), match.end())
    return found, text


# ------------------------------------------------------------------ 1. trends


def _direction(value: float, band: float) -> set[str]:
    allowed = set()
    if abs(value) <= band:
        allowed.add("stable")
    if value > 0:
        allowed.add("up")
    if value < 0:
        allowed.add("down")
    return allowed or {"stable"}


WORDING = {"up": "en hausse", "down": "en baisse", "stable": "stable"}


def check_trends(text: str, sheet: FactSheet, controls: Controls, lang: Lang) -> list[Issue]:
    issues: list[Issue] = []
    trend = controls.trend
    for sentence in SENTENCE.split(normalize(text, lang)):
        found, masked = mentions(sentence, sheet, controls, lang)
        for phrase in trend.neutral_phrases.get(lang):
            for start, end, _ in _find([phrase], masked, lang):
                masked = _mask(masked, start, end)
        for kind in ("up", "down", "stable"):
            for start, _, word in _find(getattr(trend.words, kind).get(lang), masked, lang):
                near = [m for m in found if abs(m.start - start) <= trend.window]
                if not near:
                    continue
                mention = min(near, key=lambda m: abs(m.start - start))
                measured = sorted(
                    code
                    for code, rule in trend.indicators.items()
                    if code in mention.codes or mention.codes & set(rule.covers)
                )
                if measured:
                    brief = sheet.briefs.get(measured[0])
                    if brief is None or brief.value is None:
                        continue  # missing data: the other check speaks
                    allowed = _direction(brief.value, trend.indicators[measured[0]].stable_band)
                    if kind not in allowed:
                        actual = " ou ".join(WORDING[a] for a in sorted(allowed))
                        issues.append(
                            Issue(
                                "trend",
                                f"« {word} » est faux pour « {brief.label['fr']} » : la valeur "
                                f"calculée est {actual}",
                            )
                        )
                else:
                    codes = sorted(mention.codes)
                    label = (
                        sheet.briefs[codes[0]].label["fr"] if codes[0] in sheet.briefs else codes[0]
                    )
                    issues.append(
                        Issue(
                            "trend",
                            f"« {word} » : aucune évolution n'est mesurée pour « {label} » "
                            "(une seule date) ; n'emploie pas de mot de tendance",
                        )
                    )
    return issues


# ------------------------------------------------------------------ 2. missing data

MISSING_STATUSES = {"not_available", "not_evaluable"}


def missing_codes(sheet: FactSheet) -> set[str]:
    return {
        b.code for b in sheet.briefs.values() if not b.available or b.status in MISSING_STATUSES
    }


def says_missing(clause: str, controls: Controls, lang: Lang) -> bool:
    rules = controls.missing
    if _any(rules.strong_markers.get(lang), clause, lang):
        return True
    return _any(rules.weak_markers.get(lang), clause, lang) and _any(
        rules.data_nouns.get(lang), clause, lang
    )


def _clauses(sentence: str, controls: Controls, lang: Lang) -> list[str]:
    breaks = controls.missing.clause_breaks.get(lang)
    if not breaks:
        return [sentence]
    cuts = sorted({start for start, _, _ in _find(breaks, sentence, lang)})
    bounds = [0, *cuts, len(sentence)]
    return [sentence[a:b] for a, b in pairwise(bounds) if sentence[a:b].strip()]


def check_missing(text: str, sheet: FactSheet, controls: Controls, lang: Lang) -> list[Issue]:
    missing = missing_codes(sheet)
    if not missing:
        return []
    issues: list[Issue] = []
    for sentence in SENTENCE.split(normalize(text, lang)):
        for clause in _clauses(sentence, controls, lang):
            found, _ = mentions(clause, sheet, controls, lang)
            about_missing = [m for m in found if m.codes and m.codes <= missing]
            if about_missing and not says_missing(clause, controls, lang):
                mention = about_missing[0]
                code = sorted(mention.codes)[0]
                label = sheet.briefs[code].label["fr"] if code in sheet.briefs else code
                issues.append(
                    Issue(
                        "missing",
                        f"« {label} » est non disponible : n'affirme rien sur « {mention.token} », "
                        "écris seulement que la donnée manque et qu'elle est à demander",
                    )
                )
    return issues


# ------------------------------------------------------------------ Arabic: numbers side by side

_NUMERIC = r"(?:\{\{F\d{3}\}\}|(?<![\w])\d{4}(?![\w]))"
ADJACENT = re.compile(rf"{_NUMERIC}\s+{_NUMERIC}")


def check_adjacent(text: str, lang: Lang) -> list[Issue]:
    """In Arabic, two numbers side by side (« في سنة 2024 168 391 ») are unreadable."""
    if lang != "ar":
        return []
    return [
        Issue(
            "adjacent",
            f"deux nombres collés : « {m.group(0)} » ; place le fait après le verbe, par exemple "
            "« يبلغ عدد السكان {{F001}} سنة 2024 » et non « في سنة 2024 {{F001}} »",
        )
        for m in ADJACENT.finditer(text)
    ]


# ------------------------------------------------------------------ 3. statuses

STATUS_SENTENCE = re.compile(r"(?<=[.!?؟])\s+|\n+")


def check_statuses(text: str, sheet: FactSheet, controls: Controls, lang: Lang) -> list[Issue]:
    """A computed status (« à surveiller », « déficit marqué »…) named in a sentence must be the
    status of the indicator it qualifies (nearest mention)."""
    labels = {
        status: normalize(label[lang], lang)
        for status, label in sheet.status_labels.items()
        if status in ("deficit_marked", "watch", "ok")
    }
    if not labels:
        return []
    issues: list[Issue] = []
    for sentence in STATUS_SENTENCE.split(normalize(text, lang)):
        found, masked = mentions(sentence, sheet, controls, lang)
        for status, label in labels.items():
            start = masked.find(label)
            while start != -1:
                near = [m for m in found if abs(m.start - start) <= controls.trend.window * 2]
                if near:
                    mention = min(near, key=lambda m: abs(m.start - start))
                    briefs = [sheet.briefs[c] for c in sorted(mention.codes) if c in sheet.briefs]
                    if briefs and all(b.status != status for b in briefs):
                        brief = briefs[0]
                        issues.append(
                            Issue(
                                "status",
                                f"« {brief.label['fr']} » a le statut « {brief.status_label['fr']} », "
                                f"pas « {label} »",
                            )
                        )
                start = masked.find(label, start + len(label))
    return issues


def check_subjective(text: str, controls: Controls, lang: Lang) -> list[Issue]:
    return [
        Issue(
            "subjective",
            f"jugement subjectif « {word} » : qualifie seulement avec le statut calculé et "
            "l'écart à la moyenne",
        )
        for _, _, word in _find(controls.subjective.get(lang), normalize(text, lang), lang)
    ]


def check_meaning(text: str, sheet: FactSheet, controls: Controls, lang: Lang) -> list[Issue]:
    return (
        check_trends(text, sheet, controls, lang)
        + check_missing(text, sheet, controls, lang)
        + check_statuses(text, sheet, controls, lang)
        + check_subjective(text, controls, lang)
        + check_adjacent(text, lang)
    )
