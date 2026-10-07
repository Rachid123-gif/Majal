"""Completeness of the grid for a territory and what each institution's data would allow
(stage 5.2-5.3). Pure functions: the diagnostic and the configuration in, plain data out.

- Status of an indicator for the territory, from the badges of the diagnostic values: the least
  reliable badge present wins; « missing » when no unit has a value (never 0).
- Three effects of a data request on an indicator, computed from its current status
  (config/data_holders/regles.yaml, `effects`):
  « calculer » (missing today), « fiabiliser » (open or estimated today), « affiner » (already
  official, available at a finer scale).
- For each institution: its indicators by effect, the citizen themes it would document, and a
  sentence built from these counts — never written by the language model.
- The payload carries what the screen's simulator needs (« Si nous obtenons les données de… »):
  every request with its holders, its dependencies and its effects.
"""

from typing import Any

from app.config_loader.data_holders import DataHolders, DataRequest, Institution, ModuleRules
from app.config_loader.indicators import IndicatorGrid
from app.config_loader.taxonomy import Taxonomy
from app.services.data_needs.priority import priority, ranked

BADGE_TO_STATUS = {"official": "official", "open": "open", "estimated": "estimated"}
STATUS_ORDER = ["official", "open", "estimated", "missing"]
EFFECTS = ("computed", "reliable", "finer")


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


def effects_of(request: DataRequest, statuses: dict[str, dict[str, Any]]) -> dict[str, list[str]]:
    """Indicators of this territory's grid profile, by effect. An indicator « enabled » but
    already available is not counted as computed; an indicator « improved » but still missing
    is left out (the data alone would not make it computable)."""

    def status(code: str) -> str | None:
        return statuses.get(code, {}).get("status")

    computed = [c for c in request.enables if status(c) == "missing"]
    reliable = [c for c in request.improves if status(c) in ("open", "estimated")]
    finer = [c for c in request.improves if status(c) == "official"]
    return {"computed": computed, "reliable": reliable, "finer": finer}


def _plural(n: int, word: str) -> str:
    return word if n == 1 else f"{word}s"


def sentence(
    institution: Institution,
    effects: dict[str, list[str]],
    jointly_with: list[Institution],
    finer_scale: dict[str, str] | None,
    themes: list[str],
    context: bool,
    rules: ModuleRules,
) -> dict[str, str]:
    """« Avec les données du HCP, MAJAL pourrait calculer 1 indicateur supplémentaire (avec les
    données de l'AREF), fiabiliser 1 indicateur et affiner 9 indicateurs à l'échelle du
    quartier. »"""
    of = institution.with_data_of or institution.name
    verbs = {k: v.verb for k, v in rules.effects.items()}
    fr: list[str] = []
    ar: list[str] = []
    n = len(effects["computed"])
    if n:
        text = (
            f"{verbs['computed'].fr} {n} {_plural(n, 'indicateur')} {_plural(n, 'supplémentaire')}"
        )
        text_ar = f"{verbs['computed'].ar} مؤشرات إضافية ({n})"
        if jointly_with:
            text += (
                " (avec les données "
                + " et ".join((i.with_data_of or i.name).fr for i in jointly_with)
                + ")"
            )
            text_ar += (
                " (مع معطيات "
                + " و".join((i.with_data_of or i.name).ar for i in jointly_with)
                + ")"
            )
        fr.append(text)
        ar.append(text_ar)
    n = len(effects["reliable"])
    if n:
        fr.append(f"{verbs['reliable'].fr} {n} {_plural(n, 'indicateur')}")
        ar.append(f"{verbs['reliable'].ar} مؤشرات ({n})")
    n = len(effects["finer"])
    if n:
        scale = f" à l'échelle {finer_scale['fr']}" if finer_scale else ""
        scale_ar = f" على مستوى {finer_scale['ar']}" if finer_scale else ""
        fr.append(f"{verbs['finer'].fr} {n} {_plural(n, 'indicateur')}{scale}")
        ar.append(f"{verbs['finer'].ar} مؤشرات ({n}){scale_ar}")
    if themes:
        n = len(themes)
        fr.append(f"documenter {n} {_plural(n, 'thème')} de l'écoute citoyenne")
        ar.append(f"توثيق مواضيع من الإنصات للمواطنين ({n})")
    if context:
        fr.append("situer les projets programmés par rapport aux déficits mesurés")
        ar.append("موقعة المشاريع المبرمجة بالنسبة لأوجه الخصاص المقيسة")
    if not fr:
        return {"fr": "", "ar": ""}
    joined = fr[0] if len(fr) == 1 else ", ".join(fr[:-1]) + " et " + fr[-1]
    return {
        "fr": f"Avec les données {of.fr}, MAJAL pourrait {joined}.",
        "ar": f"بفضل معطيات {of.ar}، يمكن لمجال: {'، '.join(ar)}.",
    }


def request_row(
    request: DataRequest, rules: ModuleRules, statuses: dict[str, dict[str, Any]]
) -> dict[str, Any]:
    level = priority(request, rules)
    effects = effects_of(request, statuses)
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
        "effects": effects,
        "finer_scale": request.finer_scale.model_dump() if request.finer_scale else None,
        "themes": request.themes,
        "requires_also": request.requires_also,
        "context": request.context,
        "boundaries": request.boundaries,
    }


def _institution_row(
    institution: Institution,
    holders: DataHolders,
    rows: dict[str, dict[str, Any]],
    rules: ModuleRules,
) -> dict[str, Any]:
    by_request = {r.code: r for r in holders.requests}
    own = [rows[r.code] for r in holders.requests if institution.code in r.holders]
    effects: dict[str, list[str]] = {
        k: sorted({c for row in own for c in row["effects"][k]}) for k in EFFECTS
    }
    effects["reliable"] = [c for c in effects["reliable"] if c not in effects["computed"]]
    effects["finer"] = [
        c for c in effects["finer"] if c not in effects["computed"] + effects["reliable"]
    ]
    partners = {
        h
        for row in own
        if row["effects"]["computed"]
        for other in row["requires_also"]
        for h in by_request[other].holders
        if h != institution.code
    }
    jointly = [i for i in holders.institutions if i.code in partners]
    scales = [row["finer_scale"] for row in own if row["effects"]["finer"] and row["finer_scale"]]
    themes = sorted({t for row in own for t in row["themes"]})
    context = any(row["context"] for row in own)
    levels = [row["priority"] for row in own]
    best = min(levels, key=list(rules.priorities).index) if levels else None
    return {
        "code": institution.code,
        "name": institution.name.model_dump(),
        "kind": institution.kind,
        "to_verify": institution.to_verify,
        "priority": best,
        "priority_label": rules.priorities[best].model_dump() if best else None,
        "requests": [row["code"] for row in own],
        "effects": effects,
        "computed_with": [i.code for i in jointly],
        "themes": themes,
        "sentence": sentence(
            institution,
            effects,
            jointly,
            scales[0] if scales else None,
            themes,
            context,
            rules,
        ),
    }


def compute(
    diagnostic: dict[str, Any],
    grid: IndicatorGrid,
    holders: DataHolders,
    rules: ModuleRules,
    taxonomy: Taxonomy | None = None,
) -> dict[str, Any]:
    statuses = indicator_statuses(diagnostic)
    requests = [request_row(r, rules, statuses) for r in ranked(holders, rules)]
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
                "indicators": [s["code"] for s in items],
            }
        )

    institutions = [_institution_row(i, holders, rows, rules) for i in holders.institutions]
    order = list(rules.priorities)
    institutions.sort(
        key=lambda i: (
            order.index(i["priority"]) if i["priority"] else len(order),
            -sum(len(v) for v in i["effects"].values()),
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
        "effects": {
            k: {"verb": v.verb.model_dump(), "label": v.label.model_dump()}
            for k, v in rules.effects.items()
        },
        "indicators": list(statuses.values()),
        "axes": axes,
        "requests": requests,
        "institutions": institutions,
        "themes": theme_labels,
    }
