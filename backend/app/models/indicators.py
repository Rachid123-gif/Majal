"""Indicator inputs and results (stage 2)."""

from datetime import datetime
from typing import Any

from geoalchemy2 import Geometry, WKBElement
from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class RawVariable(Base):
    """Input variable of a unit (census figure, count, built-up area…), with its source."""

    __tablename__ = "raw_variables"
    __table_args__ = (UniqueConstraint("territory_id", "code", "year"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    territory_id: Mapped[int] = mapped_column(ForeignKey("territories.id", ondelete="CASCADE"))
    code: Mapped[str] = mapped_column(String(60))
    year: Mapped[int] = mapped_column(Integer)
    value: Mapped[float] = mapped_column(Float)
    unit: Mapped[str | None] = mapped_column(String(40))
    source_id: Mapped[int] = mapped_column(ForeignKey("data_sources.id"))
    badge: Mapped[str] = mapped_column(String(20))
    method: Mapped[str] = mapped_column(String(20), default="direct")


class PopulationCell(Base):
    """Population grid cell (GHSL), rescaled so each unit matches its official census total."""

    __tablename__ = "population_cells"

    id: Mapped[int] = mapped_column(primary_key=True)
    study_area_id: Mapped[int] = mapped_column(ForeignKey("study_areas.id", ondelete="CASCADE"))
    territory_id: Mapped[int] = mapped_column(ForeignKey("territories.id", ondelete="CASCADE"))
    geom: Mapped[WKBElement] = mapped_column(Geometry("POINT", srid=4326))
    population: Mapped[float] = mapped_column(Float)
    grid_population: Mapped[float] = mapped_column(Float)


class IndicatorDefinitionRow(Base):
    __tablename__ = "indicator_definitions"
    __table_args__ = (UniqueConstraint("grid_version", "code"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    grid_version: Mapped[str] = mapped_column(String(40))
    code: Mapped[str] = mapped_column(String(40))
    definition: Mapped[dict[str, Any]] = mapped_column(JSONB)


class Diagnostic(Base):
    __tablename__ = "diagnostics"

    id: Mapped[int] = mapped_column(primary_key=True)
    study_area_id: Mapped[int] = mapped_column(ForeignKey("study_areas.id", ondelete="CASCADE"))
    grid_version: Mapped[str] = mapped_column(String(40))
    method_hash: Mapped[str] = mapped_column(String(40))
    computed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    status: Mapped[str] = mapped_column(String(20), default="computed")
    author: Mapped[str | None] = mapped_column(String(80))
    duration_ms: Mapped[int | None] = mapped_column(Integer)
    result: Mapped[dict[str, Any]] = mapped_column(JSONB)


class IndicatorValue(Base):
    __tablename__ = "indicator_values"

    id: Mapped[int] = mapped_column(primary_key=True)
    diagnostic_id: Mapped[int] = mapped_column(ForeignKey("diagnostics.id", ondelete="CASCADE"))
    territory_id: Mapped[int] = mapped_column(ForeignKey("territories.id", ondelete="CASCADE"))
    indicator_code: Mapped[str] = mapped_column(String(40))
    year: Mapped[int | None] = mapped_column(Integer)
    value: Mapped[float | None] = mapped_column(Float)
    unit: Mapped[str | None] = mapped_column(String(40))
    badge: Mapped[str | None] = mapped_column(String(20))
    reliability: Mapped[int | None] = mapped_column(Integer)
    method: Mapped[str | None] = mapped_column(String(20))
    status: Mapped[str] = mapped_column(String(20))
    rank: Mapped[int | None] = mapped_column(Integer)
    reference: Mapped[float | None] = mapped_column(Float)
    ratio: Mapped[float | None] = mapped_column(Float)
    provisional: Mapped[bool] = mapped_column(Boolean, default=False)
    extra: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
