"""Official census data from the HCP (RGPH 2014 and 2024), badge « Officiel ».

- Legal population files (2014, 2024): population, households, official geographic codes and
  official Arabic names, down to arrondissements.
- RGPH 2024 dissemination platform: commune-level indicators (unemployment, illiteracy,
  housing conditions…), listed in config/mappings/hcp_rgph.yaml.
"""

import json
import re
import urllib.request
from dataclasses import dataclass
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

import openpyxl
from pydantic import BaseModel, ConfigDict, Field, ValidationError
from sqlalchemy import select, text

from app.config_loader.territory import Slug, StrictModel, Text
from app.config_loader.validation import load_model
from app.ingestion.common import (
    ImportContext,
    ImportFailure,
    ImportResult,
    normalize,
    upsert_source,
)
from app.models import Badge, RawVariable, Territory
from app.settings import get_settings

USER_AGENT = "MAJAL-demonstrateur/0.1 (diagnostic territorial, usage non commercial)"
NAME_PREFIX = re.compile(
    r"^(prefecture|province|commune|arrondissement|municipalite|mun)\s+(de\s+|d\s+|du\s+)?"
)
AR_PREFIX = re.compile(r"^(جماعة|مقاطعة)\s+")


# ---------- mapping file ----------


class LegalFile(StrictModel):
    year: int
    url: Text
    page: Text
    file: Text
    title: Text
    published: date


class PlatformDataset(StrictModel):
    id: int
    indicator_column: Text


class PlatformVariable(StrictModel):
    code: Slug
    dataset: Slug
    indicator: Text
    sex: Text = "Ensemble"
    unit: Text


class Platform(StrictModel):
    title: Text
    url: Text
    page: Text
    year: int
    datasets: dict[Slug, PlatformDataset]
    variables: list[PlatformVariable] = Field(min_length=1)


class HcpMapping(StrictModel):
    mapping_version: Text
    legal_population: list[LegalFile] = Field(min_length=1)
    platform: Platform


class CensusParams(BaseModel):
    model_config = ConfigDict(extra="ignore")
    mapping: str


# ---------- HCP files ----------


@dataclass(frozen=True)
class HcpRow:
    code: str  # digits only
    name_fr: str
    name_ar: str
    population: int | None
    households: int | None

    @property
    def key(self) -> str:
        """Province (3) + cercle (2) + commune (2) digits: stable between 2014 and 2024."""
        return self.code[-7:]


def _download(url: str, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            target.write_bytes(response.read())
    except OSError as exc:
        raise ImportFailure(
            f"Téléchargement impossible depuis le site du HCP ({url}) : {exc}. "
            f"Vous pouvez placer le fichier vous-même dans {target}."
        ) from exc


def _int(value: Any) -> int | None:
    return int(value) if isinstance(value, int | float) else None


def read_legal_2024(path: Path) -> list[HcpRow]:
    """Columns: name FR, Moroccans, foreigners, population, households, name AR, code."""
    sheet = openpyxl.load_workbook(path, read_only=True).worksheets[0]
    rows: dict[str, HcpRow] = {}
    for values in sheet.iter_rows(values_only=True):
        if len(values) < 7 or values[6] is None or not isinstance(values[0], str):
            continue
        name = values[0].strip()
        if "milieu" in name.lower() or name.lower().startswith("dont"):
            continue
        code = re.sub(r"\D", "", str(values[6]))
        rows.setdefault(
            code, HcpRow(code, name, str(values[5] or "").strip(), _int(values[3]), _int(values[4]))
        )
    return list(rows.values())


def read_legal_2014(path: Path) -> list[HcpRow]:
    """Sheet « Communes »: code, name FR, households, population, foreigners, Moroccans, name AR."""
    workbook = openpyxl.load_workbook(path, read_only=True)
    sheet = workbook["Communes"] if "Communes" in workbook.sheetnames else workbook.worksheets[-1]
    rows: dict[str, HcpRow] = {}
    for values in sheet.iter_rows(values_only=True):
        if len(values) < 7 or not isinstance(values[0], str) or not re.match(r"^\d", values[0]):
            continue
        name = str(values[1] or "").strip()
        if name.lower().startswith("dont"):
            continue
        code = re.sub(r"\D", "", values[0])
        rows.setdefault(
            code, HcpRow(code, name, str(values[6] or "").strip(), _int(values[3]), _int(values[2]))
        )
    return list(rows.values())


def _key_name(name: str) -> str:
    cleaned = re.sub(r"\((mun|arrond)\.?\)", "", name, flags=re.IGNORECASE)
    cleaned = cleaned.replace("Préfecture:", "Préfecture de").replace("Province:", "Province de")
    return NAME_PREFIX.sub("", normalize(cleaned))


def match_units(
    units: list[tuple[int, str, str]], rows: list[HcpRow]
) -> tuple[dict[int, HcpRow], list[str]]:
    """Match (id, level, name) units to 2024 HCP rows, by name within their prefecture.

    Top-level units (prefectures, provinces) are matched first; communes and arrondissements
    are then searched only among the rows of their prefecture.
    """
    matched: dict[int, HcpRow] = {}
    tops = [r for r in rows if len(r.code) == 4]
    for unit_id, level, name in units:
        if level in ("prefecture", "province"):
            row = next((r for r in tops if _key_name(r.name_fr) == _key_name(name)), None)
            if row:
                matched[unit_id] = row
    prefixes = tuple(r.code for r in matched.values())
    candidates = [r for r in rows if len(r.code) in (7, 8) and r.code.startswith(prefixes)]
    missing = []
    for unit_id, level, name in units:
        if level in ("prefecture", "province"):
            if unit_id not in matched:
                missing.append(name)
            continue
        found = [r for r in candidates if _key_name(r.name_fr) == _key_name(name)]
        if len(found) == 1:
            matched[unit_id] = found[0]
        else:
            missing.append(name)
    return matched, missing


# ---------- platform ----------


def fetch_platform(
    platform: Platform, dataset: PlatformDataset, provinces: list[str], cache: Path, refresh: bool
) -> list[dict[str, Any]]:
    columns = [
        "code_zone",
        "code_prov",
        "libelle_commune",
        "Sexe",
        "Milieu",
        dataset.indicator_column,
        "Value(valeur indicateur)",
    ]
    query = {
        "datasource": {"id": dataset.id, "type": "table"},
        "force": False,
        "queries": [
            {
                "columns": columns,
                "filters": [{"col": "code_prov", "op": "IN", "val": provinces}],
                "row_limit": 200000,
                "orderby": [],
            }
        ],
        "result_format": "json",
        "result_type": "full",
    }
    if cache.exists() and not refresh:
        cached = json.loads(cache.read_text(encoding="utf-8"))
        if cached.get("query") == query:
            return list(cached["rows"])
    request = urllib.request.Request(
        platform.url,
        data=json.dumps(query).encode(),
        headers={"Content-Type": "application/json", "User-Agent": USER_AGENT},
    )
    try:
        with urllib.request.urlopen(request, timeout=180) as response:
            rows = json.load(response)["result"][0]["data"]
    except (OSError, KeyError, ValueError) as exc:
        raise ImportFailure(
            f"La plateforme de résultats du HCP n'a pas répondu ({exc.__class__.__name__}). "
            "Vérifiez la connexion internet et relancez `make data`."
        ) from exc
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(
        json.dumps(
            {"retrieved_at": datetime.now(UTC).isoformat(), "query": query, "rows": rows},
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    return list(rows)


# ---------- importer ----------


def run(ctx: ImportContext) -> ImportResult:
    config = ctx.territory
    settings = get_settings()
    try:
        params = CensusParams.model_validate(config.sources["census"].model_dump())
    except ValidationError as exc:
        raise ImportFailure(f"Paramètres de « sources > census » incorrects : {exc}") from None
    mapping = load_model(settings.config_dir.parent / params.mapping, HcpMapping)
    raw_root = settings.data_dir / "raw"

    legal: dict[int, list[HcpRow]] = {}
    sources: dict[int, int] = {}
    for item in mapping.legal_population:
        path = raw_root / item.file
        if not path.exists() or ctx.refresh:
            _download(item.url, path)
        legal[item.year] = read_legal_2024(path) if item.year >= 2024 else read_legal_2014(path)
        sources[item.year] = upsert_source(
            ctx.session,
            f"hcp_legal_{item.year}",
            name=f"HCP — {item.title}",
            producer="Haut-Commissariat au Plan",
            url=item.page,
            license="Publication officielle",
            badge=Badge.official,
            retrieved_at=datetime.fromtimestamp(path.stat().st_mtime, UTC),
            published_at=datetime.combine(item.published, datetime.min.time(), UTC),
            notes=f"Fichier : {item.url}",
        ).id
    latest = max(legal)

    territories = ctx.session.scalars(
        select(Territory).where(Territory.study_area_id == ctx.study_area.id)
    ).all()
    matched, missing = match_units([(t.id, t.level, t.name_fr) for t in territories], legal[latest])
    analysis_names = {t.name_fr for t in territories if t.is_analysis_unit}
    warnings = [
        f"Unité absente des tableaux du HCP : {name}." for name in missing if name in analysis_names
    ]
    by_key = {year: {r.key: r for r in rows} for year, rows in legal.items()}

    values: list[dict[str, Any]] = []

    def add(territory_id: int, code: str, year: int, value: float, unit: str, source: int) -> None:
        values.append(
            {
                "territory_id": territory_id,
                "code": code,
                "year": year,
                "value": value,
                "unit": unit,
                "source_id": source,
                "badge": Badge.official,
                "method": "direct",
            }
        )

    for territory in territories:
        row = matched.get(territory.id)
        if row is None:
            continue
        territory.official_code = row.code
        meta = dict(territory.source_meta or {})
        meta.setdefault("osm_name_ar", territory.name_ar)
        meta["official_name_fr"] = row.name_fr
        territory.source_meta = meta
        if row.name_ar and territory.level not in ("prefecture", "province"):
            territory.name_ar = AR_PREFIX.sub("", row.name_ar)
        for year, rows_by_key in by_key.items():
            same = rows_by_key.get(row.key) if year != latest else row
            if same is None and year != latest:
                # Codes can change between censuses (new cercles): fall back to the name,
                # within the same province.
                same = next(
                    (
                        r
                        for r in legal[year]
                        if r.key[:3] == row.key[:3]
                        and len(r.code) >= 9
                        and _key_name(r.name_fr) == _key_name(row.name_fr)
                    ),
                    None,
                )
            if same is None or same.population is None:
                if year != latest and territory.is_analysis_unit:
                    warnings.append(f"Population {year} introuvable pour {territory.name_fr}.")
                continue
            add(territory.id, "population", year, same.population, "habitants", sources[year])
            if same.households is not None:
                add(territory.id, "households", year, same.households, "ménages", sources[year])

    # RGPH 2024 platform indicators, matched on the official code.
    platform = mapping.platform
    province_codes = sorted({f"MA-0{r.code[:4]}" for r in matched.values()})
    platform_source = upsert_source(
        ctx.session,
        "hcp_rgph2024_platform",
        name=platform.title,
        producer="Haut-Commissariat au Plan",
        url=platform.page,
        license="Publication officielle",
        badge=Badge.official,
        retrieved_at=datetime.now(UTC),
        published_at=None,
        notes="Indicateurs communaux du RGPH 2024 (milieu « Ensemble »).",
    ).id
    by_code = {r.code: tid for tid, r in matched.items()}
    found = 0
    for name, dataset in platform.datasets.items():
        wanted = [v for v in platform.variables if v.dataset == name]
        if not wanted:
            continue
        cache = ctx.raw_dir / f"hcp_platform_{name}.json"
        rows = fetch_platform(platform, dataset, province_codes, cache, ctx.refresh)
        for variable in wanted:
            for entry in rows:
                if (
                    entry.get(dataset.indicator_column) == variable.indicator
                    and entry.get("Milieu") == "Ensemble"
                    and entry.get("Sexe") == variable.sex
                    and entry.get("Value(valeur indicateur)") is not None
                ):
                    territory_id = by_code.get(str(entry["code_zone"]))
                    if territory_id is not None:
                        add(
                            territory_id,
                            variable.code,
                            platform.year,
                            float(entry["Value(valeur indicateur)"]),
                            variable.unit,
                            platform_source,
                        )
                        found += 1

    ids = [t.id for t in territories]
    hcp_sources = [*sources.values(), platform_source]
    ctx.session.execute(
        text("DELETE FROM raw_variables WHERE territory_id = ANY(:ids) AND source_id = ANY(:src)"),
        {"ids": ids, "src": hcp_sources},
    )
    if values:
        ctx.session.execute(RawVariable.__table__.insert(), values)  # type: ignore[attr-defined]

    analysis = [t for t in territories if t.is_analysis_unit]
    with_code = sum(1 for t in analysis if t.official_code)
    summary = (
        f"Recensement HCP : {with_code}/{len(analysis)} unités rattachées à leur code officiel, "
        f"population 2014 et 2024, {found} valeurs d'indicateurs communaux 2024."
    )
    return ImportResult(
        summary, {"matched": with_code, "platform_values": found}, warnings, None, len(values)
    )
