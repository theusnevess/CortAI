"""add_latency_and_truncation_metrics

Revision ID: e3b1a2c4d5f6
Revises: c1d2e3f4a5b6
Create Date: 2026-02-10 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "e3b1a2c4d5f6"
down_revision: Union[str, None] = "c1d2e3f4a5b6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "cognitive_metrics_daily",
        sa.Column("truncated_runs", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "cognitive_metrics_daily",
        sa.Column("truncated_ratio", sa.Numeric(precision=5, scale=2), nullable=True),
    )
    op.add_column(
        "cognitive_metrics_daily",
        sa.Column(
            "latency_by_action",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
    )
    op.alter_column("cognitive_metrics_daily", "truncated_runs", server_default=None)
    op.alter_column("cognitive_metrics_daily", "latency_by_action", server_default=None)

    op.create_index(
        "ix_observations_event_type",
        "observations",
        [sa.text("(facts->>'event_type')")],
    )


def downgrade() -> None:
    op.drop_index("ix_observations_event_type", table_name="observations")
    op.drop_column("cognitive_metrics_daily", "latency_by_action")
    op.drop_column("cognitive_metrics_daily", "truncated_ratio")
    op.drop_column("cognitive_metrics_daily", "truncated_runs")
