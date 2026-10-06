"""Analysis of one ANONYMISED contribution by the local model: language, French translation,
themes (taxonomy codes only), tonality, place cited, and any person name left by the rules.

The model's answer is checked: unknown theme codes are dropped (the keyword fallback takes over
if none is left), the tonality and language must be in their lists, and the place is only a
candidate: it is attached to a unit by the gazetteer, never by the model.
"""

import time
from dataclasses import dataclass, field
from typing import Any

from app.config_loader.taxonomy import Taxonomy
from app.services.citizens.fallback import (
    AnalysisConfig,
    _hits,
    classify_themes,
    classify_tonality,
    detect_language,
)
from app.services.llm.base import LLMError, LLMProvider

SYSTEM = (
    "Tu analyses une contribution d'habitant recueillie lors d'une concertation territoriale au "
    "Maroc. Le texte est déjà anonymisé ([NOM], [TÉLÉPHONE]…). Il peut être en français, en arabe "
    "standard, en darija (alphabet arabe ou latin, avec des chiffres comme 3, 7, 9) ou en "
    "amazighe transcrit en lettres latines.\n"
    "Réponds uniquement en JSON avec :\n"
    "- language : la langue du texte (une des valeurs proposées) ;\n"
    "- translation_fr : la traduction fidèle en français (le texte lui-même s'il est en français),"
    " sans rien ajouter ni résumer, en gardant les marques [NOM], [TÉLÉPHONE]… ; les noms de "
    "lieux (quartiers, rues, places, communes) ne se traduisent pas : écris-les en lettres "
    "latines tels qu'ils se prononcent, sans les traduire ;\n"
    "- themes : le code du thème PRINCIPAL de la liste, puis un second code SEULEMENT si ce "
    "second sujet est explicitement évoqué dans le texte (au plus deux codes ; ne déduis "
    "jamais un thème qui n'est pas écrit) ;\n"
    "- tonality : demande, plainte, proposition ou satisfaction ;\n"
    "- place : le lieu cité (quartier, rue, place, commune) tel qu'il est écrit, ou null ;\n"
    "- place_fr : ce lieu en lettres latines tel qu'il s'écrit en français, ou null ;\n"
    "- remaining_names : les prénoms ou noms de PERSONNES encore présents, sinon une liste vide.\n"
    "Thèmes possibles :\n{themes}\n"
    "Glossaire (darija, amazighe) :\n{glossary}"
)
HINT = "Langue repérée automatiquement (indicative) : {language}.\n\nTexte :\n{text}"
# Languages that the marker words recognise more reliably than the model (benchmark, stage 4).
TRUST_MARKERS = {"darija_ar", "darija_latin", "amazigh_latin"}


def schema(taxonomy: Taxonomy, languages: list[str]) -> dict[str, Any]:
    codes = [t.code for t in taxonomy.themes]
    return {
        "type": "object",
        "properties": {
            "language": {"type": "string", "enum": languages},
            "translation_fr": {"type": "string"},
            "themes": {
                "type": "array",
                "items": {"type": "string", "enum": codes},
                "minItems": 1,
                "maxItems": 2,
            },
            "tonality": {"type": "string", "enum": list(taxonomy.tonalities)},
            "place": {"type": ["string", "null"]},
            "place_fr": {"type": ["string", "null"]},
            "remaining_names": {"type": "array", "items": {"type": "string"}},
        },
        "required": [
            "language",
            "translation_fr",
            "themes",
            "tonality",
            "place",
            "place_fr",
            "remaining_names",
        ],
    }


@dataclass
class Analysis:
    language: str
    translation_fr: str | None
    themes: list[str]
    tonality: str
    place: str | None
    place_fr: str | None
    names: list[str] = field(default_factory=list)
    mode: str = "ai"  # ai | keywords
    model: str | None = None
    duration_s: float = 0.0
    error: str | None = None
    keywords: dict[str, Any] = field(default_factory=dict)  # fallback result, for comparison


def explicit_themes(
    themes: list[str], text: str, translation: Any, taxonomy: Taxonomy
) -> list[str]:
    """Rule of method: a second theme is kept only if it is explicitly evoked, that is if one of
    its keywords appears in the text or in its French translation."""
    if len(themes) < 2:
        return themes
    second = taxonomy.theme(themes[1])
    if second is None:
        return themes[:1]
    found = _hits(second.keywords.ar, text, True) or _hits(
        second.keywords.fr + second.keywords.darija, text, False
    )
    if not found and isinstance(translation, str):
        found = _hits(second.keywords.fr, translation, False)
    return themes if found else themes[:1]


def keywords_only(text: str, taxonomy: Taxonomy, config: AnalysisConfig) -> dict[str, Any]:
    return {
        "language": detect_language(text, config),
        "themes": classify_themes(text, taxonomy),
        "tonality": classify_tonality(text, config),
    }


def analyze(
    text: str,
    taxonomy: Taxonomy,
    config: AnalysisConfig,
    provider: LLMProvider | None,
) -> Analysis:
    baseline = keywords_only(text, taxonomy, config)
    fallback = Analysis(
        language=baseline["language"],
        translation_fr=text if baseline["language"] == "fr" else None,
        themes=baseline["themes"],
        tonality=baseline["tonality"],
        place=None,
        place_fr=None,
        mode="keywords",
        keywords=baseline,
    )
    if provider is None:
        fallback.error = "IA désactivée"
        return fallback
    themes_list = "\n".join(f"- {t.code} : {t.label.fr} — {t.description}" for t in taxonomy.themes)
    glossary = "\n".join(
        f"- {word} : {meaning}"
        for group in config.glossary.values()
        for word, meaning in group.items()
    )
    hint_language = config.languages.get(baseline["language"])
    prompt = HINT.format(language=hint_language.fr if hint_language else "?", text=text)
    started = time.perf_counter()
    try:
        result = provider.generate_json(
            SYSTEM.format(themes=themes_list, glossary=glossary),
            prompt,
            schema(taxonomy, list(config.languages)),
            temperature=0,
        )
    except LLMError as exc:
        fallback.error = str(exc)
        return fallback
    data = result.data or {}
    codes = {t.code for t in taxonomy.themes}
    themes = [t for t in data.get("themes") or [] if t in codes]
    themes = list(dict.fromkeys(themes))[:2]  # main theme, then an explicit second one
    if not themes:
        fallback.error = "Réponse sans thème valide"
        return fallback
    themes = explicit_themes(themes, text, data.get("translation_fr"), taxonomy)
    language = data.get("language") if data.get("language") in config.languages else None
    if baseline["language"] in TRUST_MARKERS or language in (None, "other"):
        language = baseline["language"]
    tonality = data.get("tonality") if data.get("tonality") in taxonomy.tonalities else None
    translation = data.get("translation_fr")
    return Analysis(
        language=language or baseline["language"],
        translation_fr=translation
        if isinstance(translation, str) and translation.strip()
        else None,
        themes=themes,
        tonality=tonality or baseline["tonality"],
        place=data.get("place") if isinstance(data.get("place"), str) else None,
        place_fr=data.get("place_fr") if isinstance(data.get("place_fr"), str) else None,
        names=[n for n in data.get("remaining_names") or [] if isinstance(n, str)],
        mode="ai",
        model=getattr(provider, "model", None),
        duration_s=round(time.perf_counter() - started, 2),
        keywords=baseline,
    )
