"""Module « Besoins en données » (stage 5): completeness, what each institution's data would
allow, ranked requests (« Par où commencer ») and the follow-up of the requests."""

import datetime as dt
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config_loader import ConfigError
from app.config_loader.data_holders import (
    DataHolders,
    ModuleRules,
    load_data_holders,
    load_module_rules,
)
from app.config_loader.indicators import load_grid
from app.db import get_engine
from app.models import DataRequestTracking, StudyArea
from app.security import Account, Role, require_account
from app.services.citizens.pipeline import taxonomy_for
from app.services.data_needs.completeness import compute
from app.services.indicators.engine import MissingInput
from app.services.reports.context import latest_diagnostic
from app.settings import get_settings

router = APIRouter(tags=["data-needs"])


def _area(session: Session, code: str) -> StudyArea:
    area = session.scalars(select(StudyArea).where(StudyArea.code == code)).one_or_none()
    if area is None:
        raise HTTPException(status_code=404, detail="Territoire inconnu ou non importé.")
    return area


def _config(code: str) -> tuple[DataHolders, ModuleRules]:
    root = get_settings().config_dir / "data_holders"
    path = root / f"{code}.yaml"
    if not path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Référentiel des institutions non rédigé : config/data_holders/{code}.yaml.",
        )
    try:
        return load_data_holders(path), load_module_rules(root / "regles.yaml")
    except ConfigError as exc:
        raise HTTPException(status_code=500, detail=exc.format()) from None


def _tracking(row: DataRequestTracking | None, rules: ModuleRules) -> dict[str, Any]:
    status = row.status if row else "to_send"
    return {
        "status": status,
        "status_label": rules.tracking_statuses[status].model_dump()
        if status in rules.tracking_statuses
        else None,
        "date": row.status_date.isoformat() if row and row.status_date else None,
        "updated_by": row.updated_by if row else None,
        "history": row.history if row else [],
    }


@router.get("/api/territories/{code}/data-needs")
def data_needs(code: str, _: Annotated[Account, Depends(require_account)]) -> dict[str, Any]:
    return _data_needs(code)


def _data_needs(code: str) -> dict[str, Any]:
    holders, rules = _config(code)
    with Session(get_engine()) as session:
        area = _area(session, code)
        try:
            diagnostic = latest_diagnostic(session, code).result
        except MissingInput as exc:
            raise HTTPException(status_code=409, detail=exc.reason) from None
        grid = load_grid(get_settings().config_dir / "indicators" / "grille-v0.yaml")
        result = compute(diagnostic, grid, holders, rules, taxonomy_for(area))
        rows = {
            r.institution_code: r
            for r in session.scalars(
                select(DataRequestTracking).where(DataRequestTracking.study_area_id == area.id)
            )
        }
        for institution in result["institutions"]:
            institution["tracking"] = _tracking(rows.get(institution["code"]), rules)
        result["tracking_statuses"] = {
            k: v.model_dump() for k, v in rules.tracking_statuses.items()
        }
        result["territory"] = code
        return result


class TrackingUpdate(BaseModel):
    status: str
    date: dt.date | None = None


@router.put("/api/territories/{code}/data-needs/institutions/{institution}/tracking")
def update_tracking(
    code: str,
    institution: str,
    update: TrackingUpdate,
    account: Annotated[Account, Depends(require_account)],
) -> dict[str, Any]:
    if not ({Role.referent, Role.admin} & set(account.roles)):
        raise HTTPException(
            status_code=403,
            detail="Le suivi des demandes est réservé aux comptes professeur et administrateur.",
        )
    holders, rules = _config(code)
    if holders.institution(institution) is None:
        raise HTTPException(status_code=404, detail="Institution absente du référentiel.")
    if update.status not in rules.tracking_statuses:
        raise HTTPException(
            status_code=422,
            detail="Statut inconnu : " + ", ".join(rules.tracking_statuses) + ".",
        )
    with Session(get_engine()) as session:
        area = _area(session, code)
        row = session.scalars(
            select(DataRequestTracking).where(
                DataRequestTracking.study_area_id == area.id,
                DataRequestTracking.institution_code == institution,
            )
        ).one_or_none()
        if row is None:
            row = DataRequestTracking(
                study_area_id=area.id, institution_code=institution, history=[]
            )
            session.add(row)
        row.status = update.status
        row.status_date = update.date or dt.date.today()
        row.updated_by = account.username
        row.history = [
            *(row.history or []),
            {
                "status": update.status,
                "date": row.status_date.isoformat(),
                "by": account.username,
            },
        ]
        session.commit()
        return _tracking(row, rules)


@router.get("/api/territories/{code}/data-needs/export.xlsx")
def export_xlsx(code: str, _: Annotated[Account, Depends(require_account)]) -> Response:
    """Summary spreadsheet of the data requests (ranked, with the « Priorité » column)."""
    from app.services.data_needs.excel import to_xlsx

    holders, _rules = _config(code)
    body = to_xlsx(_data_needs(code), holders.note_territory.fr)
    return Response(
        content=body,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f'attachment; filename="majal-besoins-donnees-{code}.xlsx"'
        },
    )


NOTE_TYPES = {
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "pdf": "application/pdf",
}


@router.get("/api/territories/{code}/data-needs/institutions/{institution}/note.{fmt}")
def note(
    code: str, institution: str, fmt: str, _: Annotated[Account, Depends(require_account)]
) -> Response:
    """Draft data request note (fixed template, no AI), to be read and adapted before sending."""
    from app.services.data_needs.notes import build_note, load_note_template, to_docx, to_pdf

    if fmt not in NOTE_TYPES:
        raise HTTPException(status_code=404, detail="Format inconnu : docx ou pdf.")
    holders, _rules = _config(code)
    if holders.institution(institution) is None:
        raise HTTPException(status_code=404, detail="Institution absente du référentiel.")
    template = load_note_template(
        get_settings().config_dir / "report_templates" / "note_demande.yaml"
    )
    content = build_note(_data_needs(code), institution, holders, template)
    body = to_docx(content) if fmt == "docx" else to_pdf(content)
    filename = f"majal-note-demande-{code}-{institution}.{fmt}"
    return Response(
        content=body,
        media_type=NOTE_TYPES[fmt],
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
