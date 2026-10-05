"""Generated reports.

Revision ID: 0004
Revises: 0003
Create Date: 2026-10-05
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "reports",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "territory_id",
            sa.Integer,
            sa.ForeignKey("territories.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "diagnostic_id", sa.Integer, sa.ForeignKey("diagnostics.id", ondelete="SET NULL")
        ),
        sa.Column("language", sa.String(5), nullable=False),
        sa.Column("provider", sa.String(40), nullable=False),
        sa.Column("model", sa.String(80), nullable=False),
        sa.Column("cache_key", sa.String(64), nullable=False, index=True),
        sa.Column("state", sa.String(20), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("writing_mode", sa.String(20)),
        sa.Column("progress", postgresql.JSONB, nullable=False),
        sa.Column("content", postgresql.JSONB, nullable=False),
        sa.Column("fact_sheet", postgresql.JSONB, nullable=False),
        sa.Column("history", postgresql.JSONB, nullable=False),
        sa.Column("error", sa.String(500)),
        sa.Column("duration_s", sa.Float),
        sa.Column("requested_by", sa.String(80)),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("finished_at", sa.DateTime(timezone=True)),
        sa.Column("llm_calls", sa.Integer, nullable=False),
    )


def downgrade() -> None:
    op.drop_table("reports")
