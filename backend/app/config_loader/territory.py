"""Schema of `config/territories/<code>.yaml`.

Adding a territory means adding one of these files and running the imports — never
changing business logic.
"""

import re
from enum import StrEnum
from pathlib import Path
from typing import Annotated, Literal, Self

from pydantic import (
    AfterValidator,
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    ValidationInfo,
    field_validator,
    model_validator,
)

from app.config_loader.errors import ConfigError
from app.config_loader.validation import load_model

ARABIC_LETTERS = re.compile(r"[؀-ۿ]")


def _require_arabic(value: str) -> str:
    if not ARABIC_LETTERS.search(value):
        raise ValueError("Le texte arabe doit contenir des caractères arabes.")
    return value


Slug = Annotated[str, StringConstraints(pattern=r"^[a-z][a-z0-9_]*$")]
Text = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
ArabicText = Annotated[Text, AfterValidator(_require_arabic)]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class Localized(StrictModel):
    fr: Text
    ar: ArabicText


class LevelKind(StrEnum):
    region = "region"
    prefecture = "prefecture"
    province = "province"
    commune = "commune"
    arrondissement = "arrondissement"
    quartier = "quartier"
    douar = "douar"
    grid = "grid"


class StudyArea(StrictModel):
    level: LevelKind
    label: Localized


class ScopeMember(StrictModel):
    """Selection rule used by the importers: which administrative units form the scope."""

    level: LevelKind
    name_fr: Text


class Scope(StrictModel):
    code: Slug
    label: Localized
    default: bool = False
    members: list[ScopeMember] = Field(min_length=1)


class MainLevel(StrictModel):
    levels: list[LevelKind] = Field(min_length=1)
    terms: dict[LevelKind, Localized]

    @model_validator(mode="after")
    def every_level_has_a_term(self) -> Self:
        missing = [lvl.value for lvl in self.levels if lvl not in self.terms]
        if missing:
            raise ValueError(
                "Chaque niveau listé dans « levels » doit avoir son libellé dans « terms ». "
                f"Libellé manquant pour : {', '.join(missing)}."
            )
        return self


class FineLevel(StrictModel):
    level: LevelKind
    term: Localized
    cell_size_m: int | None = Field(default=None, ge=100, le=5000)
    fallback: Literal["grid"] | None = None
    fallback_cell_size_m: int | None = Field(default=None, ge=100, le=5000)

    @model_validator(mode="after")
    def grid_needs_cell_size(self) -> Self:
        if self.level == LevelKind.grid and self.cell_size_m is None:
            raise ValueError(
                "Un maillage régulier (level: grid) demande « cell_size_m » (en mètres)."
            )
        if self.fallback == "grid" and self.fallback_cell_size_m is None:
            raise ValueError("« fallback: grid » demande « fallback_cell_size_m » (en mètres).")
        return self


class AnalysisLevels(StrictModel):
    main: MainLevel
    fine: FineLevel


class Profiles(StrictModel):
    indicators: Slug
    taxonomy: Slug


class SourceRef(BaseModel):
    """Importer-specific parameters are validated by the importer itself."""

    model_config = ConfigDict(extra="allow", frozen=True)

    importer: Slug


class MapSettings(StrictModel):
    center: (
        tuple[Annotated[float, Field(ge=-180, le=180)], Annotated[float, Field(ge=-90, le=90)]]
        | None
    ) = None
    zoom: float | None = Field(default=None, ge=0, le=22)


class DemoSettings(StrictModel):
    fictitious_contributions: Text | None = None


class TerritoryConfig(StrictModel):
    code: Slug
    schema_version: Literal[1]
    name: Localized
    region: Localized
    study_area: StudyArea
    scopes: list[Scope] = Field(min_length=1)
    analysis_levels: AnalysisLevels
    profiles: Profiles
    sources: dict[Slug, SourceRef] = Field(default_factory=dict)
    data_holders: Text | None = None
    map: MapSettings = MapSettings()
    demo: DemoSettings = DemoSettings()

    @field_validator("code")
    @classmethod
    def code_matches_file_name(cls, value: str, info: ValidationInfo) -> str:
        stem = (info.context or {}).get("file_stem")
        if stem is not None and value != stem:
            raise ValueError(
                f"Le code « {value} » doit être identique au nom du fichier (« {stem} »)."
            )
        return value

    @model_validator(mode="after")
    def scopes_are_consistent(self) -> Self:
        codes = [scope.code for scope in self.scopes]
        duplicates = sorted({c for c in codes if codes.count(c) > 1})
        if duplicates:
            raise ValueError(f"Codes de périmètre en double : {', '.join(duplicates)}.")
        defaults = [scope.code for scope in self.scopes if scope.default]
        if len(defaults) != 1:
            raise ValueError(
                "Un et un seul périmètre doit porter « default: true » "
                f"(actuellement : {len(defaults)})."
            )
        return self

    @property
    def default_scope(self) -> Scope:
        return next(scope for scope in self.scopes if scope.default)


EXAMPLES = {
    "code": "code: rabat",
    "schema_version": "schema_version: 1",
    "fr": 'fr: "Rabat"',
    "ar": 'ar: "الرباط"',
    "level": "level: commune",
    "levels": "levels: [arrondissement, commune]",
    "name_fr": 'name_fr: "Salé"',
    "default": "default: true",
    "members": '- { level: prefecture, name_fr: "Rabat" }',
    "cell_size_m": "cell_size_m: 500",
    "fallback_cell_size_m": "fallback_cell_size_m: 1000",
    "indicators": "indicators: urbain",
    "taxonomy": "taxonomy: urbain",
    "importer": "importer: boundaries_file",
    "center": "center: [-6.84, 34.01]   # longitude, latitude",
    "zoom": "zoom: 10",
    "scopes": "scopes:\n    - code: agglomeration\n      default: true …",
}


def load_territory(path: Path) -> TerritoryConfig:
    return load_model(path, TerritoryConfig, EXAMPLES)


def load_territories(directory: Path) -> dict[str, TerritoryConfig]:
    """Load every territory file; report the errors of all files at once."""
    territories: dict[str, TerritoryConfig] = {}
    issues = []
    for path in sorted(directory.glob("*.yaml")):
        try:
            territory = load_territory(path)
        except ConfigError as exc:
            issues.extend(exc.issues)
            continue
        territories[territory.code] = territory
    if issues:
        raise ConfigError(issues)
    return territories
