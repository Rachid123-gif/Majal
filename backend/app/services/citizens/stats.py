"""Statistics of the citizen dashboard (stage 4.4).

Rules from the project owner:
- the main statistics count only the MAIN theme of each contribution; secondary themes are
  added only on request, with a note of lower reliability;
- below `percent_min_total` contributions, a unit is described with counts, never percentages;
- verbatims: contributions whose detected language and main theme are « sure » first (the
  model and the keyword fallback agree), always with the original next to the translation;
- every contribution set marked fictitious carries the permanent banner.
"""

from collections import Counter
from typing import Any

from app.config_loader.taxonomy import Taxonomy
from app.models import Contribution

FICTITIOUS_BANNER = {
    "fr": "Contributions fictives — illustration du fonctionnement de l'outil. Elles ne reflètent pas l'opinion réelle des habitants.",
    "ar": "مساهمات افتراضية — لتوضيح طريقة اشتغال الأداة. لا تعكس الرأي الحقيقي للسكان.",
}
SECONDARY_NOTE = {
    "fr": "Thèmes secondaires inclus : moins fiables que le thème principal (une contribution peut alors compter deux fois).",
    "ar": "تشمل المواضيع الثانوية: أقل موثوقية من الموضوع الرئيسي (قد تُحتسب المساهمة مرتين).",
}
TRANSLATION_NOTE = {"fr": "Traduction automatique", "ar": "ترجمة آلية"}
AMAZIGH_NOTE = {
    "fr": "Transcription approximative, à relire par un locuteur",
    "ar": "نسخ تقريبي، يتعين أن يراجعه متحدث",
}


def themes_of(contribution: Contribution, secondary: bool) -> list[str]:
    themes = list(contribution.themes or [])
    return themes if secondary else themes[:1]


def language_sure(contribution: Contribution) -> bool:
    keywords = (contribution.analysis or {}).get("keywords", {})
    return bool(contribution.language) and contribution.language == keywords.get("language")


def theme_sure(contribution: Contribution) -> bool:
    keywords = (contribution.analysis or {}).get("keywords", {})
    return bool(contribution.themes) and contribution.themes[0] in (keywords.get("themes") or [])


def filtered(
    contributions: list[Contribution],
    theme: str | None = None,
    unit: int | None = None,
    language: str | None = None,
    tonality: str | None = None,
    secondary: bool = False,
) -> list[Contribution]:
    out = []
    for c in contributions:
        if theme and theme not in themes_of(c, secondary):
            continue
        if unit is not None and c.territory_id != unit:
            continue
        if language and c.language != language:
            continue
        if tonality and c.tonality != tonality:
            continue
        out.append(c)
    return out


def share(count: int, total: int, minimum: int) -> float | None:
    """A percentage only when the base is large enough (counts otherwise)."""
    return round(count / total, 4) if total >= minimum and total else None


def summary(
    contributions: list[Contribution],
    taxonomy: Taxonomy,
    units: dict[int, dict[str, Any]],
    secondary: bool = False,
) -> dict[str, Any]:
    rules = taxonomy.crossing
    total = len(contributions)
    theme_counts: Counter[str] = Counter(t for c in contributions for t in themes_of(c, secondary))
    themes: list[dict[str, Any]] = [
        {
            "code": t.code,
            "label": t.label.model_dump(),
            "count": theme_counts.get(t.code, 0),
            "share": share(theme_counts.get(t.code, 0), total, rules.percent_min_total),
        }
        for t in taxonomy.themes
        if theme_counts.get(t.code)
    ]
    themes.sort(key=lambda row: -int(row["count"]))
    by_unit: dict[int, list[Contribution]] = {}
    for c in contributions:
        if c.territory_id is not None:
            by_unit.setdefault(c.territory_id, []).append(c)
    unit_rows = []
    for unit_id, info in units.items():
        items = by_unit.get(unit_id, [])
        top = Counter(t for c in items for t in themes_of(c, False)).most_common(1)
        population = info.get("population")
        unit_rows.append(
            {
                "id": unit_id,
                "name_fr": info["name_fr"],
                "name_ar": info.get("name_ar"),
                "count": len(items),
                "per_10k": round(len(items) / population * 10000, 2) if population else None,
                "main_theme": top[0][0] if top and len(items) >= rules.min_contributions else None,
                "describe_with_counts": len(items) < rules.percent_min_total,
            }
        )
    unit_rows.sort(key=lambda row: -row["count"])
    return {
        "total": total,
        "located": sum(1 for c in contributions if c.territory_id is not None),
        "analysed_by_ai": sum(1 for c in contributions if (c.analysis or {}).get("mode") == "ai"),
        "secondary_included": secondary,
        "secondary_note": SECONDARY_NOTE if secondary else None,
        "themes": themes,
        "units": unit_rows,
        "languages": Counter(c.language or "other" for c in contributions).most_common(),
        "tonalities": Counter(c.tonality or "plainte" for c in contributions).most_common(),
        "rules": {
            "min_contributions": rules.min_contributions,
            "percent_min_total": rules.percent_min_total,
        },
    }


def verbatims(
    contributions: list[Contribution],
    theme: str,
    units: dict[int, dict[str, Any]],
    limit: int = 3,
) -> list[dict[str, Any]]:
    """Up to `limit` contributions whose MAIN theme is `theme`, sure ones first, varied units."""
    candidates = [c for c in contributions if c.themes and c.themes[0] == theme]
    candidates.sort(key=lambda c: (-(language_sure(c) + theme_sure(c)), c.external_id))
    chosen: list[Contribution] = []
    seen_units: set[int | None] = set()
    for c in candidates:  # first pass: different units
        if c.territory_id not in seen_units or c.territory_id is None:
            chosen.append(c)
            seen_units.add(c.territory_id)
        if len(chosen) == limit:
            break
    for c in candidates:
        if len(chosen) == limit:
            break
        if c not in chosen:
            chosen.append(c)
    return [verbatim(c, units) for c in chosen]


def verbatim(c: Contribution, units: dict[int, dict[str, Any]]) -> dict[str, Any]:
    unit = units.get(c.territory_id) if c.territory_id is not None else None
    return {
        "id": c.external_id,
        "original": c.anonymized_text,  # anonymised: the raw text is never shown
        "translation_fr": c.translation_fr if c.language != "fr" else None,
        "translation_note": TRANSLATION_NOTE if c.language != "fr" else None,
        "language": c.language,
        "language_note": AMAZIGH_NOTE if c.language == "amazigh_latin" else None,
        "themes": c.themes,
        "tonality": c.tonality,
        "place": c.place_text,
        "unit": {"id": c.territory_id, "name_fr": unit["name_fr"], "name_ar": unit.get("name_ar")}
        if unit
        else None,
        "sure": {"language": language_sure(c), "theme": theme_sure(c)},
        "badge": c.badge,
    }
