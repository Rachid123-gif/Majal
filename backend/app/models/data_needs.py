"""Module « Besoins en données » (stage 5): follow-up of the data requests, per institution."""

from datetime import date, datetime
from typing import Any

from sqlalchemy import Date, DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class DataRequestTracking(Base):
    """Status of the request sent to one institution (to_send, sent, granted, refused), the date
    the user gives for it, and the history of the changes."""

    __tablename__ = "data_request_tracking"
    __table_args__ = (UniqueConstraint("study_area_id", "institution_code"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    study_area_id: Mapped[int] = mapped_column(ForeignKey("study_areas.id", ondelete="CASCADE"))
    institution_code: Mapped[str] = mapped_column(String(80))  # config/data_holders/<code>.yaml
    status: Mapped[str] = mapped_column(String(20))
    status_date: Mapped[date | None] = mapped_column(Date)
    updated_by: Mapped[str | None] = mapped_column(String(80))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    history: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, default=list)
