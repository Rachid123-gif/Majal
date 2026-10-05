"""Global Human Settlement Layer (JRC, European Commission), open data (CC BY 4.0).

- GHS-POP: population grid (3 arc-seconds, ≈ 90 m). Used only to distribute each unit's
  official census population inside the unit (« population carroyée », badge « Estimé »).
- GHS-BUILT-S: built-up surface per cell, from satellite imagery (badge « Ouvert »).
"""

import math
import urllib.request
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
import rasterio
from geoalchemy2.shape import to_shape
from pydantic import BaseModel, ConfigDict, Field, ValidationError
from rasterio.features import geometry_mask
from rasterio.windows import Window, from_bounds
from sqlalchemy import select, text

from app.ingestion.common import ImportContext, ImportFailure, ImportResult, upsert_source
from app.models import Badge, PopulationCell, RawVariable, Territory
from app.settings import get_settings

BASE = "https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/GHSL"
PRODUCTS = {
    "pop": ("GHS_POP_GLOBE_R2023A", "GHS_POP_E{epoch}_GLOBE_R2023A_4326_3ss"),
    "built": ("GHS_BUILT_S_GLOBE_R2023A", "GHS_BUILT_S_E{epoch}_GLOBE_R2023A_4326_3ss"),
}
USER_AGENT = "MAJAL-demonstrateur/0.1 (diagnostic territorial, usage non commercial)"


class GridParams(BaseModel):
    model_config = ConfigDict(extra="ignore")
    population_epoch: int = 2020
    built_up_epochs: list[int] = Field(default_factory=lambda: [2015, 2020], min_length=1)


def tiles_for(bounds: tuple[float, float, float, float]) -> list[tuple[int, int]]:
    """GHSL WGS84 tiles: 10 by 10 degrees, rows from 90°N, columns from 180°W (1-based)."""
    west, south, east, north = bounds
    rows = range(math.floor((90 - north) / 10) + 1, math.floor((90 - south) / 10) + 2)
    cols = range(math.floor((west + 180) / 10) + 1, math.floor((east + 180) / 10) + 2)
    return [(r, c) for r in rows for c in cols]


def _tile_tif(product: str, epoch: int, row: int, col: int, cache: Path) -> Path:
    folder, pattern = PRODUCTS[product]
    name = pattern.format(epoch=epoch)
    stem = f"{name}_V1_0_R{row}_C{col}"
    tif = cache / f"{stem}.tif"
    if tif.exists():
        return tif
    archive = cache / f"{stem}.zip"
    if not archive.exists():
        url = f"{BASE}/{folder}/{name}/V1-0/tiles/{stem}.zip"
        cache.mkdir(parents=True, exist_ok=True)
        request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        try:
            with urllib.request.urlopen(request, timeout=600) as response:
                archive.write_bytes(response.read())
        except OSError as exc:
            raise ImportFailure(
                f"Téléchargement GHSL impossible ({url}) : {exc}. Relancez `make data` plus tard."
            ) from exc
    with zipfile.ZipFile(archive) as zf:
        member = next(n for n in zf.namelist() if n.endswith(".tif"))
        tif.write_bytes(zf.read(member))
    return tif


def _read(tif: Path, bounds: tuple[float, float, float, float]) -> tuple[np.ndarray, Any]:
    with rasterio.open(tif) as src:
        window = from_bounds(*bounds, transform=src.transform).round_offsets().round_lengths()
        window = window.intersection(Window(0, 0, src.width, src.height))
        data = src.read(1, window=window, masked=True).filled(0).astype("float64")
        data[data < 0] = 0
        return data, src.window_transform(window)


def run(ctx: ImportContext) -> ImportResult:
    config = ctx.territory
    try:
        params = GridParams.model_validate(config.sources["grids"].model_dump())
    except ValidationError as exc:
        raise ImportFailure(f"Paramètres de « sources > grids » incorrects : {exc}") from None
    units = ctx.session.scalars(
        select(Territory).where(
            Territory.study_area_id == ctx.study_area.id, Territory.is_analysis_unit
        )
    ).all()
    if not units:
        raise ImportFailure("Importez d'abord les limites (`make data`).")
    shapes = {u.id: to_shape(u.geom) for u in units}
    west = min(s.bounds[0] for s in shapes.values())
    south = min(s.bounds[1] for s in shapes.values())
    east = max(s.bounds[2] for s in shapes.values())
    north = max(s.bounds[3] for s in shapes.values())
    bounds = (west, south, east, north)
    tiles = tiles_for(bounds)
    if len(tiles) != 1:
        raise ImportFailure(
            "Le territoire chevauche plusieurs tuiles GHSL : cas non encore pris en charge."
        )
    row, col = tiles[0]
    cache = get_settings().data_dir / "raw" / "ghsl"
    now = datetime.now(UTC)

    census: dict[int, float] = dict(
        ctx.session.execute(
            text(
                "SELECT territory_id, value FROM raw_variables WHERE code = 'population' "
                "AND year = 2024 AND territory_id = ANY(:ids)"
            ),
            {"ids": list(shapes)},
        ).all()
    )

    # ---- population grid, rescaled to the official totals
    pop, transform = _read(_tile_tif("pop", params.population_epoch, row, col, cache), bounds)
    upsert_source(  # registered for traceability (cells carry the « Estimé » badge)
        ctx.session,
        f"ghsl_pop:{config.code}",
        name=f"JRC GHSL — GHS-POP R2023A, époque {params.population_epoch} (3″)",
        producer="Commission européenne, Centre commun de recherche (JRC)",
        url="https://human-settlement.emergency.copernicus.eu/download.php?ds=pop",
        license="CC BY 4.0",
        badge=Badge.estimated,
        retrieved_at=now,
        published_at=datetime(2023, 1, 1, tzinfo=UTC),
        notes="Répartition de la population à l'intérieur des unités, recalée sur les totaux "
        "officiels du RGPH 2024 (méthode dasymétrique simple).",
    )
    ctx.session.execute(
        text("DELETE FROM population_cells WHERE study_area_id = :sa"), {"sa": ctx.study_area.id}
    )
    xs = transform.c + (np.arange(pop.shape[1]) + 0.5) * transform.a
    ys = transform.f + (np.arange(pop.shape[0]) + 0.5) * transform.e
    cells: list[dict[str, Any]] = []
    warnings: list[str] = []
    for unit_id, shape in shapes.items():
        inside = geometry_mask([shape], out_shape=pop.shape, transform=transform, invert=True)
        values = np.where(inside, pop, 0)
        total = float(values.sum())
        official = census.get(unit_id)
        if total <= 0:
            warnings.append(f"Aucune population dans la grille GHSL pour l'unité {unit_id}.")
            continue
        factor = (official / total) if official else 1.0
        if not official:
            warnings.append(
                f"Population officielle absente : grille non recalée (unité {unit_id})."
            )
        for i, j in zip(*np.nonzero(values), strict=True):
            cells.append(
                {
                    "study_area_id": ctx.study_area.id,
                    "territory_id": unit_id,
                    "geom": f"SRID=4326;POINT({xs[j]:.6f} {ys[i]:.6f})",
                    "population": float(values[i, j]) * factor,
                    "grid_population": float(values[i, j]),
                }
            )
    for start in range(0, len(cells), 5000):
        ctx.session.execute(PopulationCell.__table__.insert(), cells[start : start + 5000])  # type: ignore[attr-defined]

    # ---- built-up surface per unit and epoch
    built_source = upsert_source(
        ctx.session,
        f"ghsl_built:{config.code}",
        name="JRC GHSL — GHS-BUILT-S R2023A (3″)",
        producer="Commission européenne, Centre commun de recherche (JRC)",
        url="https://human-settlement.emergency.copernicus.eu/download.php?ds=bu",
        license="CC BY 4.0",
        badge=Badge.open,
        retrieved_at=now,
        published_at=datetime(2023, 1, 1, tzinfo=UTC),
        notes="Surface bâtie par cellule, issue de l'imagerie satellite (Sentinel-2, Landsat).",
    )
    rows: list[dict[str, Any]] = []
    for epoch in params.built_up_epochs:
        built, built_transform = _read(_tile_tif("built", epoch, row, col, cache), bounds)
        for unit_id, shape in shapes.items():
            inside = geometry_mask(
                [shape], out_shape=built.shape, transform=built_transform, invert=True
            )
            area_km2 = float(np.where(inside, built, 0).sum()) / 1e6  # values are m² per cell
            rows.append(
                {
                    "territory_id": unit_id,
                    "code": "built_up_km2",
                    "year": epoch,
                    "value": area_km2,
                    "unit": "km²",
                    "source_id": built_source.id,
                    "badge": Badge.open,
                    "method": "derived",
                }
            )
    ctx.session.execute(
        text("DELETE FROM raw_variables WHERE source_id = :src AND territory_id = ANY(:ids)"),
        {"src": built_source.id, "ids": list(shapes)},
    )
    ctx.session.execute(RawVariable.__table__.insert(), rows)  # type: ignore[attr-defined]

    epochs = ", ".join(str(e) for e in params.built_up_epochs)
    summary = (
        f"Grilles GHSL : {len(cells)} cellules de population recalées sur le recensement, "
        f"surface bâtie {epochs} pour {len(shapes)} unités."
    )
    return ImportResult(
        summary, {"cells": len(cells)}, warnings, str(cache), len(cells) + len(rows)
    )
