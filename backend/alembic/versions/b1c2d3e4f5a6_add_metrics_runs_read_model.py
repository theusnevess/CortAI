"""add metrics_runs_read_model table for P2-C read-path

Revision ID: b1c2d3e4f5a6
Revises: a1b2c3d4e5f7
Create Date: 2026-02-20 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "b1c2d3e4f5a6"
down_revision = "a1b2c3d4e5f7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())
    if "metrics_runs_read_model" not in tables:
        op.create_table(
            "metrics_runs_read_model",
            sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("start_date", sa.Date(), nullable=False),
            sa.Column("end_date", sa.Date(), nullable=False),
            sa.Column("limit", sa.Integer(), nullable=False),
            sa.Column("offset", sa.Integer(), nullable=False),
            sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
            sa.Column("refreshed_at", sa.DateTime(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )

    existing_indexes = {idx["name"] for idx in inspector.get_indexes("metrics_runs_read_model")}
    if "ix_runs_read_model_start_date" not in existing_indexes:
        op.create_index(
            "ix_runs_read_model_start_date",
            "metrics_runs_read_model",
            ["start_date"],
            unique=False,
        )
    if "ix_runs_read_model_end_date" not in existing_indexes:
        op.create_index(
            "ix_runs_read_model_end_date",
            "metrics_runs_read_model",
            ["end_date"],
            unique=False,
        )
    if "ux_runs_read_model_key" not in existing_indexes:
        op.create_index(
            "ux_runs_read_model_key",
            "metrics_runs_read_model",
            ["start_date", "end_date", "limit", "offset"],
            unique=True,
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())
    if "metrics_runs_read_model" not in tables:
        return

    indexes = {idx["name"] for idx in inspector.get_indexes("metrics_runs_read_model")}
    if "ux_runs_read_model_key" in indexes:
        op.drop_index("ux_runs_read_model_key", table_name="metrics_runs_read_model")
    if "ix_runs_read_model_end_date" in indexes:
        op.drop_index("ix_runs_read_model_end_date", table_name="metrics_runs_read_model")
    if "ix_runs_read_model_start_date" in indexes:
        op.drop_index("ix_runs_read_model_start_date", table_name="metrics_runs_read_model")
    op.drop_table("metrics_runs_read_model")

