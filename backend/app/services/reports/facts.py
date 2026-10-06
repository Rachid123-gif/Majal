"""Fact sheet: every number of a report, identified (F001…), formatted and sourced.

The language model only sees fact identifiers and qualitative descriptors (status, trend);
it never receives nor writes numbers. The renderer substitutes the formatted values.
"""

from dataclasses import dataclass, field
from typing import Any

NBSP = " "  # narrow no-break space: French thousands separator


def format_number(value: float, decimals: int) -> str:
    """French rules (also used in Arabic texts, with Western digits as in Moroccan usage)."""
    text = f"{value:,.{decimals}f}"
    return text.replace(",", "\u0001").replace(".", ",").replace("\u0001", NBSP)


@dataclass
class Fact:
    id: str
    kind: str  # value | reference | rank | gap | area
    indicator: str | None
    label: dict[str, str]
    text: dict[str, str]  # rendered text substituted for {{Fxxx}}
    source: str | None = None
    year: int | None = None
    badge: str | None = None


@dataclass
class IndicatorBrief:
    """What the model may know about one indicator: no number, only words and fact ids."""

    code: str
    label: dict[str, str]
    available: bool
    status: str
    status_label: dict[str, str]
    descriptor: dict[str, str]
    fact_ids: dict[str, str]  # kind -> fact id
    reason: str | None = None
    requested_from: str | None = None
    value: float | None = None  # never shown to the model: used by the trend check


@dataclass
class FactSheet:
    unit: dict[str, Any]
    identity: dict[str, str]
    facts: list[Fact] = field(default_factory=list)
    briefs: dict[str, IndicatorBrief] = field(default_factory=dict)
    years: set[int] = field(default_factory=set)
    attention: list[str] = field(default_factory=list)
    reference_label: dict[str, str] = field(default_factory=dict)
    grid_label: dict[str, str] = field(default_factory=dict)
    evaluation_label: dict[str, str] = field(default_factory=dict)
    status_labels: dict[str, dict[str, str]] = field(default_factory=dict)
    # Section 7: {"total_fact", "themes": [(label, fact id)], "total", "fictitious", "too_few"}
    citizens: dict[str, Any] | None = None

    def get(self, fact_id: str) -> Fact | None:
        return next((f for f in self.facts if f.id == fact_id), None)

    def to_json(self) -> dict[str, Any]:
        return {
            "unit": self.unit,
            "facts": [f.__dict__ for f in self.facts],
            "years": sorted(self.years),
            "attention": self.attention,
        }


RANK_SUFFIX = {"fr": lambda r: "er" if r == 1 else "e"}


def _rank_text(rank: int, of: int, neutral: bool) -> dict[str, str]:
    fr = f"{rank}{'er' if rank == 1 else 'e'}"
    if neutral:
        return {
            "fr": f"{fr} valeur la plus élevée sur {of}",
            "ar": f"{rank} من حيث القيمة الأعلى من أصل {of}",
        }
    # No « الرتبة » here: the models already write the word before the reference.
    return {"fr": f"{fr} sur {of}", "ar": f"{rank} من أصل {of}"}


def _gap_text(gap: float, reference: dict[str, str]) -> dict[str, str]:
    magnitude = format_number(abs(gap), 0)
    if gap >= 0:
        return {
            "fr": f"{magnitude} % au-dessus de la moyenne {reference['fr']}",
            "ar": f"أعلى بنسبة {magnitude} % من متوسط {reference['ar']}",
        }
    return {
        "fr": f"{magnitude} % au-dessous de la moyenne {reference['fr']}",
        "ar": f"أقل بنسبة {magnitude} % من متوسط {reference['ar']}",
    }


def _descriptor(meta: dict[str, Any], entry: dict[str, Any]) -> dict[str, str]:
    """Words, not numbers: trend for growth indicators, position for evaluated ones."""
    value = entry.get("value")
    if value is None:
        return {"fr": "", "ar": ""}
    if meta["formula"] in ("cagr", "change"):
        return (
            {"fr": "en hausse", "ar": "في ارتفاع"}
            if value > 0
            else {"fr": "en baisse", "ar": "في انخفاض"}
        )
    gap = entry.get("gap_pct")
    if gap is None:
        return {"fr": "", "ar": ""}
    if abs(gap) < 5:
        return {"fr": "proche de la moyenne", "ar": "قريب من المتوسط"}
    return (
        {"fr": "supérieur à la moyenne", "ar": "أعلى من المتوسط"}
        if gap > 0
        else {"fr": "inférieur à la moyenne", "ar": "أقل من المتوسط"}
    )


def build_fact_sheet(
    diagnostic: dict[str, Any], unit_id: int, identity: dict[str, str]
) -> FactSheet:
    unit = next(u for u in diagnostic["units"] if u["id"] == unit_id)
    statuses = diagnostic["evaluation"]["statuses"]
    reference = diagnostic["evaluation"]["reference_label"]
    sheet = FactSheet(
        unit={
            k: unit[k] for k in ("id", "name_fr", "name_ar", "level", "official_code", "area_km2")
        },
        identity=identity,
        reference_label=reference,
        grid_label=diagnostic["grid"]["label"],
        evaluation_label=diagnostic["evaluation"]["label"],
        status_labels=statuses,
    )
    counter = 0

    def new(
        kind: str, code: str | None, label: dict[str, str], text: dict[str, str], **extra: Any
    ) -> str:
        nonlocal counter
        counter += 1
        fact_id = f"F{counter:03d}"
        sheet.facts.append(Fact(fact_id, kind, code, label, text, **extra))
        return fact_id

    if unit.get("area_km2"):
        area = format_number(unit["area_km2"], 1)
        sheet.identity["area_fact"] = new(
            "area",
            None,
            {"fr": "Surface", "ar": "المساحة"},
            {"fr": f"{area} km²", "ar": f"{area} كلم²"},
            source="Calcul MAJAL à partir des limites OpenStreetMap",
            badge="estimated",
        )

    for meta in diagnostic["indicators"]:
        entry = unit["values"].get(meta["code"])
        if entry is None:
            continue
        ids: dict[str, str] = {}
        value = entry.get("value")
        source = "; ".join(entry.get("sources") or []) or meta["source_expected"]
        if value is not None:
            number = format_number(value, meta["decimals"])
            ids["value"] = new(
                "value",
                meta["code"],
                meta["label"],
                {
                    "fr": f"{number} {meta['unit']['fr']}".strip(),
                    "ar": f"{number} {meta['unit']['ar']}".strip(),
                },
                source=source,
                year=entry.get("year"),
                badge=entry.get("badge"),
            )
            if entry.get("year"):
                sheet.years.add(int(entry["year"]))
            ref = meta.get("reference")
            if ref and ref.get("value") is not None:
                ref_number = format_number(ref["value"], meta["decimals"])
                ids["reference"] = new(
                    "reference",
                    meta["code"],
                    {"fr": f"Moyenne {reference['fr']}", "ar": f"متوسط {reference['ar']}"},
                    # Self-describing, so that a model cannot present it as the unit's value.
                    {
                        "fr": f"{ref_number} {meta['unit']['fr']}".strip()
                        + f" (moyenne {reference['fr']})",
                        "ar": f"{ref_number} {meta['unit']['ar']}".strip()
                        + f" (متوسط {reference['ar']})",
                    },
                    source="Calcul MAJAL (moyenne pondérée par la population)",
                )
            if entry.get("rank") and entry.get("rank_of"):
                ids["rank"] = new(
                    "rank",
                    meta["code"],
                    {"fr": "Rang", "ar": "الرتبة"},
                    _rank_text(entry["rank"], entry["rank_of"], meta["direction"] == "neutral"),
                )
            if entry.get("gap_pct") is not None:
                ids["gap"] = new(
                    "gap",
                    meta["code"],
                    {"fr": "Écart à la moyenne", "ar": "الفارق عن المتوسط"},
                    _gap_text(entry["gap_pct"], reference),
                )
        sheet.briefs[meta["code"]] = IndicatorBrief(
            code=meta["code"],
            label=meta["label"],
            available=value is not None,
            status=entry["status"],
            status_label=statuses[entry["status"]],
            descriptor=_descriptor(meta, entry),
            fact_ids=ids,
            reason=entry.get("reason"),
            requested_from=meta.get("requested_from"),
            value=value,
        )

    # Attention points: deterministic, most marked deficits first (same rule as the UI).
    marked = []
    for meta in diagnostic["indicators"]:
        entry = unit["values"].get(meta["code"])
        if entry and entry["status"] in ("deficit_marked", "watch") and entry.get("ratio"):
            severity = (
                entry["ratio"] - 1 if meta["direction"] == "lower_better" else 1 - entry["ratio"]
            )
            marked.append((severity, meta["code"]))
    sheet.attention = [code for _, code in sorted(marked, reverse=True)[:5]]
    for year in (2014, 2024, 2015, 2020):
        sheet.years.add(year) if any(
            str(year) in m["label"]["fr"] for m in diagnostic["indicators"]
        ) else None
    return sheet


def add_citizen_facts(sheet: FactSheet, citizens: dict[str, Any] | None) -> None:
    """Counts of citizen contributions (main theme only) become facts like any other number."""
    if citizens is None:
        return
    badge = "fictitious" if citizens["fictitious"] else "official"
    source = (
        "Contributions citoyennes fictives (jeu de démonstration MAJAL)"
        if citizens["fictitious"]
        else "Contributions citoyennes importées"
    )

    def new(label: dict[str, str], count: int) -> str:
        fact_id = f"F{len(sheet.facts) + 1:03d}"
        sheet.facts.append(
            Fact(
                fact_id,
                "citizens",
                None,
                label,
                {"fr": f"{count} contribution{'s' if count > 1 else ''}", "ar": f"{count} مساهمة"},
                source=source,
                badge=badge,
            )
        )
        return fact_id

    sheet.citizens = {
        "total": citizens["total"],
        "fictitious": citizens["fictitious"],
        "too_few": citizens["too_few"],
        "total_fact": new(
            {"fr": "Contributions localisées", "ar": "المساهمات المحددة"}, citizens["total"]
        )
        if citizens["total"]
        else None,
        "themes": [(t["label"], new(t["label"], t["count"])) for t in citizens["themes"]],
    }
