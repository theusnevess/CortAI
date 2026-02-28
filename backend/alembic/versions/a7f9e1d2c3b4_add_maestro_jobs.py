"""add_maestro_jobs

Revision ID: a7f9e1d2c3b4
Revises: f4b5c6d7e8f9
Create Date: 2026-02-28 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "a7f9e1d2c3b4"
down_revision: Union[str, None] = "f4b5c6d7e8f9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "maestro_jobs",
        sa.Column("job_id", sa.String(), nullable=False),
        sa.Column("source_ref", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("step", sa.String(), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(), nullable=False),
        sa.Column("finished_at", sa.DateTime(), nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("demo_mode", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column(
            "step_durations_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.PrimaryKeyConstraint("job_id"),
    )
    op.create_index("ix_maestro_jobs_status", "maestro_jobs", ["status"], unique=False)
    op.create_index("ix_maestro_jobs_started_at", "maestro_jobs", ["started_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_maestro_jobs_started_at", table_name="maestro_jobs")
    op.drop_index("ix_maestro_jobs_status", table_name="maestro_jobs")
    op.drop_table("maestro_jobs")
