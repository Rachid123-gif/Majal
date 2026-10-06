"""Citizen listening (stage 4): place gazetteer, consultations and contributions."""

from datetime import datetime
from typing import Any

from geoalchemy2 import Geometry, WKBElement
from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Place(Base):
    """Named places (neighbourhoods, squares…) used to locate what citizens mention."""

    __tablename__ = "places"
    __table_args__ = (UniqueConstraint("study_area_id", "external_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    study_area_id: Mapped[int] = mapped_column(ForeignKey("study_areas.id", ondelete="CASCADE"))
    external_id: Mapped[str] = mapped_column(String(80))
    kind: Mapped[str] = mapped_column(String(40))  # suburb | neighbourhood | quarter | square…
    name: Mapped[str] = mapped_column(String(300))
    name_ar: Mapped[str | None] = mapped_column(String(300))
    alt_names: Mapped[list[str]] = mapped_column(JSONB, default=list)
    territory_id: Mapped[int | None] = mapped_column(
        ForeignKey("territories.id", ondelete="SET NULL")
    )
    geom: Mapped[WKBElement] = mapped_column(Geometry("POINT", srid=4326))
    source_id: Mapped[int] = mapped_column(ForeignKey("data_sources.id"))


class Consultation(Base):
    """A set of contributions imported together (a file, a public meeting, a platform)."""

    __tablename__ = "consultations"
    __table_args__ = (UniqueConstraint("study_area_id", "code"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    study_area_id: Mapped[int] = mapped_column(ForeignKey("study_areas.id", ondelete="CASCADE"))
    code: Mapped[str] = mapped_column(String(80))
    title: Mapped[str] = mapped_column(String(300))
    badge: Mapped[str] = mapped_column(String(20))  # fictitious in version D
    source_file: Mapped[str | None] = mapped_column(String(300))
    method_note: Mapped[str | None] = mapped_column(Text)
    imported_by: Mapped[str | None] = mapped_column(String(80))
    imported_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class Contribution(Base):
    __tablename__ = "contributions"
    __table_args__ = (UniqueConstraint("consultation_id", "external_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    consultation_id: Mapped[int] = mapped_column(ForeignKey("consultations.id", ondelete="CASCADE"))
    external_id: Mapped[str] = mapped_column(String(80))
    original_text: Mapped[str] = mapped_column(Text)
    declared_language: Mapped[str | None] = mapped_column(String(20))
    language: Mapped[str | None] = mapped_column(String(20))  # detected
    anonymized_text: Mapped[str | None] = mapped_column(Text)
    anonymization: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)  # what was masked
    translation_fr: Mapped[str | None] = mapped_column(Text)
    themes: Mapped[list[str]] = mapped_column(JSONB, default=list)
    tonality: Mapped[str | None] = mapped_column(String(20))
    place_text: Mapped[str | None] = mapped_column(String(300))
    place_id: Mapped[int | None] = mapped_column(ForeignKey("places.id", ondelete="SET NULL"))
    territory_id: Mapped[int | None] = mapped_column(
        ForeignKey("territories.id", ondelete="SET NULL")
    )
    badge: Mapped[str] = mapped_column(String(20))
    analysis: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)  # model, mode, timing
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
