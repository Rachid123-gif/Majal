"""Territorial core tables: sources, study areas, territories, facilities, roads, imports.

Revision ID: 0002
Revises: 0001
Create Date: 2026-10-05
"""

from collections.abc import Sequence

import geoalchemy2
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "data_sources",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("code", sa.String(80), nullable=False, unique=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("producer", sa.String(200), nullable=False),
        sa.Column("url", sa.String(500)),
        sa.Column("license", sa.String(200)),
        sa.Column("default_badge", sa.String(20), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True)),
        sa.Column("retrieved_at", sa.DateTime(timezone=True)),
        sa.Column("notes", sa.Text),
    )
    op.create_table(
        "study_areas",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("code", sa.String(40), nullable=False, unique=True),
        sa.Column("name_fr", sa.String(200), nullable=False),
        sa.Column("name_ar", sa.String(200), nullable=False),
        sa.Column("indicator_profile", sa.String(40), nullable=False),
        sa.Column("taxonomy_profile", sa.String(40), nullable=False),
        sa.Column("config", postgresql.JSONB, nullable=False),
    )
    op.create_table(
        "territories",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "study_area_id",
            sa.Integer,
            sa.ForeignKey("study_areas.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("external_id", sa.String(80), nullable=False),
        sa.Column("official_code", sa.String(40)),
        sa.Column("name_fr", sa.String(200), nullable=False),
        sa.Column("name_ar", sa.String(200)),
        sa.Column("level", sa.String(30), nullable=False),
        sa.Column("parent_id", sa.Integer, sa.ForeignKey("territories.id", ondelete="SET NULL")),
        sa.Column("milieu", sa.String(10)),
        sa.Column("is_analysis_unit", sa.Boolean, nullable=False),
        sa.Column("scopes", postgresql.JSONB, nullable=False),
        sa.Column(
            "geom",
            geoalchemy2.Geometry("MULTIPOLYGON", srid=4326, spatial_index=True),
            nullable=False,
        ),
        sa.Column("area_km2", sa.Float),
        sa.Column("source_id", sa.Integer, sa.ForeignKey("data_sources.id"), nullable=False),
        sa.Column("source_meta", postgresql.JSONB, nullable=False),
        sa.UniqueConstraint("study_area_id", "external_id"),
    )
    op.create_table(
        "facilities",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "study_area_id",
            sa.Integer,
            sa.ForeignKey("study_areas.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("external_id", sa.String(80), nullable=False),
        sa.Column("category", sa.String(60), nullable=False),
        sa.Column("subcategory", sa.String(80)),
        sa.Column("name", sa.String(300)),
        sa.Column("name_ar", sa.String(300)),
        sa.Column("territory_id", sa.Integer, sa.ForeignKey("territories.id", ondelete="SET NULL")),
        sa.Column(
            "geom", geoalchemy2.Geometry("GEOMETRY", srid=4326, spatial_index=True), nullable=False
        ),
        sa.Column("area_m2", sa.Float),
        sa.Column("source_id", sa.Integer, sa.ForeignKey("data_sources.id"), nullable=False),
        sa.UniqueConstraint("study_area_id", "external_id"),
    )
    op.create_index("ix_facilities_category", "facilities", ["study_area_id", "category"])
    op.create_table(
        "roads",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "study_area_id",
            sa.Integer,
            sa.ForeignKey("study_areas.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("external_id", sa.String(80), nullable=False),
        sa.Column("highway", sa.String(40), nullable=False),
        sa.Column("surface", sa.String(40)),
        sa.Column("paved", sa.Boolean),
        sa.Column("name", sa.String(300)),
        sa.Column(
            "geom",
            geoalchemy2.Geometry("LINESTRING", srid=4326, spatial_index=True),
            nullable=False,
        ),
        sa.Column("length_m", sa.Float),
        sa.Column("source_id", sa.Integer, sa.ForeignKey("data_sources.id"), nullable=False),
        sa.UniqueConstraint("study_area_id", "external_id"),
    )
    op.create_table(
        "import_runs",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("study_area_code", sa.String(40), nullable=False),
        sa.Column("importer", sa.String(60), nullable=False),
        sa.Column(
            "started_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("finished_at", sa.DateTime(timezone=True)),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("summary", sa.Text),
        sa.Column("counts", postgresql.JSONB, nullable=False),
        sa.Column("warnings", postgresql.JSONB, nullable=False),
        sa.Column("raw_file", sa.String(300)),
        sa.Column("rows", sa.Integer, nullable=False),
    )


def downgrade() -> None:
    for table in ("import_runs", "roads", "facilities", "territories", "study_areas"):
        op.drop_table(table)
    op.drop_table("data_sources")
