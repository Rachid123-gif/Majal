"""Schema of `config/mappings/osm_facilities.yaml` (OSM tags -> MAJAL facility categories)."""

import re
from pathlib import Path
from typing import Annotated, Self

from pydantic import AfterValidator, Field, model_validator

from app.config_loader.territory import Localized, Slug, StrictModel, Text
from app.config_loader.validation import load_model

RULE = re.compile(r"^[a-z_:]+=[A-Za-z0-9_:\-]+$")
COLOR = re.compile(r"^#[0-9a-fA-F]{6}$")


def _rule(value: str) -> str:
    if not RULE.match(value):
        raise ValueError(
            f"Règle « {value} » mal écrite : attendu « clé=valeur », par exemple amenity=school."
        )
    return value


def _color(value: str) -> str:
    if not COLOR.match(value):
        raise ValueError(f'Couleur « {value} » mal écrite : attendu par exemple "#12545a".')
    return value


class FacilityCategory(StrictModel):
    code: Slug
    label: Localized
    group: Slug
    color: Annotated[str, AfterValidator(_color)]
    enabled: bool = True
    rules: list[Annotated[str, AfterValidator(_rule)]] = Field(min_length=1)
    # Objects matching one of these rules are left out (e.g. private gardens).
    exclude: list[Annotated[str, AfterValidator(_rule)]] = Field(default_factory=list)

    def tag_pairs(self) -> list[tuple[str, str]]:
        return [(rule.split("=", 1)[0], rule.split("=", 1)[1]) for rule in self.rules]

    def excluded(self, tags: dict[str, str]) -> bool:
        return any(tags.get(r.split("=", 1)[0]) == r.split("=", 1)[1] for r in self.exclude)


class FacilityMapping(StrictModel):
    mapping_version: Text
    status: Text
    source_note: Text | None = None
    categories: list[FacilityCategory] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_codes(self) -> Self:
        codes = [c.code for c in self.categories]
        duplicates = sorted({c for c in codes if codes.count(c) > 1})
        if duplicates:
            raise ValueError(f"Codes de catégorie en double : {', '.join(duplicates)}.")
        return self

    @property
    def enabled(self) -> list[FacilityCategory]:
        return [c for c in self.categories if c.enabled]

    def classify(self, tags: dict[str, str]) -> FacilityCategory | None:
        """First enabled category with a matching rule (order matters)."""
        for category in self.enabled:
            if any(tags.get(key) == value for key, value in category.tag_pairs()):
                return None if category.excluded(tags) else category
        return None


EXAMPLES = {
    "rules": 'rules: ["amenity=school"]',
    "color": 'color: "#12545a"',
    "code": "code: school",
    "group": "group: education",
    "enabled": "enabled: false",
    "exclude": 'exclude: ["access=private"]',
}


def load_facility_mapping(path: Path) -> FacilityMapping:
    return load_model(path, FacilityMapping, EXAMPLES)
