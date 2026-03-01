"""add_decision_audit_log

Revision ID: d3e4f5a6b7c8
Revises: a7f9e1d2c3b4
Create Date: 2026-02-28 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "d3e4f5a6b7c8"
down_revision: Union[str, None] = "a7f9e1d2c3b4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "decision_audit_log",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("ts", sa.DateTime(timezone=True), nullable=False),
        sa.Column("source", sa.String(), nullable=False),
        sa.Column("request_id", sa.String(), nullable=True),
        sa.Column("policy_version", sa.String(), nullable=False, server_default=""),
        sa.Column("policy_state", sa.String(), nullable=False, server_default=""),
        sa.Column("policy_score", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("policy_decision", sa.String(), nullable=False, server_default=""),
        sa.Column("decision_state", sa.String(), nullable=True),
        sa.Column("decision_action", sa.String(), nullable=True),
        sa.Column(
            "payload",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_decision_audit_log_ts", "decision_audit_log", ["ts"], unique=False)
    op.create_index(
        "ix_decision_audit_log_policy_state_ts",
        "decision_audit_log",
        ["policy_state", "ts"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_decision_audit_log_policy_state_ts", table_name="decision_audit_log")
    op.drop_index("ix_decision_audit_log_ts", table_name="decision_audit_log")
    op.drop_table("decision_audit_log")
