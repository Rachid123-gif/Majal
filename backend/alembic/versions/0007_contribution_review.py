"""Contributions: human review (the tool proposes, the urban planner validates).

Revision ID: 0007
Revises: 0006
Create Date: 2026-10-06
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "0007"
down_revision: str | None = "0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("contributions", sa.Column("ai_proposal", JSONB))
    op.add_column("contributions", sa.Column("validated_by", sa.String(80)))
    op.add_column("contributions", sa.Column("validated_at", sa.DateTime(timezone=True)))


def downgrade() -> None:
    op.drop_column("contributions", "validated_at")
    op.drop_column("contributions", "validated_by")
    op.drop_column("contributions", "ai_proposal")
