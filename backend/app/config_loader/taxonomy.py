"""Schema of config/taxonomy/<profile>.yaml (themes of citizen contributions)."""

from pathlib import Path
from typing import Self

from pydantic import Field, model_validator

from app.config_loader.territory import Localized, Slug, StrictModel, Text
from app.config_loader.validation import load_model


class Keywords(StrictModel):
    fr: list[str] = Field(default_factory=list)
    ar: list[str] = Field(default_factory=list)
    darija: list[str] = Field(default_factory=list)


class DataRequest(StrictModel):
    """Data to ask for when no indicator of the grid covers the theme (« Besoins en données »)."""

    data: Localized
    holder: Localized


class Theme(StrictModel):
    code: Slug
    label: Localized
    description: Text
    keywords: Keywords = Field(default_factory=Keywords)
    indicators: list[str] = Field(default_factory=list)
    data_request: DataRequest | None = None


class CrossingRules(StrictModel):
    min_contributions: int = Field(default=5, ge=1)
    percent_min_total: int = Field(default=20, ge=1)
    strong_share: float = Field(default=0.15, gt=0, lt=1)
    labels: dict[str, Localized]


class Taxonomy(StrictModel):
    taxonomy_version: Text
    status: Text
    profile: Slug
    label: Localized
    tonalities: dict[str, Localized] = Field(min_length=1)
    themes: list[Theme] = Field(min_length=2)
    crossing: CrossingRules

    @model_validator(mode="after")
    def unique_codes(self) -> Self:
        codes = [t.code for t in self.themes]
        duplicates = sorted({c for c in codes if codes.count(c) > 1})
        if duplicates:
            raise ValueError(f"Thèmes en double : {', '.join(duplicates)}.")
        return self

    def theme(self, code: str) -> Theme | None:
        return next((t for t in self.themes if t.code == code), None)


def load_taxonomy(path: Path) -> Taxonomy:
    return load_model(
        path,
        Taxonomy,
        {"themes": "- code: mobilite", "indicators": "indicators: [MOB_TC, MOB_TRAM]"},
    )
