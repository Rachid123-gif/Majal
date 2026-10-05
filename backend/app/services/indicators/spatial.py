"""Spatial inputs computed in PostGIS from facilities and the population grid.

Distances are measured on the ellipsoid (geography). A degree-based bounding box is used
first so the spatial index can be used, then the exact distance is checked.
"""

from sqlalchemy import text
from sqlalchemy.orm import Session

# Conservative degrees per metre at Moroccan latitudes (cos 36° ≈ 0.81).
DEG_PER_M = 1 / 85000


def proximity_share(
    session: Session,
    study_area_id: int,
    needs: list[list[str]],
    distance_m: float,
    min_area_m2: float | None = None,
) -> dict[int, tuple[float, float]]:
    """Per unit: (population covered by every need within distance, total population)."""
    params: dict[str, object] = {
        "sa": study_area_id,
        "d": distance_m,
        "deg": distance_m * DEG_PER_M,
    }
    conditions = []
    for index, categories in enumerate(needs):
        params[f"cats{index}"] = categories
        area = ""
        if min_area_m2 is not None:
            params["min_area"] = min_area_m2
            area = "AND f.area_m2 >= :min_area"
        conditions.append(
            f"""EXISTS (SELECT 1 FROM facilities f
                 WHERE f.study_area_id = :sa AND f.category = ANY(:cats{index}) {area}
                   AND f.geom && ST_Expand(c.geom, :deg)
                   AND ST_DWithin(f.geom::geography, c.geom::geography, :d))"""
        )
    rows = session.execute(
        text(
            f"""
            SELECT c.territory_id,
                   sum(c.population) FILTER (WHERE {" AND ".join(conditions)}) AS covered,
                   sum(c.population) AS total
            FROM population_cells c
            WHERE c.study_area_id = :sa
            GROUP BY c.territory_id
            """
        ),
        params,
    ).all()
    return {r[0]: (float(r[1] or 0.0), float(r[2] or 0.0)) for r in rows}


def distance_mean(session: Session, study_area_id: int, categories: list[str]) -> dict[int, float]:
    """Per unit: population-weighted mean distance (km) to the nearest facility."""
    rows = session.execute(
        text(
            """
            SELECT c.territory_id, sum(c.population * d.dist) / NULLIF(sum(c.population), 0)
            FROM population_cells c
            CROSS JOIN LATERAL (
                SELECT ST_Distance(f.geom::geography, c.geom::geography) AS dist
                FROM facilities f
                WHERE f.study_area_id = :sa AND f.category = ANY(:cats)
                ORDER BY f.geom <-> c.geom
                LIMIT 1
            ) d
            WHERE c.study_area_id = :sa
            GROUP BY c.territory_id
            """
        ),
        {"sa": study_area_id, "cats": categories},
    ).all()
    return {r[0]: float(r[1]) / 1000 for r in rows if r[1] is not None}


def facility_area(session: Session, study_area_id: int, categories: list[str]) -> dict[int, float]:
    """Per unit: total area (m²) of the polygon facilities of these categories."""
    rows = session.execute(
        text(
            """
            SELECT territory_id, sum(area_m2) FROM facilities
            WHERE study_area_id = :sa AND category = ANY(:cats) AND area_m2 IS NOT NULL
            GROUP BY territory_id
            """
        ),
        {"sa": study_area_id, "cats": categories},
    ).all()
    return {r[0]: float(r[1]) for r in rows if r[0] is not None}


def facility_counts(session: Session, study_area_id: int) -> dict[tuple[int, str], int]:
    rows = session.execute(
        text(
            "SELECT territory_id, category, count(*) FROM facilities "
            "WHERE study_area_id = :sa AND territory_id IS NOT NULL GROUP BY 1, 2"
        ),
        {"sa": study_area_id},
    ).all()
    return {(r[0], r[1]): int(r[2]) for r in rows}
