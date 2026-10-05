"""Diagnostic of a territory: indicator values, references, statuses, ranks."""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.config_loader import ConfigError, load_territories
from app.db import get_engine
from app.models import Diagnostic, StudyArea
from app.security import Account, require_account
from app.services.indicators.engine import MissingInput, compute_diagnostic, load_method
from app.settings import get_settings

router = APIRouter(prefix="/api/territories", tags=["diagnostics"])
KEEP = 10  # diagnostics kept per territory (history)


def _respond(diagnostic: Diagnostic, recomputed: bool) -> dict[str, Any]:
    return {
        **diagnostic.result,
        "meta": {
            "diagnostic_id": diagnostic.id,
            "computed_at": diagnostic.computed_at.isoformat() if diagnostic.computed_at else None,
            "author": diagnostic.author,
            "duration_ms": diagnostic.duration_ms,
            "recomputed": recomputed,
        },
    }


def _compute(session: Session, code: str, author: str) -> Diagnostic:
    try:
        diagnostic = compute_diagnostic(session, code, author=author)
    except ConfigError as exc:
        raise HTTPException(status_code=503, detail=exc.format()) from None
    except MissingInput as exc:
        raise HTTPException(status_code=409, detail=exc.reason) from None
    session.execute(
        text(
            "DELETE FROM diagnostics WHERE study_area_id = :sa AND id NOT IN ("
            "SELECT id FROM diagnostics WHERE study_area_id = :sa "
            "ORDER BY computed_at DESC LIMIT :keep)"
        ),
        {"sa": diagnostic.study_area_id, "keep": KEEP},
    )
    session.commit()
    return diagnostic


@router.get("/{code}/diagnostic")
def latest(code: str, account: Annotated[Account, Depends(require_account)]) -> dict[str, Any]:
    try:
        territories = load_territories(get_settings().config_dir / "territories")
        if code not in territories:
            raise HTTPException(status_code=404, detail=f"Territoire inconnu : {code}.")
        fingerprint = load_method(territories[code]).fingerprint
    except ConfigError as exc:
        raise HTTPException(status_code=503, detail=exc.format()) from None
    with Session(get_engine()) as session:
        area = session.scalars(select(StudyArea).where(StudyArea.code == code)).one_or_none()
        if area is None:
            raise HTTPException(status_code=409, detail="Données non importées pour ce territoire.")
        diagnostic = session.scalars(
            select(Diagnostic)
            .where(Diagnostic.study_area_id == area.id)
            .order_by(Diagnostic.computed_at.desc())
            .limit(1)
        ).one_or_none()
        # The method files changed (grid, thresholds, mapping…): recompute automatically.
        if diagnostic is None or diagnostic.method_hash != fingerprint:
            return _respond(_compute(session, code, f"auto ({account.username})"), True)
        return _respond(diagnostic, False)


@router.post("/{code}/diagnostic")
def recompute(code: str, account: Annotated[Account, Depends(require_account)]) -> dict[str, Any]:
    with Session(get_engine()) as session:
        return _respond(_compute(session, code, account.username), True)
