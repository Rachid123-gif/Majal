"""Indicator inputs and results: raw variables, population grid, diagnostics.

Revision ID: 0003
Revises: 0002
Create Date: 2026-10-05
"""

from collections.abc import Sequence

import geoalchemy2
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "raw_variables",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "territory_id",
            sa.Integer,
            sa.ForeignKey("territories.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("code", sa.String(60), nullable=False),
        sa.Column("year", sa.Integer, nullable=False),
        sa.Column("value", sa.Float, nullable=False),
        sa.Column("unit", sa.String(40)),
        sa.Column("source_id", sa.Integer, sa.ForeignKey("data_sources.id"), nullable=False),
        sa.Column("badge", sa.String(20), nullable=False),
        sa.Column("method", sa.String(20), nullable=False),
        sa.UniqueConstraint("territory_id", "code", "year"),
    )
    op.create_table(
        "population_cells",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "study_area_id",
            sa.Integer,
            sa.ForeignKey("study_areas.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "territory_id",
            sa.Integer,
            sa.ForeignKey("territories.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "geom", geoalchemy2.Geometry("POINT", srid=4326, spatial_index=True), nullable=False
        ),
        sa.Column("population", sa.Float, nullable=False),
        sa.Column("grid_population", sa.Float, nullable=False),
    )
    op.create_index("ix_population_cells_territory", "population_cells", ["territory_id"])
    op.create_table(
        "indicator_definitions",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("grid_version", sa.String(40), nullable=False),
        sa.Column("code", sa.String(40), nullable=False),
        sa.Column("definition", postgresql.JSONB, nullable=False),
        sa.UniqueConstraint("grid_version", "code"),
    )
    op.create_table(
        "diagnostics",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "study_area_id",
            sa.Integer,
            sa.ForeignKey("study_areas.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("grid_version", sa.String(40), nullable=False),
        sa.Column("method_hash", sa.String(40), nullable=False),
        sa.Column(
            "computed_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("author", sa.String(80)),
        sa.Column("duration_ms", sa.Integer),
        sa.Column("result", postgresql.JSONB, nullable=False),
    )
    op.create_table(
        "indicator_values",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "diagnostic_id",
            sa.Integer,
            sa.ForeignKey("diagnostics.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "territory_id",
            sa.Integer,
            sa.ForeignKey("territories.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("indicator_code", sa.String(40), nullable=False),
        sa.Column("year", sa.Integer),
        sa.Column("value", sa.Float),
        sa.Column("unit", sa.String(40)),
        sa.Column("badge", sa.String(20)),
        sa.Column("reliability", sa.Integer),
        sa.Column("method", sa.String(20)),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("rank", sa.Integer),
        sa.Column("reference", sa.Float),
        sa.Column("ratio", sa.Float),
        sa.Column("provisional", sa.Boolean, nullable=False),
        sa.Column("extra", postgresql.JSONB, nullable=False),
    )
    op.create_index(
        "ix_indicator_values_lookup", "indicator_values", ["diagnostic_id", "indicator_code"]
    )


def downgrade() -> None:
    for table in (
        "indicator_values",
        "diagnostics",
        "indicator_definitions",
        "population_cells",
        "raw_variables",
    ):
        op.drop_table(table)
