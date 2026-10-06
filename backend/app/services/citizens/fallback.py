"""Analysis without AI (fallback, and point of comparison for the model): language from script
and marker words, themes from the taxonomy keywords, tonality from marker phrases.
Configuration: config/citizens/analyse.yaml and config/taxonomy/<profile>.yaml."""

import re
from functools import lru_cache
from pathlib import Path

from pydantic import Field

from app.config_loader.taxonomy import Taxonomy
from app.config_loader.territory import Localized, StrictModel
from app.config_loader.validation import load_model
from app.services.reports.meaning import Lang, normalize, word_pattern

AR = "ء-ي"
LATIN_AMAZIGH = re.compile("[ɣḥṭẓṣḍɛ]")
DARIJA_DIGITS = re.compile(r"(?<![\d])[a-z]*[379][a-z]+|[a-z]+[379][a-z]*(?![\d])", re.IGNORECASE)


class MarkerLists(StrictModel):
    darija_ar: list[str] = Field(default_factory=list)
    darija_latin: list[str] = Field(default_factory=list)
    amazigh_latin: list[str] = Field(default_factory=list)


class ToneWords(StrictModel):
    fr: list[str] = Field(default_factory=list)
    ar: list[str] = Field(default_factory=list)
    darija: list[str] = Field(default_factory=list)


class ReviewRules(StrictModel):
    keywords_silent_is_disagreement: bool = True
    uncertain_languages: list[str] = Field(default_factory=lambda: ["amazigh_latin", "other"])


class AnalysisConfig(StrictModel):
    languages: dict[str, Localized]
    markers: MarkerLists
    tonality_keywords: dict[str, ToneWords]
    glossary: dict[str, dict[str, str]] = Field(default_factory=dict)
    place_common_words: list[str] = Field(default_factory=list)
    place_cues: list[str] = Field(default_factory=list)
    review: ReviewRules = Field(default_factory=ReviewRules)


def load_analysis_config(path: Path) -> AnalysisConfig:
    return load_model(path, AnalysisConfig, {"markers": "markers:\n  darija_ar: [ديال]"})


@lru_cache(maxsize=2)
def cached_analysis_config(path: Path) -> AnalysisConfig:
    return load_analysis_config(path)


def _hits(words: list[str], text: str, arabic: bool) -> list[str]:
    lang: Lang = "ar" if arabic else "fr"
    source = normalize(text, lang)
    return [w for w in words if word_pattern(w, lang).search(source)]


def detect_language(text: str, config: AnalysisConfig) -> str:
    letters = re.findall(rf"[{AR}A-Za-zÀ-ÿɣḥṭẓṣḍɛ]", text)
    if not letters:
        return "other"
    arabic_share = sum(1 for c in letters if re.match(f"[{AR}]", c)) / len(letters)
    if arabic_share > 0.5:
        return "darija_ar" if len(_hits(config.markers.darija_ar, text, True)) >= 2 else "ar"
    words = re.findall(r"[\wɣḥṭẓṣḍɛ']+", text.casefold())
    if (
        LATIN_AMAZIGH.search(text)
        or len({w for w in words} & {m.casefold() for m in config.markers.amazigh_latin}) >= 3
    ):
        return "amazigh_latin"
    darija_words = {w for w in words} & {m.casefold() for m in config.markers.darija_latin}
    if len(DARIJA_DIGITS.findall(text)) >= 1 or len(darija_words) >= 3:
        return "darija_latin"
    return "fr"


def classify_themes(text: str, taxonomy: Taxonomy, limit: int = 2) -> list[str]:
    arabic = bool(re.search(f"[{AR}]", text))
    scores: dict[str, int] = {}
    for theme in taxonomy.themes:
        words = theme.keywords.ar if arabic else theme.keywords.fr + theme.keywords.darija
        found = _hits(words, text, arabic)
        if found:
            scores[theme.code] = len(found)
    ranked = sorted(scores, key=lambda code: -scores[code])
    return ranked[:limit] or ["autres"]


def keyword_tonality(text: str, config: AnalysisConfig) -> str | None:
    """Tonality given by marker phrases (longest match wins), or None when none is found."""
    arabic = bool(re.search(f"[{AR}]", text))
    best, best_length = None, 0
    for tonality, words in config.tonality_keywords.items():
        candidates = words.ar if arabic else words.fr + words.darija
        for word in _hits(candidates, text, arabic):
            if len(word) > best_length:
                best, best_length = tonality, len(word)
    return best


def classify_tonality(text: str, config: AnalysisConfig) -> str:
    return keyword_tonality(text, config) or "plainte"
