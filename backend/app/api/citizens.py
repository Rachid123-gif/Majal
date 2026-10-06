"""Citizen listening (stage 4): dashboard, verbatims, unit summary, import of contributions."""

from typing import Annotated, Any, Literal

import yaml
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_engine
from app.models import Consultation, Contribution, StudyArea, Territory
from app.security import Account, Role, require_account
from app.services.citizens import evaluate, pipeline, review, stats
from app.services.citizens.fallback import cached_analysis_config
from app.services.citizens.jobs import enqueue
from app.services.indicators.engine import MissingInput
from app.services.reports.context import latest_diagnostic
from app.settings import REPO_ROOT, get_settings

router = APIRouter(tags=["citizens"])
MAX_UPLOAD = 5 * 1024 * 1024


def _area(session: Session, code: str) -> StudyArea:
    area = session.scalars(select(StudyArea).where(StudyArea.code == code)).one_or_none()
    if area is None:
        raise HTTPException(status_code=404, detail="Territoire inconnu ou non importé.")
    return area


def _units(session: Session, code: str, area: StudyArea) -> dict[int, dict[str, Any]]:
    population: dict[int, float] = {}
    try:
        for unit in latest_diagnostic(session, code).result["units"]:
            value = (unit["values"].get("DEM_POP") or {}).get("value")
            if value:
                population[unit["id"]] = value
    except MissingInput:
        pass
    return {
        t.id: {"name_fr": t.name_fr, "name_ar": t.name_ar, "population": population.get(t.id)}
        for t in session.scalars(
            select(Territory).where(Territory.study_area_id == area.id, Territory.is_analysis_unit)
        )
    }


Scale = Literal["unit", "commune"]


def _groups(
    session: Session, area: StudyArea, units: dict[int, dict[str, Any]], scale: Scale
) -> tuple[dict[int, dict[str, Any]], dict[int, int] | None]:
    """Rows of the chosen scale, and the map unit → row. « commune »: arrondissements are
    grouped under their commune (Rabat, Salé); other analysis units stay as they are."""
    if scale == "unit":
        return units, None
    territories = {
        t.id: t
        for t in session.scalars(select(Territory).where(Territory.study_area_id == area.id))
    }
    group_of: dict[int, int] = {}
    groups: dict[int, dict[str, Any]] = {}
    for unit_id, info in units.items():
        territory = territories[unit_id]
        parent = territories.get(territory.parent_id) if territory.parent_id else None
        gid = parent.id if territory.level == "arrondissement" and parent else unit_id
        group_of[unit_id] = gid
        target = parent if gid != unit_id and parent else territory
        row = groups.setdefault(
            gid,
            {"name_fr": target.name_fr, "name_ar": target.name_ar, "population": 0, "members": []},
        )
        row["members"].append(unit_id)
        row["population"] = (row["population"] or 0) + (info.get("population") or 0)
    return groups, group_of


def _contributions(
    session: Session, area: StudyArea
) -> tuple[list[Consultation], list[Contribution]]:
    consultations = list(
        session.scalars(select(Consultation).where(Consultation.study_area_id == area.id)).all()
    )
    ids = [c.id for c in consultations]
    contributions = (
        list(
            session.scalars(select(Contribution).where(Contribution.consultation_id.in_(ids))).all()
        )
        if ids
        else []
    )
    return consultations, contributions


def _evaluation(
    code: str, contributions: list[Contribution], units: dict[int, dict[str, Any]]
) -> dict[str, Any]:
    fictitious = get_settings().data_dir / "fictif" / code / "contributions.yaml"
    out: dict[str, Any] = {"provisional": None, "reference": None, "anonymisation": None}
    if fictitious.exists():
        ids = {info["name_fr"]: uid for uid, info in units.items()}
        truth = evaluate.provisional_truth(fictitious, ids)
        result = evaluate.score(contributions, truth)
        if result["n"]:
            out["provisional"] = {
                **result,
                "base": {k: v.format(n=result["n"]) for k, v in evaluate.PROVISIONAL_BASE.items()},
            }
        # Anonymisation: share of the fictitious traps that are masked in the stored texts.
        data = yaml.safe_load(fictitious.read_text(encoding="utf-8"))["contributions"]
        by_id = {c.external_id: c for c in contributions}
        traps = masked = 0
        for item in data:
            stored = by_id.get(item["id"])
            if stored is None or not item.get("pii"):
                continue
            spans = [
                stored.original_text[i["start"] : i["end"]]
                for i in stored.anonymization.get("items", [])
            ]
            traps += 1
            masked += all(
                any(p["value"] in s or s in p["value"] for s in spans) for p in item["pii"]
            )
        if traps:
            out["anonymisation"] = {
                "rate": masked / traps,
                "masked": masked,
                "traps": traps,
                "base": {k: v.format(n=traps) for k, v in evaluate.ANONYMISATION_BASE.items()},
            }
    sheet = REPO_ROOT / "docs" / "evaluation" / "annotation-professeur.xlsx"
    reference_truth = evaluate.reference_truth(sheet, {"amazigh_latin"})
    if reference_truth:
        result = evaluate.score(contributions, reference_truth)
        if result["n"]:
            kind = evaluate.annotator_kind(sheet)
            bases = (
                evaluate.SECOND_MODEL_BASE if kind == "second_model" else evaluate.REFERENCE_BASE
            )
            out["reference"] = {
                **result,
                "kind": kind,
                "title": evaluate.TITLES[kind],
                "note": evaluate.SECOND_MODEL_NOTE if kind == "second_model" else None,
                "base": {k: v.format(n=result["n"]) for k, v in bases.items()},
            }
    out["human"] = review.human_evaluation(contributions)
    return out


def _review_rules() -> Any:
    return cached_analysis_config(get_settings().config_dir / "citizens" / "analyse.yaml").review


def _require_reviewer(account: Account) -> None:
    if not ({Role.referent, Role.admin} & set(account.roles)):
        raise HTTPException(
            status_code=403,
            detail="La vérification est réservée aux comptes professeur et administrateur.",
        )


@router.get("/api/territories/{code}/citizens")
def dashboard(
    code: str,
    _: Annotated[Account, Depends(require_account)],
    secondary: bool = False,
    theme: str | None = None,
    unit: int | None = None,
    language: str | None = None,
    tonality: str | None = None,
    scale: Scale = "unit",
) -> dict[str, Any]:
    with Session(get_engine()) as session:
        area = _area(session, code)
        taxonomy = pipeline.taxonomy_for(area)
        consultations, contributions = _contributions(session, area)
        units, group_of = _groups(session, area, _units(session, code, area), scale)
        selected = stats.filtered(
            contributions, theme, unit, language, tonality, secondary, group_of
        )
        fictitious = any(c.badge == "fictitious" for c in consultations)
        return {
            "territory": code,
            "taxonomy": {
                "label": taxonomy.label.model_dump(),
                "themes": [
                    {"code": t.code, "label": t.label.model_dump(), "indicators": t.indicators}
                    for t in taxonomy.themes
                ],
                "tonalities": {k: v.model_dump() for k, v in taxonomy.tonalities.items()},
            },
            "languages": {
                k: v.model_dump()
                for k, v in cached_analysis_config(
                    get_settings().config_dir / "citizens" / "analyse.yaml"
                ).languages.items()
            },
            "consultations": [
                {"id": c.id, "code": c.code, "title": c.title, "badge": c.badge}
                for c in consultations
            ],
            "fictitious": fictitious,
            "banner": stats.FICTITIOUS_BANNER if fictitious else None,
            "filters": {"theme": theme, "unit": unit, "language": language, "tonality": tonality},
            "scale": scale,
            "summary": stats.summary(selected, taxonomy, units, secondary, group_of),
            "evaluation": _evaluation(code, contributions, units),
            "review": {
                "pending": sum(1 for c in contributions if review.pending(c, _review_rules())),
                "validated": sum(1 for c in contributions if c.validated_by),
            },
        }


@router.get("/api/territories/{code}/citizens/verbatims")
def verbatims(
    code: str,
    _: Annotated[Account, Depends(require_account)],
    theme: Annotated[list[str] | None, Query()] = None,
    unit: int | None = None,
    language: str | None = None,
    tonality: str | None = None,
) -> dict[str, list[dict[str, Any]]]:
    with Session(get_engine()) as session:
        area = _area(session, code)
        taxonomy = pipeline.taxonomy_for(area)
        contributions = _contributions(session, area)[1]
        units = _units(session, code, area)
        selected = stats.filtered(contributions, None, unit, language, tonality)
        codes = theme or [t.code for t in taxonomy.themes]
        return {c: rows for c in codes if (rows := stats.verbatims(selected, c, units))}


@router.get("/api/territories/{code}/units/{unit_id}/citizens")
def unit_summary(
    code: str,
    unit_id: int,
    _: Annotated[Account, Depends(require_account)],
    secondary: bool = False,
) -> dict[str, Any]:
    with Session(get_engine()) as session:
        area = _area(session, code)
        taxonomy = pipeline.taxonomy_for(area)
        consultations, contributions = _contributions(session, area)
        units = _units(session, code, area)
        selected = stats.filtered(contributions, unit=unit_id, secondary=secondary)
        summary = stats.summary(
            selected, taxonomy, {unit_id: units[unit_id]} if unit_id in units else {}, secondary
        )
        top = [row["code"] for row in summary["themes"][:2]]
        fictitious = any(c.badge == "fictitious" for c in consultations)
        return {
            "fictitious": fictitious,
            "banner": stats.FICTITIOUS_BANNER if fictitious else None,
            "summary": summary,
            "verbatims": [
                v for code_ in top for v in stats.verbatims(selected, code_, units, limit=1)
            ],
        }


@router.post("/api/territories/{code}/citizens/import")
async def import_file(
    code: str,
    request: Request,
    account: Annotated[Account, Depends(require_account)],
    filename: str,
    title: str = "Consultation importée",
) -> dict[str, Any]:
    if not ({Role.referent, Role.admin} & set(account.roles)):
        raise HTTPException(
            status_code=403,
            detail="L'import est réservé aux comptes professeur et administrateur.",
        )
    content = await request.body()
    if len(content) > MAX_UPLOAD:
        raise HTTPException(status_code=413, detail="Fichier trop volumineux (5 Mo au plus).")
    try:
        rows = pipeline.read_rows(filename, content)
    except (pipeline.ImportError_, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from None
    with Session(get_engine()) as session:
        area = _area(session, code)
        slug = "".join(ch if ch.isalnum() else "-" for ch in filename.rsplit(".", 1)[0].casefold())
        consultation = pipeline.import_contributions(
            session,
            area,
            f"import-{slug}"[:80],
            title,
            "official",
            rows,
            filename,
            account.username,
        )
        mode = enqueue(consultation.id)
        return {"consultation_id": consultation.id, "rows": len(rows), "processing": mode}


@router.get("/api/citizens/consultations/{consultation_id}/progress")
def progress(
    consultation_id: int, _: Annotated[Account, Depends(require_account)]
) -> dict[str, int]:
    with Session(get_engine()) as session:
        rows = session.scalars(
            select(Contribution).where(Contribution.consultation_id == consultation_id)
        ).all()
        return {
            "total": len(rows),
            "analysed": sum(1 for c in rows if c.analysis and c.analysis.get("mode")),
        }


@router.get("/api/territories/{code}/units/{unit_id}/crossing")
def unit_crossing(
    code: str,
    unit_id: int,
    account: Annotated[Account, Depends(require_account)],
    secondary: bool = False,
    scale: Scale = "unit",
) -> dict[str, Any]:
    """Citizens / data crossing for one unit, or one commune (`scale=commune`, `unit_id` = the
    commune), main theme only unless `secondary`."""
    with Session(get_engine()) as session:
        area = _area(session, code)
        taxonomy = pipeline.taxonomy_for(area)
        consultations, contributions = _contributions(session, area)
        try:
            diagnostic = latest_diagnostic(session, code).result
        except MissingInput as exc:
            raise HTTPException(status_code=409, detail=exc.reason) from None
        units, group_of = _groups(session, area, _units(session, code, area), scale)
        row = units.get(unit_id)
        if row is None:
            raise HTTPException(status_code=404, detail="Unité inconnue pour ce territoire.")
        member_ids = row.get("members", [unit_id])
        by_id = {u["id"]: u for u in diagnostic["units"]}
        members = [
            {
                "name_fr": by_id[m]["name_fr"],
                "name_ar": by_id[m].get("name_ar"),
                "population": (by_id[m]["values"].get("DEM_POP") or {}).get("value"),
                "values": by_id[m]["values"],
            }
            for m in member_ids
            if m in by_id
        ]
        if not members:
            raise HTTPException(status_code=404, detail="Unité sans diagnostic.")
        result = stats.crossing(
            stats.filtered(contributions, unit=unit_id, group_of=group_of),
            taxonomy,
            members[0]["values"],
            {i["code"]: i for i in diagnostic["indicators"]},
            diagnostic["evaluation"]["statuses"],
            secondary,
            members,
        )
        fictitious = any(c.badge == "fictitious" for c in consultations)
        return {
            "unit": {"id": unit_id, "name_fr": row["name_fr"], "name_ar": row.get("name_ar")},
            "scale": scale,
            "members": [m["name_fr"] for m in members],
            "fictitious": fictitious,
            "banner": stats.FICTITIOUS_BANNER if fictitious else None,
            "evaluation_label": diagnostic["evaluation"]["label"],
            **result,
        }


REASONS = {
    "theme": {
        "fr": "L'IA et les mots-clés ne donnent pas le même thème principal",
        "ar": "الذكاء الاصطناعي والكلمات المفتاحية لا يعطيان نفس الموضوع الرئيسي",
    },
    "theme_unconfirmed": {
        "fr": "Thème de l'IA non confirmé par les mots-clés",
        "ar": "موضوع الذكاء الاصطناعي غير مؤكد بالكلمات المفتاحية",
    },
    "language": {"fr": "Langue incertaine", "ar": "لغة غير مؤكدة"},
}


def _review_item(c: Contribution, units: dict[int, dict[str, Any]]) -> dict[str, Any]:
    tool = review.proposed(c)
    keywords = (c.analysis or {}).get("keywords") or {}
    unit_of = units.get

    def unit(uid: int | None) -> dict[str, Any] | None:
        info = unit_of(uid) if uid is not None else None
        return (
            {"id": uid, "name_fr": info["name_fr"], "name_ar": info.get("name_ar")}
            if info
            else None
        )

    return {
        "id": c.id,
        "external_id": c.external_id,
        "original": c.anonymized_text,  # anonymised: the raw text is never shown
        "translation_fr": c.translation_fr if c.language != "fr" else None,
        "translation_note": stats.TRANSLATION_NOTE if c.language != "fr" else None,
        "language": c.language,
        "language_note": stats.AMAZIGH_NOTE if c.language == "amazigh_latin" else None,
        "reasons": [{"code": r, "label": REASONS[r]} for r in review.reasons(c, _review_rules())],
        "proposal": {
            "themes": list(tool.themes or []),
            "tonality": tool.tonality,
            "unit": unit(tool.territory_id),
            "place": tool.place_text,
        },
        "keywords": {"themes": keywords.get("themes"), "tonality": keywords.get("tonality")},
        "current": {
            "themes": list(c.themes or []),
            "tonality": c.tonality,
            "unit": unit(c.territory_id),
        },
        "validated_by": c.validated_by,
        "validated_at": c.validated_at.isoformat() if c.validated_at else None,
        "badge": c.badge,
    }


@router.get("/api/territories/{code}/citizens/review")
def review_queue(
    code: str,
    account: Annotated[Account, Depends(require_account)],
    status: Literal["pending", "validated"] = "pending",
) -> dict[str, Any]:
    """« À vérifier »: the tool's proposals to check (or those already validated)."""
    _require_reviewer(account)
    with Session(get_engine()) as session:
        area = _area(session, code)
        taxonomy = pipeline.taxonomy_for(area)
        consultations, contributions = _contributions(session, area)
        units = _units(session, code, area)
        rules = _review_rules()
        if status == "pending":
            chosen = [c for c in contributions if review.pending(c, rules)]
            chosen.sort(key=lambda c: c.external_id)
        else:
            chosen = [c for c in contributions if c.validated_by]
            chosen.sort(key=lambda c: c.validated_at or c.created_at, reverse=True)
        fictitious = any(c.badge == "fictitious" for c in consultations)
        return {
            "status": status,
            "fictitious": fictitious,
            "banner": stats.FICTITIOUS_BANNER if fictitious else None,
            "counts": {
                "pending": sum(1 for c in contributions if review.pending(c, rules)),
                "validated": sum(1 for c in contributions if c.validated_by),
            },
            "themes": [{"code": t.code, "label": t.label.model_dump()} for t in taxonomy.themes],
            "tonalities": {k: v.model_dump() for k, v in taxonomy.tonalities.items()},
            "units": sorted(
                (
                    {"id": uid, "name_fr": info["name_fr"], "name_ar": info.get("name_ar")}
                    for uid, info in units.items()
                ),
                key=lambda u: str(u["name_fr"]),
            ),
            "items": [_review_item(c, units) for c in chosen],
        }


class ReviewChoice(BaseModel):
    themes: list[str] = Field(min_length=1, max_length=2)
    tonality: str
    territory_id: int | None = None


@router.post("/api/territories/{code}/citizens/contributions/{contribution_id}/review")
def review_contribution(
    code: str,
    contribution_id: int,
    choice: ReviewChoice,
    account: Annotated[Account, Depends(require_account)],
) -> dict[str, Any]:
    """Records the human choice; it replaces the tool's proposal everywhere."""
    _require_reviewer(account)
    with Session(get_engine()) as session:
        area = _area(session, code)
        taxonomy = pipeline.taxonomy_for(area)
        contribution = session.get(Contribution, contribution_id)
        consultation = (
            session.get(Consultation, contribution.consultation_id) if contribution else None
        )
        if contribution is None or consultation is None or consultation.study_area_id != area.id:
            raise HTTPException(status_code=404, detail="Contribution inconnue pour ce territoire.")
        codes = {t.code for t in taxonomy.themes}
        if any(t not in codes for t in choice.themes):
            raise HTTPException(status_code=422, detail="Thème inconnu dans la taxonomie.")
        if choice.tonality not in taxonomy.tonalities:
            raise HTTPException(status_code=422, detail="Tonalité inconnue.")
        units = _units(session, code, area)
        if choice.territory_id is not None and choice.territory_id not in units:
            raise HTTPException(status_code=422, detail="Unité inconnue pour ce territoire.")
        review.validate(
            contribution, choice.themes, choice.tonality, choice.territory_id, account.username
        )
        session.commit()
        return _review_item(contribution, units)
