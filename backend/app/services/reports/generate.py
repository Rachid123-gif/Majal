"""Report generation: fact sheet → sections (AI or fallback) → rendering → final check.

Reports are cached: the same unit, diagnostic, language, model and outline give back the
stored report instantly (demonstrations without waiting, or without the model at all).
"""

import hashlib
import json
import time
from datetime import UTC, datetime
from typing import Any, cast

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Report, Territory
from app.services.llm import LLMError, get_provider
from app.services.llm.ollama import OllamaProvider
from app.services.reports.context import latest_diagnostic, unit_identity
from app.services.reports.facts import FactSheet, build_fact_sheet
from app.services.reports.numbers import check_rendered, definitional_phrases
from app.services.reports.template import ReportTemplate, load_template
from app.services.reports.writer import Lang, SectionResult, render, write_section
from app.settings import get_settings

METHOD_NOTE = {
    "fr": [
        "Chaque chiffre de ce rapport provient de la fiche de faits établie par MAJAL à partir des sources ci-dessous ; aucun chiffre n'est écrit par l'intelligence artificielle, et un contrôle automatique bloque tout nombre non tracé.",
        "Les évaluations sont relatives à la moyenne de l'ensemble étudié, pondérée par la population : aucune norme officielle n'est encore intégrée.",
        "Les limites administratives proviennent d'OpenStreetMap et restent à confronter aux limites officielles. Les indicateurs de proximité reposent sur une répartition estimée de la population et sur des distances à vol d'oiseau.",
        "Ce document est une aide à la décision : il doit être relu et validé par un urbaniste.",
    ],
    "ar": [
        "كل رقم في هذا التقرير مأخوذ من بطاقة الوقائع التي أعدها «مجال» انطلاقاً من المصادر أسفله؛ لا يكتب الذكاء الاصطناعي أي رقم، ومراقبة آلية توقف كل عدد غير موثق.",
        "التقييمات نسبية مقارنة بمتوسط المجال المدروس، مرجحاً بعدد السكان: لم يتم بعد إدراج أي معيار رسمي.",
        "الحدود الإدارية مأخوذة من OpenStreetMap ويتعين مقارنتها بالحدود الرسمية. تعتمد مؤشرات القرب على توزيع تقديري للسكان وعلى مسافات مستقيمة.",
        "هذه الوثيقة أداة للمساعدة على القرار: يجب أن يراجعها ويصادق عليها مختص في التعمير.",
    ],
}


def template_hash(template: ReportTemplate) -> str:
    return hashlib.sha256(template.model_dump_json().encode()).hexdigest()[:12]


def cache_key(
    diagnostic_hash: str, unit_id: int, lang: str, provider: str, model: str, template: str
) -> str:
    raw = json.dumps([diagnostic_hash, unit_id, lang, provider, model, template])
    return hashlib.sha256(raw.encode()).hexdigest()


def _typology_text(diagnostic: dict[str, Any], unit_id: int, lang: Lang) -> str | None:
    typology = diagnostic.get("typology") or {}
    entry = (typology.get("units") or {}).get(str(unit_id)) or (typology.get("units") or {}).get(
        unit_id
    )
    if not entry:
        return None
    traits = ", ".join(t[lang] for t in entry.get("traits", []))
    return f"{entry['label'][lang]}" + (f" ({traits})" if traits else "")


def _sources_section(sheet: FactSheet, used: set[str], lang: Lang) -> dict[str, Any]:
    sources: dict[str, set[str]] = {}
    for fact in sheet.facts:
        if fact.id in used and fact.source:
            badge = fact.badge or ""
            for name in fact.source.split("; "):
                sources.setdefault(name, set()).add(badge)
    badges = {
        "official": {"fr": "officiel", "ar": "رسمي"},
        "open": {"fr": "ouvert", "ar": "مفتوح"},
        "estimated": {"fr": "estimé", "ar": "تقديري"},
        "fictitious": {"fr": "fictif", "ar": "افتراضي"},
    }
    lines = [
        f"{name} ({', '.join(sorted(badges[b][lang] for b in kinds if b in badges))})"
        if any(b in badges for b in kinds)
        else name
        for name, kinds in sorted(sources.items())
    ]
    return {"sources": lines, "notes": METHOD_NOTE[lang]}


def build_report(
    session: Session,
    code: str,
    unit_id: int,
    lang: Lang,
    progress: Any = None,
    model: str | None = None,
) -> tuple[dict[str, Any], dict[str, Any], int, str]:
    """Write the full report. Returns (content, fact sheet, llm calls, writing mode)."""
    settings = get_settings()
    template = load_template(settings.config_dir / "report_templates" / "diagnostic_commune.yaml")
    diagnostic = latest_diagnostic(session, code)
    identity = unit_identity(session, unit_id)
    sheet = build_fact_sheet(diagnostic.result, unit_id, dict(identity))
    provider_error: str | None = None
    try:
        provider = get_provider(settings, model)
    except LLMError as exc:
        provider = None
        provider_error = str(exc)
    typology = _typology_text(diagnostic.result, unit_id, lang)
    definitional = definitional_phrases(
        [b.label["fr"] for b in sheet.briefs.values()]
        + [b.label["ar"] for b in sheet.briefs.values()]
    )
    sections_out: list[dict[str, Any]] = []
    used_all: set[str] = set()
    calls = 0
    results: list[SectionResult] = []
    for index, section in enumerate(template.sections, start=1):
        if section.code == "sources":
            continue
        if progress:
            progress(index, len(template.sections), section.title.model_dump()[lang])
        result = write_section(provider, sheet, section, template, lang, typology)
        if provider_error and result.mode == "fallback":
            result.error = provider_error
        results.append(result)
        calls += result.attempts
        rendered, verification = [], []
        for paragraph in result.paragraphs:
            text, used = render(paragraph, sheet, lang)
            used_all.update(used)
            if result.mode != "auto":
                values = [f.text[lang] for u in used if (f := sheet.get(u)) is not None]
                verification += [
                    i.describe() for i in check_rendered(text, values, sheet.years, definitional)
                ]
            rendered.append({"text": text, "facts": used})
        sections_out.append(
            {
                "number": index,
                "code": result.code,
                "title": result.title,
                "mode": result.mode,
                "attempts": result.attempts,
                "duration_s": round(result.duration_s, 1),
                "paragraphs": rendered,
                "raw": result.paragraphs,
                "issues": result.issues,
                "error": result.error,
                "verification": verification,
            }
        )
    sources = _sources_section(sheet, used_all, lang)
    sections_out.append(
        {
            "number": len(template.sections),
            "code": "sources",
            "title": next(
                s.title.model_dump()[lang] for s in template.sections if s.code == "sources"
            ),
            "mode": "auto",
            "attempts": 0,
            "duration_s": 0,
            "paragraphs": [],
            "raw": [],
            "issues": [],
            "error": None,
            "verification": [],
            **sources,
        }
    )
    written = [r for r in results if r.mode in ("ai", "fallback")]
    modes = {r.mode for r in written}
    writing_mode = "ai" if modes == {"ai"} else "fallback" if modes == {"fallback"} else "mixed"
    blocked = [v for s in sections_out for v in s["verification"]]
    content = {
        "title": template.title.model_dump()[lang],
        "language": lang,
        "identity": identity,
        "unit": sheet.unit,
        "grid_label": sheet.grid_label[lang],
        "evaluation_label": sheet.evaluation_label[lang],
        "typology": typology,
        "sections": sections_out,
        "verification": {"ok": not blocked, "issues": blocked},
        "diagnostic_id": diagnostic.id,
        "diagnostic_computed_at": diagnostic.computed_at.isoformat()
        if diagnostic.computed_at
        else None,
        "template_version": template.template_version,
    }
    return content, sheet.to_json(), calls, writing_mode


def provider_identity() -> tuple[str, str]:
    """Provider and model a new report will be written with. With Ollama, the fallback model
    (gemma3:4b) takes over when the main one (qwen3:8b) is not installed."""
    settings = get_settings()
    if settings.llm_provider == "none":
        return "none", "sans-ia"
    if settings.llm_provider != "ollama":
        return settings.llm_provider, settings.anthropic_model
    model = settings.ollama_model
    fallback = settings.ollama_fallback_model
    if fallback and fallback != model:
        installed = OllamaProvider(settings.ollama_url, model).available_models()
        if installed and model not in installed and fallback in installed:
            return "ollama", fallback
    return "ollama", model


def unit_data_hash(diagnostic: dict[str, Any], unit_id: int) -> str:
    """Hash of everything the report depends on for this unit (values, references, typology)."""
    unit = next((u for u in diagnostic["units"] if u["id"] == unit_id), None)
    payload = {
        "unit": unit,
        "indicators": diagnostic.get("indicators"),
        "evaluation": diagnostic.get("evaluation", {}).get("label"),
        "typology": (diagnostic.get("typology") or {}).get("units", {}).get(str(unit_id)),
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest()


def current_cache_key(
    diagnostic: dict[str, Any],
    unit_id: int,
    lang: str,
    provider: str,
    model: str,
    template: ReportTemplate | None = None,
) -> str:
    """Key of a report written now: same data, language, model and outline (+ controls)."""
    settings = get_settings()
    templates = settings.config_dir / "report_templates"
    template = template or load_template(templates / "diagnostic_commune.yaml")
    controls = hashlib.sha256((templates / "controles.yaml").read_bytes()).hexdigest()[:12]
    return cache_key(
        unit_data_hash(diagnostic, unit_id),
        unit_id,
        lang,
        provider,
        model,
        template_hash(template) + controls,
    )


def find_cached(session: Session, key: str) -> Report | None:
    return session.scalars(
        select(Report)
        .where(Report.cache_key == key, Report.state == "done")
        .order_by(Report.created_at.desc())
        .limit(1)
    ).one_or_none()


def run_report(session: Session, report_id: int, code: str) -> Report:
    """Generate a pending report (called by the background worker or inline)."""
    report = session.get(Report, report_id)
    assert report is not None
    report.state = "running"
    session.commit()
    started = time.perf_counter()

    def progress(index: int, total: int, title: str) -> None:
        report.progress = {"section": index, "total": total, "title": title}
        session.commit()

    try:
        content, sheet, calls, mode = build_report(
            session,
            code,
            report.territory_id,
            cast(Lang, report.language),
            progress,
            report.model if report.provider != "none" else None,
        )
    except Exception as exc:  # the report must never stay « running »
        report.state = "failed"
        report.error = str(exc)[:500]
        session.commit()
        raise
    report.content = content
    report.fact_sheet = sheet
    report.llm_calls = calls
    report.writing_mode = mode
    report.state = "done" if content["verification"]["ok"] else "blocked"
    report.duration_s = round(time.perf_counter() - started, 1)
    report.finished_at = datetime.now(UTC)
    report.progress = {
        "section": len(content["sections"]),
        "total": len(content["sections"]),
        "title": "",
    }
    session.commit()
    return report


def request_report(
    session: Session, code: str, unit_id: int, lang: Lang, user: str, force: bool = False
) -> tuple[Report, bool]:
    """Return a cached report, or create a pending one. The bool says whether it is cached."""
    settings = get_settings()
    template = load_template(settings.config_dir / "report_templates" / "diagnostic_commune.yaml")
    diagnostic = latest_diagnostic(session, code)
    territory = session.get(Territory, unit_id)
    if territory is None or territory.study_area_id != diagnostic.study_area_id:
        raise LookupError("Unité inconnue pour ce territoire.")
    provider, model = provider_identity()
    key = current_cache_key(diagnostic.result, unit_id, lang, provider, model, template)
    if not force:
        cached = find_cached(session, key)
        if cached is not None:
            return cached, True
    report = Report(
        territory_id=unit_id,
        diagnostic_id=diagnostic.id,
        language=lang,
        provider=provider,
        model=model,
        cache_key=key,
        state="pending",
        status="brouillon",
        progress={},
        content={},
        fact_sheet={},
        requested_by=user,
        history=[{"status": "brouillon", "by": user, "at": datetime.now(UTC).isoformat()}],
    )
    session.add(report)
    session.commit()
    return report, False
