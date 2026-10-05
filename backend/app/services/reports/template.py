"""Schema of config/report_templates/diagnostic_commune.yaml (report outline)."""

from pathlib import Path
from typing import Literal, Self

from pydantic import Field, model_validator

from app.config_loader.territory import Localized, Slug, StrictModel, Text
from app.config_loader.validation import load_model


class FreeText(StrictModel):
    """Instructions and fixed texts: no Arabic-letter check (they may quote codes)."""

    fr: Text
    ar: Text


class Section(StrictModel):
    code: Slug
    title: Localized
    mode: Literal["ai", "auto"] = "ai"
    indicators: list[str] | Literal["attention"] = Field(default_factory=list)
    include_identity: bool = False
    include_typology: bool = False
    words: int = Field(default=100, ge=20, le=400)
    instruction: FreeText | None = None
    auto_text: FreeText | None = None

    @model_validator(mode="after")
    def coherent(self) -> Self:
        if self.mode == "ai" and self.instruction is None:
            raise ValueError("Une section rédigée par l'IA demande une « instruction ».")
        return self


class ReportTemplate(StrictModel):
    template_version: Text
    status: Text
    title: Localized
    style: FreeText
    examples: dict[Literal["fr", "ar"], list[str]] = Field(default_factory=dict)
    sections: list[Section] = Field(min_length=1)


def load_template(path: Path) -> ReportTemplate:
    return load_model(
        path,
        ReportTemplate,
        {
            "mode": "mode: ai",
            "words": "words: 100",
            "indicators": "indicators: [EMP_CHOM, EMP_ACTF]",
        },
    )
