"""Indicator engine: computes the diagnostic of a territory from the declarative grid.

Rules that belong to the method (indicators, thresholds, reference) come from the YAML
files; this module only applies them. A missing value is never replaced by zero: it is
« non disponible » with the reason, and feeds the data-needs module.
"""

import time
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.config_loader import load_territories
from app.config_loader.facility_mapping import FacilityMapping, load_facility_mapping
from app.config_loader.indicators import (
    AreaPerCapitaFormula,
    BuiltUpFormula,
    CagrFormula,
    ChangeFormula,
    Confidence,
    ConsumptionFormula,
    DensityFormula,
    Direction,
    DistanceFormula,
    Evaluation,
    IndicatorDefinition,
    IndicatorGrid,
    Operand,
    ProximityFormula,
    RatioFormula,
    RawFormula,
    load_confidence,
    load_evaluation,
    load_grid,
    method_fingerprint,
)
from app.config_loader.territory import QualityFlag, TerritoryConfig
from app.models import Diagnostic, IndicatorDefinitionRow, IndicatorValue, StudyArea, Territory
from app.services.indicators import spatial
from app.settings import get_settings

BADGE_ORDER = ["official", "open", "estimated", "fictitious"]


class MissingInput(Exception):
    """Raised when an input of a formula is not available for a unit."""

    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


@dataclass(frozen=True)
class Datum:
    value: float
    year: int | None
    badge: str
    method: str  # direct | derived | modeled
    source: str
    provisional: bool = False


@dataclass
class Computed:
    value: float
    inputs: list[Datum]
    method: str
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class Unit:
    id: int
    name_fr: str
    name_ar: str | None
    level: str
    area_km2: float | None
    official_code: str | None
    scopes: list[str]
    flag: QualityFlag | None


# ---------------------------------------------------------------- configuration


@dataclass
class Method:
    grid: IndicatorGrid
    evaluation: Evaluation
    confidence: Confidence
    mapping: FacilityMapping | None
    fingerprint: str


def method_paths(config: TerritoryConfig) -> list[Path]:
    root = get_settings().config_dir
    paths = [
        root / "indicators" / "grille-v0.yaml",
        root / "indicators" / "evaluation.yaml",
        root / "confidence.yaml",
        root / "territories" / f"{config.code}.yaml",
    ]
    facilities = config.sources.get("facilities")
    mapping = facilities.model_dump().get("mapping") if facilities else None
    if mapping:
        paths.append(root.parent / mapping)
    return paths


def load_method(config: TerritoryConfig) -> Method:
    root = get_settings().config_dir
    paths = method_paths(config)
    mapping = load_facility_mapping(paths[4]) if len(paths) > 4 else None
    return Method(
        grid=load_grid(root / "indicators" / "grille-v0.yaml"),
        evaluation=load_evaluation(root / "indicators" / "evaluation.yaml"),
        confidence=load_confidence(root / "confidence.yaml"),
        mapping=mapping,
        fingerprint=method_fingerprint(*paths),
    )


# ---------------------------------------------------------------- engine


class Engine:
    def __init__(self, session: Session, config: TerritoryConfig, method: Method) -> None:
        self.session = session
        self.config = config
        self.method = method
        area = session.scalars(select(StudyArea).where(StudyArea.code == config.code)).one_or_none()
        if area is None:
            raise MissingInput(f"Les données de « {config.name.fr} » ne sont pas importées.")
        self.study_area = area
        flags = {f.official_code: f for f in config.quality_flags}
        self.units = [
            Unit(
                t.id,
                t.name_fr,
                t.name_ar,
                t.level,
                t.area_km2,
                t.official_code,
                list(t.scopes or []),
                flags.get(t.official_code or ""),
            )
            for t in session.scalars(
                select(Territory)
                .where(Territory.study_area_id == area.id, Territory.is_analysis_unit)
                .order_by(Territory.name_fr)
            )
        ]
        self.sources = {
            r[0]: {
                "name": r[1],
                "producer": r[2],
                "license": r[3],
                "badge": r[4],
                "data_date": r[5].isoformat() if r[5] else None,
                "retrieved_at": r[6].isoformat() if r[6] else None,
            }
            for r in session.execute(
                text(
                    "SELECT id, name, producer, license, default_badge, published_at, "
                    "retrieved_at FROM data_sources"
                )
            )
        }
        self.source_codes = {
            r[1]: r[0] for r in session.execute(text("SELECT id, code FROM data_sources"))
        }
        self.raw: dict[tuple[int, str, int], Datum] = {}
        for row in session.execute(
            text(
                "SELECT r.territory_id, r.code, r.year, r.value, r.badge, r.method, r.source_id "
                "FROM raw_variables r JOIN territories t ON t.id = r.territory_id "
                "WHERE t.study_area_id = :sa"
            ),
            {"sa": area.id},
        ):
            self.raw[(row[0], row[1], row[2])] = Datum(
                float(row[3]), row[2], row[4], row[5], self.sources[row[6]]["name"]
            )
        self.counts = spatial.facility_counts(session, area.id)
        self.category_totals: dict[str, int] = {}
        for (_, category), n in self.counts.items():
            self.category_totals[category] = self.category_totals.get(category, 0) + n
        self.cache: dict[str, Any] = {}
        facilities_source = self.sources.get(
            self.source_codes.get(f"osm_facilities:{config.code}", -1)
        )
        boundaries_source = self.sources.get(
            self.source_codes.get(f"osm_boundaries:{config.code}", -1)
        )
        self.facility_year = _year(facilities_source)
        self.boundary_source = boundaries_source["name"] if boundaries_source else "OpenStreetMap"
        self.facility_source = facilities_source["name"] if facilities_source else "OpenStreetMap"
        grid_source = self.sources.get(self.source_codes.get(f"ghsl_pop:{config.code}", -1))
        self.grid_source = grid_source["name"] if grid_source else "GHSL"

    # ------------------------------------------------------------ inputs

    def datum(self, unit: Unit, code: str, year: int | None) -> Datum:
        if year is not None:
            found = self.raw.get((unit.id, code, year))
        else:
            years = sorted(y for (tid, c, y) in self.raw if tid == unit.id and c == code)
            found = self.raw.get((unit.id, code, years[-1])) if years else None
        if found is None:
            label = f"{code} ({year})" if year else code
            raise MissingInput(f"Donnée d'entrée manquante : {label}.")
        return found

    def facility_datum(self, unit: Unit, categories: list[str]) -> Datum:
        self.require_facilities(categories)
        n = sum(self.counts.get((unit.id, c), 0) for c in categories)
        provisional = self.provisional_categories(categories)
        return Datum(
            float(n), self.facility_year, "open", "derived", self.facility_source, provisional
        )

    def area_datum(self, unit: Unit) -> Datum:
        if not unit.area_km2:
            raise MissingInput("Surface de l'unité inconnue.")
        return Datum(unit.area_km2, self.facility_year, "open", "derived", self.boundary_source)

    def grid_datum(self, value: float, categories: list[str]) -> Datum:
        return Datum(
            value,
            self.facility_year,
            "estimated",
            "modeled",
            f"{self.facility_source} + {self.grid_source}",
            self.provisional_categories(categories),
        )

    def provisional_categories(self, categories: list[str]) -> bool:
        return any(c in ("school", "health_primary", "health_hospital") for c in categories)

    def require_facilities(self, categories: list[str]) -> None:
        minimum = self.method.evaluation.facility_minimum
        total = sum(self.category_totals.get(c, 0) for c in categories)
        if total < minimum:
            labels = self.category_labels(categories)
            raise MissingInput(
                f"Recensement OpenStreetMap insuffisant : {total} équipement(s) « {labels} » "
                f"pour tout l'ensemble étudié (minimum fixé : {minimum})."
            )

    def category_labels(self, categories: list[str]) -> str:
        if not self.method.mapping:
            return ", ".join(categories)
        names = {c.code: c.label.fr for c in self.method.mapping.categories}
        return ", ".join(names.get(c, c) for c in categories)

    def operand(self, unit: Unit, operand: Operand) -> Datum:
        if operand.facilities is not None:
            return self.facility_datum(unit, operand.facilities)
        assert operand.input is not None
        return self.datum(unit, operand.input, operand.year)

    # ------------------------------------------------------------ formulas

    def compute(self, unit: Unit, indicator: IndicatorDefinition) -> Computed:
        f = indicator.formula
        if isinstance(f, RawFormula):
            d = self.datum(unit, f.input, f.year)
            return Computed(d.value, [d], d.method)
        if isinstance(f, DensityFormula):
            num, area = self.datum(unit, f.input, f.year), self.area_datum(unit)
            return Computed(num.value / area.value, [num, area], "derived")
        if isinstance(f, CagrFormula):
            a, b = self.datum(unit, f.input, f.from_year), self.datum(unit, f.input, f.to_year)
            if a.value <= 0:
                raise MissingInput("Valeur de départ nulle : taux non calculable.")
            rate = ((b.value / a.value) ** (1 / (f.to_year - f.from_year)) - 1) * 100
            return Computed(rate, [a, b], "derived")
        if isinstance(f, RatioFormula):
            num, den = self.operand(unit, f.numerator), self.operand(unit, f.denominator)
            if den.value <= 0:
                raise MissingInput("Dénominateur nul : ratio non calculable.")
            return Computed(num.value / den.value * f.per, [num, den], "derived")
        if isinstance(f, ProximityFormula):
            for need in f.all_of:
                self.require_facilities(need)
            key = f"prox:{f.all_of}:{f.distance_m}:{f.min_area_m2}"
            if key not in self.cache:
                self.cache[key] = spatial.proximity_share(
                    self.session, self.study_area.id, f.all_of, f.distance_m, f.min_area_m2
                )
            covered, total = self.cache[key].get(unit.id, (0.0, 0.0))
            if total <= 0:
                raise MissingInput("Population carroyée absente pour cette unité.")
            cats = [c for need in f.all_of for c in need]
            return Computed(covered / total * 100, [self.grid_datum(covered, cats)], "modeled")
        if isinstance(f, DistanceFormula):
            self.require_facilities(f.categories)
            key = f"dist:{f.categories}"
            if key not in self.cache:
                self.cache[key] = spatial.distance_mean(
                    self.session, self.study_area.id, f.categories
                )
            if unit.id not in self.cache[key]:
                raise MissingInput("Population carroyée absente pour cette unité.")
            value = self.cache[key][unit.id]
            return Computed(value, [self.grid_datum(value, f.categories)], "modeled")
        if isinstance(f, AreaPerCapitaFormula):
            self.require_facilities(f.categories)
            key = f"area:{f.categories}"
            if key not in self.cache:
                self.cache[key] = spatial.facility_area(
                    self.session, self.study_area.id, f.categories
                )
            pop = self.datum(unit, "population", f.year)
            area = Datum(
                self.cache[key].get(unit.id, 0.0),
                self.facility_year,
                "open",
                "derived",
                self.facility_source,
            )
            return Computed(area.value / pop.value, [area, pop], "derived")
        if isinstance(f, BuiltUpFormula):
            built = self.datum(unit, "built_up_km2", f.year)
            extra = {}
            if unit.area_km2:
                extra["share_of_area_pct"] = round(built.value / unit.area_km2 * 100, 1)
            return Computed(built.value, [built], "derived", extra)
        if isinstance(f, ChangeFormula):
            a, b = self.datum(unit, f.input, f.from_year), self.datum(unit, f.input, f.to_year)
            if a.value <= 0:
                raise MissingInput("Valeur de départ nulle : variation non calculable.")
            return Computed(
                (b.value / a.value - 1) * 100,
                [a, b],
                "derived",
                {"absolute": round(b.value - a.value, 3)},
            )
        if isinstance(f, ConsumptionFormula):
            b0 = self.datum(unit, "built_up_km2", f.from_year)
            b1 = self.datum(unit, "built_up_km2", f.to_year)
            p14, p24 = self.datum(unit, "population", 2014), self.datum(unit, "population", 2024)
            if p14.value <= 0:
                raise MissingInput("Population 2014 nulle.")
            growth = (p24.value / p14.value) ** (1 / 10)
            pop0 = p14.value * growth ** (f.from_year - 2014)
            pop1 = p14.value * growth ** (f.to_year - 2014)
            added = pop1 - pop0
            if added <= 0:
                raise MissingInput("Population stable ou en baisse : indicateur non évaluable.")
            value = (b1.value - b0.value) * 1e6 / added
            interpolated = Datum(
                added, f.to_year, "estimated", "modeled", "Interpolation MAJAL (HCP)"
            )
            return Computed(
                value,
                [b0, b1, p14, p24, interpolated],
                "modeled",
                {
                    "added_built_m2": round((b1.value - b0.value) * 1e6),
                    "added_population": round(added),
                },
            )
        raise MissingInput("Type de calcul non pris en charge.")

    # ------------------------------------------------------------ confidence

    def badge(self, inputs: list[Datum]) -> str:
        return max((d.badge for d in inputs), key=BADGE_ORDER.index)

    def reliability(self, inputs: list[Datum], method: str, provisional: bool) -> int:
        weights = self.method.confidence.reliability
        badge = self.badge(inputs)
        years = [d.year for d in inputs if d.year]
        age = datetime.now(UTC).year - min(years) if years else 99
        recency = next(step.points for step in weights.recency if age <= step.max_age)
        completeness = weights.completeness["provisional" if provisional else "complete"]
        method_key = method if method in weights.method else "derived"
        return int(weights.source[badge] + recency + completeness + weights.method[method_key])  # type: ignore[index]

    # ------------------------------------------------------------ diagnostic

    def run(self, author: str | None = None) -> Diagnostic:
        started = time.perf_counter()
        profile = self.config.profiles.indicators
        indicators = self.method.grid.for_profile(profile)
        default_scope = self.config.default_scope
        population = {u.id: self.raw.get((u.id, "population", 2024)) for u in self.units}
        results: dict[str, dict[int, dict[str, Any]]] = {}
        references: dict[str, Any] = {}

        for indicator in indicators:
            per_unit: dict[int, dict[str, Any]] = {}
            for unit in self.units:
                entry: dict[str, Any] = {"value": None, "status": "not_available", "rank": None}
                if unit.flag and unit.flag.boundary_unreliable and indicator.spatial:
                    entry.update(status="not_evaluable", reason=unit.flag.warning.fr)
                    per_unit[unit.id] = entry
                    continue
                try:
                    computed = self.compute(unit, indicator)
                except MissingInput as exc:
                    entry["reason"] = exc.reason
                    per_unit[unit.id] = entry
                    continue
                provisional = indicator.provisional or any(d.provisional for d in computed.inputs)
                years = [d.year for d in computed.inputs if d.year]
                entry.update(
                    value=computed.value,
                    year=max(years) if years else None,
                    badge=self.badge(computed.inputs),
                    method=computed.method,
                    reliability=self.reliability(computed.inputs, computed.method, provisional),
                    provisional=provisional,
                    sources=sorted({d.source for d in computed.inputs}),
                    extra=computed.extra,
                    status="context"
                    if indicator.direction == Direction.neutral
                    else "not_evaluable",
                )
                per_unit[unit.id] = entry

            reference = self.reference(indicator, per_unit, population, default_scope.code)
            references[indicator.code] = reference
            self.evaluate(indicator, per_unit, reference)
            self.rank(indicator, per_unit, default_scope.code)
            results[indicator.code] = per_unit

        duration = int((time.perf_counter() - started) * 1000)
        payload = self.payload(indicators, results, references, duration)
        diagnostic = Diagnostic(
            study_area_id=self.study_area.id,
            grid_version=self.method.grid.grid_version,
            method_hash=self.method.fingerprint,
            status="computed",
            author=author,
            duration_ms=duration,
            result=payload,
        )
        self.session.add(diagnostic)
        self.session.flush()
        self.session.execute(
            IndicatorValue.__table__.insert(),  # type: ignore[attr-defined]
            [
                {
                    "diagnostic_id": diagnostic.id,
                    "territory_id": unit_id,
                    "indicator_code": code,
                    "year": e.get("year"),
                    "value": e["value"],
                    "unit": next(i.unit.fr for i in indicators if i.code == code),
                    "badge": e.get("badge"),
                    "reliability": e.get("reliability"),
                    "method": e.get("method"),
                    "status": e["status"],
                    "rank": e.get("rank"),
                    "reference": references[code]["value"] if references[code] else None,
                    "ratio": e.get("ratio"),
                    "provisional": bool(e.get("provisional")),
                    "extra": e.get("extra") or {},
                }
                for code, per_unit in results.items()
                for unit_id, e in per_unit.items()
            ],
        )
        for indicator in self.method.grid.indicators:
            row = self.session.scalars(
                select(IndicatorDefinitionRow).where(
                    IndicatorDefinitionRow.grid_version == self.method.grid.grid_version,
                    IndicatorDefinitionRow.code == indicator.code,
                )
            ).one_or_none()
            if row is None:
                row = IndicatorDefinitionRow(
                    grid_version=self.method.grid.grid_version, code=indicator.code
                )
                self.session.add(row)
            row.definition = indicator.model_dump(mode="json")
        self.session.commit()
        return diagnostic

    def reference(
        self,
        indicator: IndicatorDefinition,
        per_unit: dict[int, dict[str, Any]],
        population: dict[int, Datum | None],
        scope: str,
    ) -> dict[str, Any] | None:
        if indicator.reference != "relative":
            return None
        if indicator.norm and indicator.norm.value is not None:
            return {"type": "norm", "value": indicator.norm.value, "source": indicator.norm.source}
        total = weight = 0.0
        for unit in self.units:
            entry = per_unit[unit.id]
            pop = population.get(unit.id)
            if entry["value"] is None or pop is None or scope not in unit.scopes:
                continue
            if unit.flag and unit.flag.exclude_from_ranking:
                continue
            total += entry["value"] * pop.value
            weight += pop.value
        if weight <= 0:
            return None
        return {"type": "relative", "value": total / weight, "units": "population_weighted_mean"}

    def evaluate(
        self,
        indicator: IndicatorDefinition,
        per_unit: dict[int, dict[str, Any]],
        reference: dict[str, Any] | None,
    ) -> None:
        if indicator.direction == Direction.neutral or reference is None:
            return
        thresholds = self.method.evaluation.thresholds
        ref = reference["value"]
        for entry in per_unit.values():
            value = entry["value"]
            if value is None:
                continue
            if reference["type"] == "norm":
                below = (
                    value < ref if indicator.direction == Direction.higher_better else value > ref
                )
                entry["status"] = "deficit_marked" if below else "ok"
                continue
            if ref == 0:
                entry["status"] = "not_evaluable"
                entry["reason"] = "Moyenne de référence nulle."
                continue
            ratio = value / ref
            entry["ratio"] = ratio
            entry["gap_pct"] = (ratio - 1) * 100
            if indicator.direction == Direction.higher_better:
                t = thresholds.higher_better
                entry["status"] = (
                    "deficit_marked"
                    if ratio < t.deficit_marked
                    else "watch"
                    if ratio < t.watch
                    else "ok"
                )
            else:
                t = thresholds.lower_better
                entry["status"] = (
                    "deficit_marked"
                    if ratio > t.deficit_marked
                    else "watch"
                    if ratio > t.watch
                    else "ok"
                )

    def rank(
        self, indicator: IndicatorDefinition, per_unit: dict[int, dict[str, Any]], scope: str
    ) -> None:
        candidates = [
            u
            for u in self.units
            if per_unit[u.id]["value"] is not None
            and scope in u.scopes
            and not (u.flag and u.flag.exclude_from_ranking)
        ]
        reverse = indicator.direction != Direction.lower_better
        key: Callable[[Unit], float] = lambda u: per_unit[u.id]["value"]  # noqa: E731
        for position, unit in enumerate(sorted(candidates, key=key, reverse=reverse), start=1):
            per_unit[unit.id]["rank"] = position
            per_unit[unit.id]["rank_of"] = len(candidates)
        for unit in self.units:
            if unit.flag and unit.flag.exclude_from_ranking:
                per_unit[unit.id]["excluded_from_ranking"] = True

    def payload(
        self,
        indicators: list[IndicatorDefinition],
        results: dict[str, dict[int, dict[str, Any]]],
        references: dict[str, Any],
        duration: int,
    ) -> dict[str, Any]:
        grid, evaluation = self.method.grid, self.method.evaluation
        scope = self.config.default_scope
        ref_label = scope.reference_label or scope.label
        label = {
            lang: getattr(evaluation.label, lang).replace("{reference}", getattr(ref_label, lang))
            for lang in ("fr", "ar")
        }
        return {
            "territory": self.config.code,
            "computed_at": datetime.now(UTC).isoformat(),
            "duration_ms": duration,
            "method_hash": self.method.fingerprint,
            "grid": {
                "version": grid.grid_version,
                "label": grid.display_label.model_dump(),
                "status": grid.status,
                "axes": [a.model_dump() for a in grid.axes],
            },
            "evaluation": {
                "label": label,
                "statuses": {k: v.model_dump() for k, v in evaluation.statuses.items()},
                "thresholds": evaluation.thresholds.model_dump(),
                "reference_scope": scope.code,
                "reference_label": ref_label.model_dump(),
                "facility_minimum": evaluation.facility_minimum,
            },
            "badges": {k: v.model_dump() for k, v in self.method.confidence.badges.items()},
            "indicators": [
                {
                    "code": i.code,
                    "axis": i.axis,
                    "label": i.label.model_dump(),
                    "unit": i.unit.model_dump(),
                    "direction": i.direction.value,
                    "decimals": i.decimals,
                    "reference": references[i.code],
                    "source_expected": i.source_expected,
                    "note": i.note,
                    "threshold_note": i.threshold_note,
                    "provisional": i.provisional,
                    "highlight": i.highlight,
                    "requested_from": i.requested_from,
                    "formula": i.formula.type,
                    "spatial": i.spatial,
                }
                for i in indicators
            ],
            "units": [
                {
                    "id": u.id,
                    "name_fr": u.name_fr,
                    "name_ar": u.name_ar,
                    "level": u.level,
                    "official_code": u.official_code,
                    "area_km2": u.area_km2,
                    "scopes": u.scopes,
                    "warning": u.flag.warning.model_dump() if u.flag else None,
                    "excluded_from_ranking": bool(u.flag and u.flag.exclude_from_ranking),
                    "values": {code: results[code][u.id] for code in results},
                }
                for u in self.units
            ],
        }


def _year(source: dict[str, Any] | None) -> int | None:
    if not source:
        return None
    date = source.get("data_date") or source.get("retrieved_at")
    return int(date[:4]) if date else None


def compute_diagnostic(session: Session, code: str, author: str | None = None) -> Diagnostic:
    territories = load_territories(get_settings().config_dir / "territories")
    if code not in territories:
        raise MissingInput(f"Territoire inconnu : {code}.")
    config = territories[code]
    return Engine(session, config, load_method(config)).run(author)
