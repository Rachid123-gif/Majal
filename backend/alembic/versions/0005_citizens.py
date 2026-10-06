"""Citizen listening: places, consultations, contributions.

Revision ID: 0005
Revises: 0004
Create Date: 2026-10-06
"""

from collections.abc import Sequence

import geoalchemy2
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0005"
down_revision: str | None = "0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "places",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "study_area_id",
            sa.Integer,
            sa.ForeignKey("study_areas.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("external_id", sa.String(80), nullable=False),
        sa.Column("kind", sa.String(40), nullable=False),
        sa.Column("name", sa.String(300), nullable=False),
        sa.Column("name_ar", sa.String(300)),
        sa.Column("alt_names", postgresql.JSONB, nullable=False, server_default="[]"),
        sa.Column("territory_id", sa.Integer, sa.ForeignKey("territories.id", ondelete="SET NULL")),
        sa.Column(
            "geom",
            geoalchemy2.Geometry("POINT", srid=4326, spatial_index=True),
            nullable=False,
        ),
        sa.Column("source_id", sa.Integer, sa.ForeignKey("data_sources.id"), nullable=False),
        sa.UniqueConstraint("study_area_id", "external_id"),
    )
    op.create_table(
        "consultations",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "study_area_id",
            sa.Integer,
            sa.ForeignKey("study_areas.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("code", sa.String(80), nullable=False),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("badge", sa.String(20), nullable=False),
        sa.Column("source_file", sa.String(300)),
        sa.Column("method_note", sa.Text),
        sa.Column("imported_by", sa.String(80)),
        sa.Column(
            "imported_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.UniqueConstraint("study_area_id", "code"),
    )
    op.create_table(
        "contributions",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "consultation_id",
            sa.Integer,
            sa.ForeignKey("consultations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("external_id", sa.String(80), nullable=False),
        sa.Column("original_text", sa.Text, nullable=False),
        sa.Column("declared_language", sa.String(20)),
        sa.Column("language", sa.String(20)),
        sa.Column("anonymized_text", sa.Text),
        sa.Column("anonymization", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column("translation_fr", sa.Text),
        sa.Column("themes", postgresql.JSONB, nullable=False, server_default="[]"),
        sa.Column("tonality", sa.String(20)),
        sa.Column("place_text", sa.String(300)),
        sa.Column("place_id", sa.Integer, sa.ForeignKey("places.id", ondelete="SET NULL")),
        sa.Column("territory_id", sa.Integer, sa.ForeignKey("territories.id", ondelete="SET NULL")),
        sa.Column("badge", sa.String(20), nullable=False),
        sa.Column("analysis", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.UniqueConstraint("consultation_id", "external_id"),
    )
    op.create_index("ix_contributions_territory", "contributions", ["territory_id"])


def downgrade() -> None:
    op.drop_index("ix_contributions_territory", "contributions")
    op.drop_table("contributions")
    op.drop_table("consultations")
    op.drop_table("places")
