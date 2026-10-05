from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.config_loader import ConfigError, load_territories
from app.config_loader.territory import Localized, Profiles
from app.settings import get_settings

router = APIRouter(prefix="/api/territories", tags=["territories"])


class ScopeSummary(BaseModel):
    code: str
    label: Localized
    default: bool


class TerritorySummary(BaseModel):
    code: str
    name: Localized
    region: Localized
    study_area: Localized
    profiles: Profiles
    scopes: list[ScopeSummary]


@router.get("")
def list_territories() -> list[TerritorySummary]:
    try:
        territories = load_territories(get_settings().config_dir / "territories")
    except ConfigError as exc:
        raise HTTPException(status_code=503, detail=exc.format()) from None
    return [
        TerritorySummary(
            code=t.code,
            name=t.name,
            region=t.region,
            study_area=t.study_area.label,
            profiles=t.profiles,
            scopes=[ScopeSummary(code=s.code, label=s.label, default=s.default) for s in t.scopes],
        )
        for t in territories.values()
    ]
