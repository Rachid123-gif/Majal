"""Generated reports (stage 3): content, provenance, cache key, validation history."""

from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(primary_key=True)
    territory_id: Mapped[int] = mapped_column(ForeignKey("territories.id", ondelete="CASCADE"))
    diagnostic_id: Mapped[int | None] = mapped_column(
        ForeignKey("diagnostics.id", ondelete="SET NULL")
    )
    language: Mapped[str] = mapped_column(String(5))
    provider: Mapped[str] = mapped_column(String(40))
    model: Mapped[str] = mapped_column(String(80))
    cache_key: Mapped[str] = mapped_column(String(64), index=True)
    # pending | running | done | failed (generation) ; brouillon | relu | valide (validation)
    state: Mapped[str] = mapped_column(String(20), default="pending")
    status: Mapped[str] = mapped_column(String(20), default="brouillon")
    writing_mode: Mapped[str | None] = mapped_column(String(20))  # ai | mixed | fallback
    progress: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    content: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    fact_sheet: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    history: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, default=list)
    error: Mapped[str | None] = mapped_column(String(500))
    duration_s: Mapped[float | None] = mapped_column(Float)
    requested_by: Mapped[str | None] = mapped_column(String(80))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    llm_calls: Mapped[int] = mapped_column(Integer, default=0)
