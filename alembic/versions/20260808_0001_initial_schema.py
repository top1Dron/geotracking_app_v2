"""Initial schema with PostGIS geozones table.

Revision ID: 20260808_0001
Revises:
Create Date: 2026-08-08 18:30:00
"""

from alembic import op
import geoalchemy2
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20260808_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Apply initial database schema."""
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")
    op.create_table(
        "geozones",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", sa.String(length=128), nullable=False),
        sa.Column("name", sa.String(length=256), nullable=False),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column("radius_meters", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column(
            "center",
            geoalchemy2.Geography(geometry_type="POINT", srid=4326, spatial_index=True),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_geozones_user_id"), "geozones", ["user_id"], unique=False)


def downgrade() -> None:
    """Rollback initial schema."""
    op.drop_index(op.f("ix_geozones_user_id"), table_name="geozones")
    op.drop_table("geozones")
