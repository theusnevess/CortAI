"""add_alert_fields_to_cognitive_metrics_daily

Revision ID: c5d9f8a1b2c3
Revises: a9c4e7b1d2f3
Create Date: 2026-02-18 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "c5d9f8a1b2c3"
down_revision: Union[str, None] = "a9c4e7b1d2f3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {c["name"] for c in inspector.get_columns("cognitive_metrics_daily")}

    if "alert_count" not in columns:
        op.add_column(
            "cognitive_metrics_daily",
            sa.Column("alert_count", sa.Integer(), nullable=False, server_default="0"),
        )
        op.alter_column("cognitive_metrics_daily", "alert_count", server_default=None)

    if "alert_reasons" not in columns:
        op.add_column(
            "cognitive_metrics_daily",
            sa.Column(
                "alert_reasons",
                postgresql.JSONB(astext_type=sa.Text()),
                nullable=False,
                server_default=sa.text("'[]'::jsonb"),
            ),
        )
        op.alter_column("cognitive_metrics_daily", "alert_reasons", server_default=None)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {c["name"] for c in inspector.get_columns("cognitive_metrics_daily")}

    if "alert_reasons" in columns:
        op.drop_column("cognitive_metrics_daily", "alert_reasons")
    if "alert_count" in columns:
        op.drop_column("cognitive_metrics_daily", "alert_count")
