"""Follow-up of the data requests, per institution (module « Besoins en données »).

Revision ID: 0008
Revises: 0007
Create Date: 2026-10-07
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "0008"
down_revision: str | None = "0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "data_request_tracking",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "study_area_id",
            sa.Integer,
            sa.ForeignKey("study_areas.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("institution_code", sa.String(80), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("status_date", sa.Date),
        sa.Column("updated_by", sa.String(80)),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("history", JSONB, nullable=False, server_default="[]"),
        sa.UniqueConstraint("study_area_id", "institution_code"),
    )


def downgrade() -> None:
    op.drop_table("data_request_tracking")
