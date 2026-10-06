"""Diagnostic reports written by the AI (or by templates when it is unavailable)."""

import unicodedata
from datetime import UTC, datetime
from typing import Annotated, Any, Literal

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_engine
from app.models import Report
from app.security import Account, Role, require_account
from app.services.indicators.engine import MissingInput
from app.services.llm import LLMError, get_provider
from app.services.llm.ollama import OllamaProvider
from app.services.reports.context import latest_diagnostic
from app.services.reports.generate import (
    citizens_for,
    current_cache_key,
    provider_identity,
    request_report,
)
from app.services.reports.jobs import enqueue
from app.settings import get_settings

router = APIRouter(tags=["reports"])


class ReportRequest(BaseModel):
    language: Literal["fr", "ar"] = "fr"
    force: bool = False


class StatusChange(BaseModel):
    status: Literal["brouillon", "relu", "valide"]


def serialize(report: Report, cached: bool = False) -> dict[str, Any]:
    return {
        "id": report.id,
        "territory_id": report.territory_id,
        "language": report.language,
        "provider": report.provider,
        "model": report.model,
        "state": report.state,
        "status": report.status,
        "writing_mode": report.writing_mode,
        "progress": report.progress,
        "content": report.content,
        "history": report.history,
        "error": report.error,
        "duration_s": report.duration_s,
        "created_at": report.created_at.isoformat() if report.created_at else None,
        "finished_at": report.finished_at.isoformat() if report.finished_at else None,
        "cached": cached,
    }


def _export_payload(report: Report) -> dict[str, Any]:
    return {**serialize(report), "fact_sheet": report.fact_sheet}


@router.post("/api/territories/{code}/units/{unit_id}/reports")
def create(
    code: str,
    unit_id: int,
    body: ReportRequest,
    account: Annotated[Account, Depends(require_account)],
) -> dict[str, Any]:
    with Session(get_engine()) as session:
        try:
            report, cached = request_report(
                session, code, unit_id, body.language, account.username, body.force
            )
        except (MissingInput, LookupError) as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from None
        if not cached:
            enqueue(report.id, code)
        return serialize(report, cached)


@router.get("/api/reports/{report_id}")
def read(report_id: int, _: Annotated[Account, Depends(require_account)]) -> dict[str, Any]:
    with Session(get_engine()) as session:
        report = session.get(Report, report_id)
        if report is None:
            raise HTTPException(status_code=404, detail="Rapport introuvable.")
        return serialize(report)


@router.get("/api/territories/{code}/units/{unit_id}/reports")
def latest(
    code: str, unit_id: int, _: Annotated[Account, Depends(require_account)]
) -> list[dict[str, Any]]:
    with Session(get_engine()) as session:
        reports = session.scalars(
            select(Report)
            .where(Report.territory_id == unit_id, Report.state.in_(("done", "blocked")))
            .order_by(Report.created_at.desc())
            .limit(10)
        ).all()
        seen: set[str] = set()
        out = []
        current: dict[str, str] = {}
        if reports:
            diagnostic = latest_diagnostic(session, code)
            provider, model = provider_identity()
            citizens = citizens_for(session, diagnostic.study_area_id, unit_id)
            current = {
                lang: current_cache_key(
                    diagnostic.result, unit_id, lang, provider, model, citizens=citizens
                )
                for lang in ("fr", "ar")
            }
        for report in reports:
            if report.language not in seen:
                seen.add(report.language)
                # Written with older data, outline, controls or model: shown, but to regenerate.
                out.append(
                    {
                        **serialize(report, cached=True),
                        "outdated": report.cache_key != current.get(report.language),
                    }
                )
        return out


@router.post("/api/reports/{report_id}/status")
def change_status(
    report_id: int, body: StatusChange, account: Annotated[Account, Depends(require_account)]
) -> dict[str, Any]:
    if body.status == "valide" and Role.referent not in account.roles:
        raise HTTPException(
            status_code=403, detail="Seul le référent scientifique peut valider un rapport."
        )
    with Session(get_engine()) as session:
        report = session.get(Report, report_id)
        if report is None:
            raise HTTPException(status_code=404, detail="Rapport introuvable.")
        if report.state != "done":
            raise HTTPException(status_code=409, detail="Le rapport n'est pas prêt.")
        report.status = body.status
        report.history = [
            *report.history,
            {"status": body.status, "by": account.username, "at": datetime.now(UTC).isoformat()},
        ]
        session.commit()
        return serialize(report)


@router.get("/api/llm/status")
def llm_status(_: Annotated[Account, Depends(require_account)]) -> dict[str, Any]:
    settings = get_settings()
    info: dict[str, Any] = {
        "sovereign_mode": settings.sovereign_mode,
        "provider": settings.llm_provider,
        "model": settings.ollama_model
        if settings.llm_provider == "ollama"
        else settings.anthropic_model,
        "reachable": False,
    }
    try:
        provider = get_provider(settings)
    except LLMError as exc:
        info["error"] = str(exc)
        return info
    if isinstance(provider, OllamaProvider):
        models = provider.available_models()
        info["reachable"] = bool(models)
        info["installed"] = models
        info["model_installed"] = provider.model in models
    return info


EXPORT_TYPES = {
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "pdf": "application/pdf",
}


@router.get("/api/reports/{report_id}/export.{fmt}")
def export(report_id: int, fmt: str, _: Annotated[Account, Depends(require_account)]) -> Response:
    from app.services.reports.export import to_docx, to_pdf
    from app.services.reports.maps import unit_map_png

    if fmt not in EXPORT_TYPES:
        raise HTTPException(status_code=404, detail="Format inconnu (docx ou pdf).")
    with Session(get_engine()) as session:
        report = session.get(Report, report_id)
        if report is None:
            raise HTTPException(status_code=404, detail="Rapport introuvable.")
        if report.state != "done":
            raise HTTPException(
                status_code=409, detail="Seul un rapport terminé et contrôlé peut être exporté."
            )
        if report.language != "fr":
            raise HTTPException(
                status_code=409, detail="Les exports en arabe arrivent à l'étape 7."
            )
        payload = _export_payload(report)
        map_png = unit_map_png(session, report.territory_id, report.language)
    data = to_docx(payload, map_png) if fmt == "docx" else to_pdf(payload, map_png)
    name = payload["content"]["identity"]["name_fr"]
    ascii_name = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    slug = "-".join("".join(c if c.isalnum() else " " for c in ascii_name).lower().split())
    filename = f"majal-diagnostic-{slug}-{report.status}.{fmt}"
    return Response(
        content=data,
        media_type=EXPORT_TYPES[fmt],
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
