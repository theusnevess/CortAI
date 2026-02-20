"""add metrics_read_refresh_jobs queue for async snapshot refresh

Revision ID: c2d3e4f5a6b7
Revises: b1c2d3e4f5a6
Create Date: 2026-02-20 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "c2d3e4f5a6b7"
down_revision = "b1c2d3e4f5a6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())
    if "metrics_read_refresh_jobs" not in tables:
        op.create_table(
            "metrics_read_refresh_jobs",
            sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("job_key", sa.String(), nullable=False),
            sa.Column("endpoint", sa.String(), nullable=False),
            sa.Column("query_key", sa.String(), nullable=False),
            sa.Column("status", sa.String(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("expires_at", sa.DateTime(), nullable=False),
            sa.Column("last_error", sa.Text(), nullable=True),
            sa.PrimaryKeyConstraint("id"),
        )

    indexes = {idx["name"] for idx in inspector.get_indexes("metrics_read_refresh_jobs")}
    if "ix_metrics_read_refresh_jobs_job_key" not in indexes:
        op.create_index(
            "ix_metrics_read_refresh_jobs_job_key",
            "metrics_read_refresh_jobs",
            ["job_key"],
            unique=True,
        )
    if "ix_metrics_read_refresh_jobs_endpoint" not in indexes:
        op.create_index(
            "ix_metrics_read_refresh_jobs_endpoint",
            "metrics_read_refresh_jobs",
            ["endpoint"],
            unique=False,
        )
    if "ix_metrics_read_refresh_jobs_status" not in indexes:
        op.create_index(
            "ix_metrics_read_refresh_jobs_status",
            "metrics_read_refresh_jobs",
            ["status"],
            unique=False,
        )
    if "ix_metrics_read_refresh_jobs_expires_at" not in indexes:
        op.create_index(
            "ix_metrics_read_refresh_jobs_expires_at",
            "metrics_read_refresh_jobs",
            ["expires_at"],
            unique=False,
        )
    if "ix_metrics_read_refresh_jobs_status_expires_at" not in indexes:
        op.create_index(
            "ix_metrics_read_refresh_jobs_status_expires_at",
            "metrics_read_refresh_jobs",
            ["status", "expires_at"],
            unique=False,
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())
    if "metrics_read_refresh_jobs" not in tables:
        return
    indexes = {idx["name"] for idx in inspector.get_indexes("metrics_read_refresh_jobs")}
    for idx_name in (
        "ix_metrics_read_refresh_jobs_status_expires_at",
        "ix_metrics_read_refresh_jobs_expires_at",
        "ix_metrics_read_refresh_jobs_status",
        "ix_metrics_read_refresh_jobs_endpoint",
        "ix_metrics_read_refresh_jobs_job_key",
    ):
        if idx_name in indexes:
            op.drop_index(idx_name, table_name="metrics_read_refresh_jobs")
    op.drop_table("metrics_read_refresh_jobs")

