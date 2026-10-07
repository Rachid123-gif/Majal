"""Scenario of the presentation mode (BRIEF §8, §9.9): config/presentation/<territory>.yaml, with
the units resolved from their official names to their identifiers."""

from typing import Annotated, Any, Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config_loader import ConfigError
from app.config_loader.territory import Slug, StrictModel, Text
from app.config_loader.validation import load_model
from app.db import get_engine
from app.models import StudyArea, Territory
from app.security import Account, require_account
from app.settings import get_settings

router = APIRouter(tags=["presentation"])

Step = Literal[
    "home", "stakes", "map", "sheet", "compare", "citizens", "report", "data_needs", "proposal"
]


class FrText(StrictModel):
    fr: Text
    ar: Text | None = None  # Arabic later


class MapStep(StrictModel):
    indicator: str


class UnitStep(StrictModel):
    unit: Text


class CompareStep(StrictModel):
    units: list[Text] = Field(min_length=2, max_length=4)


class CitizensStep(StrictModel):
    scale: Literal["unit", "commune"] = "unit"
    unit: Text


class DataNeedsStep(StrictModel):
    suggested: list[Slug] = Field(default_factory=list)


class StakesStep(StrictModel):
    sentence: FrText


class ProposalStep(StrictModel):
    title: FrText
    items: list[FrText] = Field(min_length=1)
    contact: list[Text] = Field(default_factory=list)


class Scenario(StrictModel):
    territory: Slug
    data_note: FrText
    steps: list[Step] = Field(min_length=1)
    map: MapStep
    sheet: UnitStep
    compare: CompareStep
    citizens: CitizensStep
    report: UnitStep
    data_needs: DataNeedsStep
    stakes: StakesStep
    proposal: ProposalStep


def load_scenario(path: Any) -> Scenario:
    return load_model(path, Scenario, {"steps": "steps: [home, stakes, map]"})


@router.get("/api/presentation/{code}")
def scenario(code: str, _: Annotated[Account, Depends(require_account)]) -> dict[str, Any]:
    path = get_settings().config_dir / "presentation" / f"{code}.yaml"
    if not path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Scénario de présentation non rédigé : config/presentation/{code}.yaml.",
        )
    try:
        config = load_scenario(path)
    except ConfigError as exc:
        raise HTTPException(status_code=500, detail=exc.format()) from None
    with Session(get_engine()) as session:
        area = session.scalars(select(StudyArea).where(StudyArea.code == code)).one_or_none()
        if area is None:
            raise HTTPException(status_code=404, detail="Territoire inconnu ou non importé.")
        territories = session.scalars(
            select(Territory).where(Territory.study_area_id == area.id)
        ).all()

    def resolve(name: str, analysis_unit: bool = True) -> int:
        matches = [
            t
            for t in territories
            if t.name_fr == name and (t.is_analysis_unit or not analysis_unit)
        ]
        if not matches:
            raise HTTPException(
                status_code=422,
                detail=f"config/presentation/{code}.yaml : unité « {name} » introuvable parmi "
                "les unités importées (vérifier l'orthographe officielle).",
            )
        return matches[0].id

    return {
        "territory": code,
        "data_note": config.data_note.model_dump(),
        "steps": config.steps,
        "map": {"indicator": config.map.indicator},
        "sheet": {"unit": resolve(config.sheet.unit), "name": config.sheet.unit},
        "compare": {"units": [resolve(name) for name in config.compare.units]},
        "citizens": {
            "scale": config.citizens.scale,
            "unit": resolve(config.citizens.unit, analysis_unit=config.citizens.scale == "unit"),
            "name": config.citizens.unit,
        },
        "report": {"unit": resolve(config.report.unit), "name": config.report.unit},
        "data_needs": {"suggested": config.data_needs.suggested},
        "stakes": {"sentence": config.stakes.sentence.model_dump()},
        "proposal": config.proposal.model_dump(),
    }
