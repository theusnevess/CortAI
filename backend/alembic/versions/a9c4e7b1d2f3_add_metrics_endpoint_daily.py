"""add_metrics_endpoint_daily

Revision ID: a9c4e7b1d2f3
Revises: f4b5c6d7e8f9
Create Date: 2026-02-17 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "a9c4e7b1d2f3"
down_revision: Union[str, None] = "f4b5c6d7e8f9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    table_name = "metrics_endpoint_daily"
    existing_tables = inspector.get_table_names()
    if table_name not in existing_tables:
        op.create_table(
            table_name,
            sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("metric_date", sa.Date(), nullable=False),
            sa.Column("endpoint", sa.String(), nullable=False),
            sa.Column("count_requests", sa.Integer(), nullable=False),
            sa.Column("p50_ms", sa.Integer(), nullable=False),
            sa.Column("p95_ms", sa.Integer(), nullable=False),
            sa.Column("p99_ms", sa.Integer(), nullable=False),
            sa.Column("error_rate", sa.Numeric(precision=6, scale=4), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )

    existing_indexes = {idx["name"] for idx in inspector.get_indexes(table_name)}
    if "ix_metrics_endpoint_daily_metric_date" not in existing_indexes:
        op.create_index(
            "ix_metrics_endpoint_daily_metric_date",
            table_name,
            ["metric_date"],
            unique=False,
        )
    if "ix_metrics_endpoint_daily_endpoint" not in existing_indexes:
        op.create_index(
            "ix_metrics_endpoint_daily_endpoint",
            table_name,
            ["endpoint"],
            unique=False,
        )
    if "ux_metrics_endpoint_daily_metric_date_endpoint" not in existing_indexes:
        op.create_index(
            "ux_metrics_endpoint_daily_metric_date_endpoint",
            table_name,
            ["metric_date", "endpoint"],
            unique=True,
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    table_name = "metrics_endpoint_daily"
    if table_name not in inspector.get_table_names():
        return
    existing_indexes = {idx["name"] for idx in inspector.get_indexes(table_name)}
    if "ux_metrics_endpoint_daily_metric_date_endpoint" in existing_indexes:
        op.drop_index("ux_metrics_endpoint_daily_metric_date_endpoint", table_name=table_name)
    if "ix_metrics_endpoint_daily_endpoint" in existing_indexes:
        op.drop_index("ix_metrics_endpoint_daily_endpoint", table_name=table_name)
    if "ix_metrics_endpoint_daily_metric_date" in existing_indexes:
        op.drop_index("ix_metrics_endpoint_daily_metric_date", table_name=table_name)
    op.drop_table(table_name)
