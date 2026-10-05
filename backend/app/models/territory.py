"""Core territorial tables (stage 1). Future tables — projects (module 3), land_parcels and
investor_profiles (module 4) — will reference `territories.id` and need no change here."""

from datetime import datetime
from enum import StrEnum
from typing import Any

from geoalchemy2 import Geometry, WKBElement
from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Badge(StrEnum):
    """Confidence badge shown next to every value (BRIEF §7.2)."""

    official = "official"
    open = "open"
    estimated = "estimated"
    fictitious = "fictitious"


class DataSource(Base):
    __tablename__ = "data_sources"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(80), unique=True)
    name: Mapped[str] = mapped_column(String(200))
    producer: Mapped[str] = mapped_column(String(200))
    url: Mapped[str | None] = mapped_column(String(500))
    license: Mapped[str | None] = mapped_column(String(200))
    default_badge: Mapped[str] = mapped_column(String(20))
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    retrieved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    notes: Mapped[str | None] = mapped_column(Text)


class StudyArea(Base):
    __tablename__ = "study_areas"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(40), unique=True)
    name_fr: Mapped[str] = mapped_column(String(200))
    name_ar: Mapped[str] = mapped_column(String(200))
    indicator_profile: Mapped[str] = mapped_column(String(40))
    taxonomy_profile: Mapped[str] = mapped_column(String(40))
    config: Mapped[dict[str, Any]] = mapped_column(JSONB)


class Territory(Base):
    __tablename__ = "territories"
    __table_args__ = (UniqueConstraint("study_area_id", "external_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    study_area_id: Mapped[int] = mapped_column(ForeignKey("study_areas.id", ondelete="CASCADE"))
    external_id: Mapped[str] = mapped_column(String(80))  # e.g. "osm:relation/2799211"
    official_code: Mapped[str | None] = mapped_column(String(40))  # never invented
    name_fr: Mapped[str] = mapped_column(String(200))
    name_ar: Mapped[str | None] = mapped_column(String(200))
    level: Mapped[str] = mapped_column(String(30))
    parent_id: Mapped[int | None] = mapped_column(ForeignKey("territories.id", ondelete="SET NULL"))
    milieu: Mapped[str | None] = mapped_column(
        String(10)
    )  # urbain | rural, from a real source only
    is_analysis_unit: Mapped[bool] = mapped_column(Boolean, default=False)
    scopes: Mapped[list[str]] = mapped_column(JSONB, default=list)
    geom: Mapped[WKBElement] = mapped_column(Geometry("MULTIPOLYGON", srid=4326))
    area_km2: Mapped[float | None] = mapped_column(Float)
    source_id: Mapped[int] = mapped_column(ForeignKey("data_sources.id"))
    source_meta: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)

    parent: Mapped["Territory | None"] = relationship(remote_side=[id])
    source: Mapped[DataSource] = relationship()


class Facility(Base):
    __tablename__ = "facilities"
    __table_args__ = (UniqueConstraint("study_area_id", "external_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    study_area_id: Mapped[int] = mapped_column(ForeignKey("study_areas.id", ondelete="CASCADE"))
    external_id: Mapped[str] = mapped_column(String(80))
    category: Mapped[str] = mapped_column(String(60))
    subcategory: Mapped[str | None] = mapped_column(String(80))
    name: Mapped[str | None] = mapped_column(String(300))
    name_ar: Mapped[str | None] = mapped_column(String(300))
    territory_id: Mapped[int | None] = mapped_column(
        ForeignKey("territories.id", ondelete="SET NULL")
    )
    geom: Mapped[WKBElement] = mapped_column(Geometry("GEOMETRY", srid=4326))
    area_m2: Mapped[float | None] = mapped_column(Float)
    source_id: Mapped[int] = mapped_column(ForeignKey("data_sources.id"))


class Road(Base):
    __tablename__ = "roads"
    __table_args__ = (UniqueConstraint("study_area_id", "external_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    study_area_id: Mapped[int] = mapped_column(ForeignKey("study_areas.id", ondelete="CASCADE"))
    external_id: Mapped[str] = mapped_column(String(80))
    highway: Mapped[str] = mapped_column(String(40))
    surface: Mapped[str | None] = mapped_column(String(40))
    paved: Mapped[bool | None] = mapped_column(Boolean)
    name: Mapped[str | None] = mapped_column(String(300))
    geom: Mapped[WKBElement] = mapped_column(Geometry("LINESTRING", srid=4326))
    length_m: Mapped[float | None] = mapped_column(Float)
    source_id: Mapped[int] = mapped_column(ForeignKey("data_sources.id"))


class ImportRun(Base):
    __tablename__ = "import_runs"

    id: Mapped[int] = mapped_column(primary_key=True)
    study_area_code: Mapped[str] = mapped_column(String(40))
    importer: Mapped[str] = mapped_column(String(60))
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(20), default="running")
    summary: Mapped[str | None] = mapped_column(Text)
    counts: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    warnings: Mapped[list[str]] = mapped_column(JSONB, default=list)
    raw_file: Mapped[str | None] = mapped_column(String(300))
    rows: Mapped[int] = mapped_column(Integer, default=0)
