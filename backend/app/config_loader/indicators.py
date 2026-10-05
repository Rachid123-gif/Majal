"""Schemas of the indicator grid, the evaluation rule and the confidence settings.

Everything here is method, owned by the scientific referent: the code only interprets it.
"""

import hashlib
from enum import StrEnum
from pathlib import Path
from typing import Annotated, Literal, Self

from pydantic import Field, model_validator

from app.config_loader.territory import Localized, Slug, StrictModel, Text
from app.config_loader.validation import load_model


class Direction(StrEnum):
    higher_better = "higher_better"
    lower_better = "lower_better"
    neutral = "neutral"


class Operand(StrictModel):
    """Either a census/raw variable (`input`) or a count of facilities (`facilities`)."""

    input: Slug | None = None
    year: int | None = None
    facilities: list[Slug] | None = None

    @model_validator(mode="after")
    def one_kind(self) -> Self:
        if (self.input is None) == (self.facilities is None):
            raise ValueError("Indiquez soit « input », soit « facilities » (un seul des deux).")
        return self


class RawFormula(StrictModel):
    type: Literal["raw"]
    input: Slug
    year: int | None = None


class DensityFormula(StrictModel):
    type: Literal["density"]
    input: Slug
    year: int | None = None


class CagrFormula(StrictModel):
    type: Literal["cagr"]
    input: Slug
    from_year: int
    to_year: int


class RatioFormula(StrictModel):
    type: Literal["ratio"]
    numerator: Operand
    denominator: Operand
    per: float = Field(default=1, gt=0)


class ProximityFormula(StrictModel):
    type: Literal["proximity_share"]
    # Each inner list is one need, satisfied by any of its categories; all needs are required.
    all_of: list[list[Slug]] = Field(min_length=1)
    distance_m: float = Field(gt=0, le=50000)
    min_area_m2: float | None = Field(default=None, ge=0)


class DistanceFormula(StrictModel):
    type: Literal["distance_mean"]
    categories: list[Slug] = Field(min_length=1)


class AreaPerCapitaFormula(StrictModel):
    type: Literal["area_per_capita"]
    categories: list[Slug] = Field(min_length=1)
    year: int | None = None


class BuiltUpFormula(StrictModel):
    type: Literal["built_up"]
    year: int


class ChangeFormula(StrictModel):
    type: Literal["change"]
    input: Slug
    from_year: int
    to_year: int


class ConsumptionFormula(StrictModel):
    type: Literal["consumption"]
    from_year: int
    to_year: int


Formula = Annotated[
    RawFormula
    | DensityFormula
    | CagrFormula
    | RatioFormula
    | ProximityFormula
    | DistanceFormula
    | AreaPerCapitaFormula
    | BuiltUpFormula
    | ChangeFormula
    | ConsumptionFormula,
    Field(discriminator="type"),
]

# Values that depend on the unit's boundary (area, cells inside it, built-up surface).
SPATIAL_FORMULAS = {
    "density",
    "proximity_share",
    "distance_mean",
    "area_per_capita",
    "built_up",
    "consumption",
}
SPATIAL_INPUTS = {"built_up_km2"}


class Norm(StrictModel):
    value: float | None = None
    source: Text


class UnitLabel(StrictModel):
    """Units may be symbols (%, km²) in both languages: no Arabic-letter check here."""

    fr: Text
    ar: Text


class Axis(StrictModel):
    code: Slug
    number: int = Field(ge=1)
    label: Localized


class IndicatorDefinition(StrictModel):
    code: Annotated[str, Field(pattern=r"^[A-Z][A-Z0-9_]*$")]
    axis: Slug
    label: Localized
    unit: UnitLabel
    profiles: list[Slug] = Field(min_length=1)
    direction: Direction
    formula: Formula
    decimals: int = Field(default=1, ge=0, le=4)
    source_expected: Text
    reference: Literal["none", "relative"] = "none"
    norm: Norm | None = None
    note: Text | None = None
    threshold_note: Text | None = None
    provisional: bool = False
    highlight: bool = False
    requested_from: Text | None = None
    enabled: bool = True
    status: Text

    @model_validator(mode="after")
    def consistent(self) -> Self:
        if self.reference == "relative" and self.direction == Direction.neutral:
            raise ValueError(
                "Un indicateur « neutral » ne peut pas être évalué : mettez « reference: none »."
            )
        if self.norm and self.norm.value is not None and self.direction == Direction.neutral:
            raise ValueError("Une norme n'a de sens que si « direction » n'est pas « neutral ».")
        return self

    @property
    def spatial(self) -> bool:
        if self.formula.type in SPATIAL_FORMULAS:
            return True
        return getattr(self.formula, "input", None) in SPATIAL_INPUTS


class IndicatorGrid(StrictModel):
    grid_version: Text
    status: Text
    display_label: Localized
    source_document: Text | None = None
    axes: list[Axis] = Field(min_length=1)
    indicators: list[IndicatorDefinition] = Field(min_length=1)

    @model_validator(mode="after")
    def references(self) -> Self:
        axes = [a.code for a in self.axes]
        if len(set(axes)) != len(axes):
            raise ValueError("Codes d'axe en double.")
        codes = [i.code for i in self.indicators]
        duplicates = sorted({c for c in codes if codes.count(c) > 1})
        if duplicates:
            raise ValueError(f"Codes d'indicateur en double : {', '.join(duplicates)}.")
        unknown = sorted({i.axis for i in self.indicators} - set(axes))
        if unknown:
            raise ValueError(f"Axe inconnu dans les indicateurs : {', '.join(unknown)}.")
        return self

    def for_profile(self, profile: str) -> list[IndicatorDefinition]:
        return [i for i in self.indicators if i.enabled and profile in i.profiles]


class Thresholds(StrictModel):
    deficit_marked: float = Field(gt=0)
    watch: float = Field(gt=0)


class ThresholdSet(StrictModel):
    higher_better: Thresholds
    lower_better: Thresholds

    @model_validator(mode="after")
    def ordered(self) -> Self:
        if not self.higher_better.deficit_marked < self.higher_better.watch <= 1:
            raise ValueError(
                "« plus = mieux » : il faut deficit_marked < watch ≤ 1 (ex. 0.80 et 0.95)."
            )
        if not self.lower_better.deficit_marked > self.lower_better.watch >= 1:
            raise ValueError(
                "« moins = mieux » : il faut deficit_marked > watch ≥ 1 (ex. 1.20 et 1.05)."
            )
        return self


class Evaluation(StrictModel):
    evaluation_version: Text
    status: Text
    reference: Literal["population_weighted_mean"]
    thresholds: ThresholdSet
    facility_minimum: int = Field(default=10, ge=0)
    label: Localized
    statuses: dict[
        Literal[
            "deficit_marked",
            "watch",
            "ok",
            "context",
            "not_evaluable",
            "not_available",
            "not_applicable",
        ],
        Localized,
    ]


class BadgeDef(StrictModel):
    label: Localized
    help: Localized


class RecencyStep(StrictModel):
    max_age: int = Field(ge=0)
    points: int = Field(ge=0, le=100)


class Reliability(StrictModel):
    source: dict[Literal["official", "open", "estimated", "fictitious"], int]
    recency: list[RecencyStep] = Field(min_length=1)
    completeness: dict[Literal["complete", "provisional"], int]
    method: dict[Literal["direct", "derived", "modeled"], int]


class Confidence(StrictModel):
    badges: dict[Literal["official", "open", "estimated", "fictitious"], BadgeDef]
    order: list[Literal["official", "open", "estimated", "fictitious"]]
    reliability: Reliability


GRID_EXAMPLES = {
    "direction": "direction: higher_better",
    "reference": "reference: relative",
    "formula": "formula: { type: raw, input: unemployment_rate, year: 2024 }",
    "type": "type: proximity_share",
    "profiles": "profiles: [urbain, mixte]",
    "code": "code: EMP_CHOM",
    "axis": "axis: emploi",
    "distance_m": "distance_m: 500",
    "decimals": "decimals: 1",
    "deficit_marked": "deficit_marked: 0.80",
    "watch": "watch: 0.95",
}


def load_grid(path: Path) -> IndicatorGrid:
    return load_model(path, IndicatorGrid, GRID_EXAMPLES)


def load_evaluation(path: Path) -> Evaluation:
    return load_model(path, Evaluation, GRID_EXAMPLES)


def load_confidence(path: Path) -> Confidence:
    return load_model(path, Confidence, GRID_EXAMPLES)


def method_fingerprint(*paths: Path) -> str:
    """Hash of the method files: a diagnostic is recomputed when one of them changes."""
    digest = hashlib.sha256()
    for path in paths:
        digest.update(path.read_bytes())
    return digest.hexdigest()[:16]
