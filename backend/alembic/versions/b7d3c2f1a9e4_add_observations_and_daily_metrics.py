"""add_observations_and_daily_metrics

Revision ID: b7d3c2f1a9e4
Revises: 9b2f1d3f4c5a
Create Date: 2026-02-10 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "b7d3c2f1a9e4"
down_revision: Union[str, None] = "9b2f1d3f4c5a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "observations",
        sa.Column("observation_id", sa.String(), nullable=False),
        sa.Column("timestamp", sa.DateTime(), nullable=False),
        sa.Column("process_id", sa.String(), nullable=False),
        sa.Column("source_outcome_id", sa.String(), nullable=False),
        sa.Column("facts", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("observation_id"),
    )
    op.create_index("ix_observations_timestamp", "observations", ["timestamp"], unique=False)
    op.create_index("ix_observations_process_id", "observations", ["process_id"], unique=False)

    op.create_table(
        "cognitive_metrics_daily",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("metric_date", sa.Date(), nullable=False),
        sa.Column("total_runs", sa.Integer(), nullable=False),
        sa.Column("completed_runs", sa.Integer(), nullable=False),
        sa.Column("failed_runs", sa.Integer(), nullable=False),
        sa.Column("blocked_runs", sa.Integer(), nullable=False),
        sa.Column("avg_actions_executed", sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column(
            "last_action_type_distribution",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("metric_date"),
    )


def downgrade() -> None:
    op.drop_table("cognitive_metrics_daily")
    op.drop_index("ix_observations_process_id", table_name="observations")
    op.drop_index("ix_observations_timestamp", table_name="observations")
    op.drop_table("observations")
