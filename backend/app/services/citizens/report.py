"""What section 7 of the report (« Ce que disent les citoyens ») may say about a unit: counts of
contributions by MAIN theme only (rule of the owner), and whether they are fictitious."""

from collections import Counter
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config_loader.taxonomy import Taxonomy
from app.models import Consultation, Contribution


def unit_citizens(
    session: Session, study_area_id: int, unit_id: int, taxonomy: Taxonomy, top: int = 3
) -> dict[str, Any] | None:
    """None when no consultation was imported for the territory."""
    consultations = session.scalars(
        select(Consultation).where(Consultation.study_area_id == study_area_id)
    ).all()
    if not consultations:
        return None
    ids = [c.id for c in consultations]
    contributions = session.scalars(
        select(Contribution).where(
            Contribution.consultation_id.in_(ids), Contribution.territory_id == unit_id
        )
    ).all()
    counts = Counter(c.themes[0] for c in contributions if c.themes)
    themes = []
    for code, count in counts.most_common(top):
        theme = taxonomy.theme(code)
        if theme is not None and code != "autres":
            themes.append({"code": code, "label": theme.label.model_dump(), "count": count})
    return {
        "total": len(contributions),
        "themes": themes,
        "fictitious": any(c.badge == "fictitious" for c in consultations),
        "too_few": len(contributions) < taxonomy.crossing.min_contributions,
    }
