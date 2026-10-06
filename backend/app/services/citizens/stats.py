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
    if getattr(contribution, "validated_by", None):
        return True
    keywords = (contribution.analysis or {}).get("keywords", {})
    return bool(contribution.language) and contribution.language == keywords.get("language")


def theme_sure(contribution: Contribution) -> bool:
    if getattr(contribution, "validated_by", None):
        return True  # checked by a person
    keywords = (contribution.analysis or {}).get("keywords", {})
    return bool(contribution.themes) and contribution.themes[0] in (keywords.get("themes") or [])


def filtered(
    contributions: list[Contribution],
    theme: str | None = None,
    unit: int | None = None,
    language: str | None = None,
    tonality: str | None = None,
    secondary: bool = False,
    group_of: dict[int, int] | None = None,
) -> list[Contribution]:
    out = []
    for c in contributions:
        if theme and theme not in themes_of(c, secondary):
            continue
        located = c.territory_id
        if group_of is not None and located is not None:
            located = group_of.get(located, located)
        if unit is not None and located != unit:
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
    group_of: dict[int, int] | None = None,
) -> dict[str, Any]:
    """`units` are the rows to describe (analysis units, or communes when `group_of` maps each
    unit to its commune)."""
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
            key = group_of.get(c.territory_id, c.territory_id) if group_of else c.territory_id
            by_unit.setdefault(key, []).append(c)
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
                "members": info.get("members", [unit_id]),
            }
        )
    unit_rows.sort(key=lambda row: -row["count"])
    return {
        "total": total,
        "located": sum(1 for c in contributions if c.territory_id is not None),
        "analysed_by_ai": sum(1 for c in contributions if (c.analysis or {}).get("mode") == "ai"),
        "validated": sum(1 for c in contributions if getattr(c, "validated_by", None)),
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
        "validated_by": getattr(c, "validated_by", None),
        "validation_note": {
            "fr": f"Validé par {c.validated_by}",
            "ar": f"تم التحقق من طرف {c.validated_by}",
        }
        if getattr(c, "validated_by", None)
        else None,
    }


UNFAVOURABLE = {"deficit_marked", "watch"}
SEVERITY = {"deficit_marked": "marked", "watch": "watch"}


def crossing(
    contributions: list[Contribution],
    taxonomy: Taxonomy,
    unit_values: dict[str, dict[str, Any]],
    indicators: dict[str, dict[str, Any]],
    statuses: dict[str, dict[str, str]],
    secondary: bool = False,
    members: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """« Ce que disent les citoyens / ce que montrent les données » for ONE unit.

    Main theme only unless `secondary`. No conclusion below `min_contributions`; a « strong »
    demand is a share of the unit's contributions above `strong_share` (used internally; shown as
    a count below `percent_min_total`). Themes without indicator: data to ask for, and who holds it.
    """
    rules = taxonomy.crossing
    total = len(contributions)
    counts: Counter[str] = Counter(t for c in contributions for t in themes_of(c, secondary))
    rows: list[dict[str, Any]] = []
    for theme in taxonomy.themes:
        if theme.code == "autres":
            continue
        count = counts.get(theme.code, 0)
        linked = []
        for code in theme.indicators:
            meta = indicators.get(code) or {}
            if members and len(members) > 1:
                linked.append(aggregate_indicator(code, meta, members, statuses, rules))
                continue
            entry = unit_values.get(code) or {}
            status = entry.get("status")
            linked.append(
                {
                    "code": code,
                    "label": meta.get("label"),
                    "value": entry.get("value"),
                    "unit": meta.get("unit"),
                    "decimals": meta.get("decimals", 1),
                    "status": status,
                    "status_label": statuses.get(status) if status else None,
                    "unfavourable": status in UNFAVOURABLE,
                    "severity": SEVERITY.get(status) if status else None,
                }
            )
        unfavourable = any(item["unfavourable"] for item in linked)
        # The label repeats the real status: « déficit marqué » only for that status.
        severity = (
            ("marked" if any(item.get("severity") == "marked" for item in linked) else "watch")
            if unfavourable
            else None
        )
        if not theme.indicators:
            if count == 0:
                continue
            verdict = "no_indicator" if theme.data_request else "no_indicator_planned"
        elif count < rules.min_contributions:
            if count == 0 and not unfavourable:
                continue
            if count == 0 and unfavourable:
                # No demand can only be stated on a large enough base (owner rule, 30).
                verdict = "data_only" if total >= rules.absence_min_total else "absence_unknown"
            else:
                verdict = "too_few"
        else:
            strong = count / total >= rules.strong_share if total else False
            if strong and unfavourable:
                verdict = "convergence"
            elif strong:
                verdict = "demand_only"
            elif unfavourable:
                verdict = "moderate_deficit"  # some demand (not « strong ») and a deficit
            else:
                verdict = "moderate"
        key = (
            f"{verdict}_{severity}"
            if severity and f"{verdict}_{severity}" in rules.labels
            else verdict
        )
        rows.append(
            {
                "theme": theme.code,
                "label": theme.label.model_dump(),
                "count": count,
                "share": share(count, total, rules.percent_min_total),
                "indicators": linked,
                "verdict": verdict,
                "severity": severity,
                "verdict_label": rules.labels[key].model_dump() if key in rules.labels else None,
                "data_request": theme.data_request.model_dump() if theme.data_request else None,
            }
        )
    order = {
        "convergence": 0,
        "moderate_deficit": 1,
        "demand_only": 2,
        "data_only": 3,
        "moderate": 4,
        "absence_unknown": 5,
        "too_few": 5,
        "no_indicator": 6,
        "no_indicator_planned": 7,
    }
    rows.sort(key=lambda r: (order[str(r["verdict"])], -int(r["count"])))
    return {
        "total": total,
        "validated": sum(1 for c in contributions if getattr(c, "validated_by", None)),
        "secondary_included": secondary,
        "secondary_note": SECONDARY_NOTE if secondary else None,
        "rows": rows,
        "rules": {
            "min_contributions": rules.min_contributions,
            "percent_min_total": rules.percent_min_total,
            "strong_share": rules.strong_share,
            "absence_min_total": rules.absence_min_total,
        },
    }


def aggregate_indicator(
    code: str,
    meta: dict[str, Any],
    members: list[dict[str, Any]],
    statuses: dict[str, dict[str, str]],
    rules: Any,
) -> dict[str, Any]:
    """Commune scale: no aggregated value is computed. The indicator is unfavourable for the
    commune if the units in « déficit marqué » or « à surveiller » gather at least
    `aggregate_unfavourable_share` of its population."""
    # Only units where the indicator is known count; « non disponible » is never « favourable ».
    known = [m for m in members if (m["values"].get(code) or {}).get("value") is not None]
    total_pop = sum(m.get("population") or 0 for m in known)
    bad = [m for m in known if (m["values"].get(code) or {}).get("status") in UNFAVOURABLE]
    bad_pop = sum(m.get("population") or 0 for m in bad)
    pop_share = bad_pop / total_pop if total_pop else None
    marked_pop = sum(
        m.get("population") or 0
        for m in bad
        if (m["values"].get(code) or {}).get("status") == "deficit_marked"
    )
    unfavourable = pop_share is not None and pop_share >= rules.aggregate_unfavourable_share
    # « Déficit marqué » for the commune only if the units in that status alone reach the share.
    marked = bool(total_pop) and marked_pop / total_pop >= rules.aggregate_unfavourable_share
    return {
        "code": code,
        "label": meta.get("label"),
        "value": None,
        "unit": meta.get("unit"),
        "decimals": meta.get("decimals", 1),
        "status": None,
        "status_label": None,
        "aggregate": {
            "unfavourable_units": [
                {"name_fr": m["name_fr"], "name_ar": m.get("name_ar")} for m in bad
            ],
            "units": len(known),
            "missing_units": len(members) - len(known),
            "population_share": round(pop_share, 4) if pop_share is not None else None,
        },
        "unfavourable": unfavourable,
        "severity": ("marked" if marked else "watch") if unfavourable else None,
    }
