"""Completeness of the grid for a territory and what each institution's data would allow
(stage 5.2). Pure functions: the diagnostic and the configuration in, plain data out.

- Status of an indicator for the territory, from the badges of the diagnostic values: the least
  reliable badge present wins; « missing » when no unit has a value (never 0).
- Completeness by axis of the grid: counts by status (« Santé : 1 indicateur sur 4 disponible »).
- For each institution: the indicators its data would make computable (only those missing
  today), those it would improve, the citizen themes it would give a measure to, and a sentence
  built from these counts — never written by the language model.
"""

from typing import Any

from app.config_loader.data_holders import DataHolders, DataRequest, Institution, ModuleRules
from app.config_loader.indicators import IndicatorGrid
from app.config_loader.taxonomy import Taxonomy
from app.services.data_needs.priority import priority, ranked

BADGE_TO_STATUS = {"official": "official", "open": "open", "estimated": "estimated"}
STATUS_ORDER = ["official", "open", "estimated", "missing"]


def indicator_statuses(diagnostic: dict[str, Any]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    units = diagnostic["units"]
    for indicator in diagnostic["indicators"]:
        code = indicator["code"]
        values = [u["values"].get(code) or {} for u in units]
        known = [v for v in values if v.get("value") is not None]
        statuses = [BADGE_TO_STATUS.get(v.get("badge") or "", "estimated") for v in known]
        status = max(statuses, key=STATUS_ORDER.index) if statuses else "missing"
        out[code] = {
            "code": code,
            "axis": indicator["axis"],
            "label": indicator["label"],
            "status": status,
            "units": len(values),
            "missing_units": len(values) - len(known),
        }
    return out


def _plural(n: int, word: str) -> str:
    return word if n == 1 else f"{word}s"


def sentence(
    institution: Institution,
    computable: list[str],
    jointly_with: list[Institution],
    improved: list[str],
    themes: list[str],
    context: bool,
) -> dict[str, str]:
    """« Avec les données de la Direction régionale de la Santé, MAJAL pourrait calculer
    3 indicateurs supplémentaires et en améliorer 1. »"""
    of = institution.with_data_of or institution.name
    parts_fr: list[str] = []
    parts_ar: list[str] = []
    if computable:
        n = len(computable)
        text = f"calculer {n} {_plural(n, 'indicateur')} {_plural(n, 'supplémentaire')}"
        text_ar = f"حساب مؤشرات إضافية ({n})"
        if jointly_with:
            names = " et ".join((i.with_data_of or i.name).fr for i in jointly_with)
            names_ar = " و".join((i.with_data_of or i.name).ar for i in jointly_with)
            text += f" (avec les données {names})"
            text_ar += f" (مع معطيات {names_ar})"
        parts_fr.append(text)
        parts_ar.append(text_ar)
    if improved:
        n = len(improved)
        parts_fr.append(
            f"en améliorer {n}"
            if computable
            else f"améliorer {n} {_plural(n, 'indicateur')} déjà {_plural(n, 'calculé')}"
        )
        parts_ar.append(f"تحسين مؤشرات محسوبة ({n})")
    if themes:
        n = len(themes)
        parts_fr.append(f"documenter {n} {_plural(n, 'thème')} de l'écoute citoyenne")
        parts_ar.append(f"توثيق مواضيع من الإنصات للمواطنين ({n})")
    if context:
        parts_fr.append("situer les projets programmés par rapport aux déficits mesurés")
        parts_ar.append("موقعة المشاريع المبرمجة بالنسبة لأوجه الخصاص المقيسة")
    if not parts_fr:
        return {"fr": "", "ar": ""}
    joined = parts_fr[0] if len(parts_fr) == 1 else ", ".join(parts_fr[:-1]) + " et " + parts_fr[-1]
    return {
        "fr": f"Avec les données {of.fr}, MAJAL pourrait {joined}.",
        "ar": f"بفضل معطيات {of.ar}، يمكن لمجال: {'، '.join(parts_ar)}.",
    }


def request_row(
    request: DataRequest,
    rules: ModuleRules,
    statuses: dict[str, dict[str, Any]],
    holders: DataHolders,
) -> dict[str, Any]:
    level = priority(request, rules)
    in_profile = set(statuses)
    return {
        "code": request.code,
        "priority": level,
        "priority_label": rules.priorities[level].model_dump(),
        "holders": request.holders,
        "alternatives": request.alternatives,
        "complementary": request.complementary,
        "data": request.data.model_dump(),
        "detail": request.detail.model_dump(),
        "format": request.format.model_dump(),
        "frequency": request.frequency.model_dump(),
        "value": request.value.model_dump(),
        # Only indicators of this territory's grid profile; « computable » only if missing today.
        "enables": [c for c in request.enables if statuses.get(c, {}).get("status") == "missing"],
        "improves": [c for c in request.improves if c in in_profile],
        "themes": request.themes,
        "requires_also": request.requires_also,
        "context": request.context,
        "boundaries": request.boundaries,
    }


def compute(
    diagnostic: dict[str, Any],
    grid: IndicatorGrid,
    holders: DataHolders,
    rules: ModuleRules,
    taxonomy: Taxonomy | None = None,
) -> dict[str, Any]:
    statuses = indicator_statuses(diagnostic)
    by_request = {r.code: r for r in holders.requests}
    requests = [request_row(r, rules, statuses, holders) for r in ranked(holders, rules)]
    rows = {row["code"]: row for row in requests}

    axes = []
    for axis in grid.axes:
        items = [s for s in statuses.values() if s["axis"] == axis.code]
        if not items:
            continue
        counts = {k: sum(1 for s in items if s["status"] == k) for k in STATUS_ORDER}
        axes.append(
            {
                "code": axis.code,
                "label": axis.label.model_dump(),
                "total": len(items),
                "available": len(items) - counts["missing"],
                "counts": counts,
            }
        )

    institutions: list[dict[str, Any]] = []
    for institution in holders.institutions:
        own = [rows[r.code] for r in holders.requests if institution.code in r.holders]
        computable = sorted({c for row in own for c in row["enables"]})
        partners = {
            h
            for row in own
            if row["enables"]
            for other in row["requires_also"]
            for h in by_request[other].holders
            if h != institution.code
        }
        jointly = [i for i in holders.institutions if i.code in partners]
        improved = sorted({c for row in own for c in row["improves"]} - set(computable))
        themes = sorted({t for row in own for t in row["themes"]})
        context = any(row["context"] for row in own)
        levels = [row["priority"] for row in own]
        best = min(levels, key=list(rules.priorities).index) if levels else None
        institutions.append(
            {
                "code": institution.code,
                "name": institution.name.model_dump(),
                "kind": institution.kind,
                "to_verify": institution.to_verify,
                "priority": best,
                "priority_label": rules.priorities[best].model_dump() if best else None,
                "requests": [row["code"] for row in own],
                "computable": computable,
                "computable_with": [i.code for i in jointly],
                "improved": improved,
                "themes": themes,
                "sentence": sentence(institution, computable, jointly, improved, themes, context),
            }
        )
    order = list(rules.priorities)
    institutions.sort(
        key=lambda i: (
            order.index(i["priority"]) if i["priority"] else len(order),
            -(len(i["computable"]) + len(i["improved"])),
            -len(i["themes"]),
            i["code"],
        )
    )
    theme_labels = (
        {t.code: t.label.model_dump() for t in taxonomy.themes} if taxonomy is not None else {}
    )
    total = len(statuses)
    missing = sum(1 for s in statuses.values() if s["status"] == "missing")
    return {
        "label": holders.display_label.model_dump(),
        "to_verify_label": holders.to_verify_label.model_dump(),
        "rules_status": rules.status,
        "summary": {"total": total, "available": total - missing, "missing": missing},
        "statuses": {k: v.model_dump() for k, v in rules.indicator_statuses.items()},
        "indicators": list(statuses.values()),
        "axes": axes,
        "requests": requests,
        "institutions": institutions,
        "themes": theme_labels,
    }
