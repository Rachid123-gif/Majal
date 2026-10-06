"""Contributions: declared commune, channel, date.

Revision ID: 0006
Revises: 0005
Create Date: 2026-10-06
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0006"
down_revision: str | None = "0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("contributions", sa.Column("declared_commune", sa.String(200)))
    op.add_column("contributions", sa.Column("channel", sa.String(80)))
    op.add_column("contributions", sa.Column("submitted_on", sa.Date))


def downgrade() -> None:
    op.drop_column("contributions", "submitted_on")
    op.drop_column("contributions", "channel")
    op.drop_column("contributions", "declared_commune")
