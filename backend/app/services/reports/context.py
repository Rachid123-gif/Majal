"""Loads what a report needs: the latest diagnostic and the unit's identity."""

from typing import Any

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.config_loader import load_territories
from app.models import Diagnostic, StudyArea
from app.services.indicators.engine import MissingInput, load_method
from app.settings import get_settings

LEVEL_TERMS = {
    "arrondissement": {"fr": "arrondissement", "ar": "مقاطعة"},
    "commune": {"fr": "commune", "ar": "جماعة"},
}


def latest_diagnostic(session: Session, code: str) -> Diagnostic:
    territories = load_territories(get_settings().config_dir / "territories")
    if code not in territories:
        raise MissingInput(f"Territoire inconnu : {code}.")
    fingerprint = load_method(territories[code]).fingerprint
    area = session.scalars(select(StudyArea).where(StudyArea.code == code)).one_or_none()
    if area is None:
        raise MissingInput("Données non importées pour ce territoire.")
    diagnostic = session.scalars(
        select(Diagnostic)
        .where(Diagnostic.study_area_id == area.id)
        .order_by(Diagnostic.computed_at.desc())
        .limit(1)
    ).one_or_none()
    if diagnostic is None or diagnostic.method_hash != fingerprint:
        from app.services.indicators.engine import compute_diagnostic

        diagnostic = compute_diagnostic(session, code, author="rapport")
    return diagnostic


def unit_identity(session: Session, unit_id: int) -> dict[str, str]:
    rows = session.execute(
        text(
            """
            WITH RECURSIVE chain AS (
              SELECT id, name_fr, name_ar, level, parent_id, 0 AS depth FROM territories WHERE id = :id
              UNION ALL
              SELECT t.id, t.name_fr, t.name_ar, t.level, t.parent_id, c.depth + 1
              FROM territories t JOIN chain c ON t.id = c.parent_id
            )
            SELECT name_fr, name_ar, level FROM chain ORDER BY depth
            """
        ),
        {"id": unit_id},
    ).all()
    if not rows:
        raise MissingInput("Unité inconnue.")
    name_fr, name_ar, level = rows[0]
    parents = rows[1:]
    term = LEVEL_TERMS.get(level, {"fr": level, "ar": level})
    if level == "arrondissement" and parents:
        description_fr = f"arrondissement de la commune de {parents[0][0]}"
        description_ar = f"مقاطعة تابعة لجماعة {parents[0][1] or parents[0][0]}"
        parents = parents[1:]
    else:
        description_fr = term["fr"]
        description_ar = term["ar"]
    if parents:
        description_fr += f", {parents[0][0]}"
        description_ar += f"، {parents[0][1] or parents[0][0]}"
    return {
        "name_fr": name_fr,
        "name_ar": name_ar or name_fr,
        "description_fr": description_fr,
        "description_ar": description_ar,
    }


def find_unit(diagnostic: dict[str, Any], name: str) -> int:
    for unit in diagnostic["units"]:
        if unit["name_fr"].lower() == name.lower():
            return int(unit["id"])
    raise MissingInput(f"Unité introuvable : {name}.")
