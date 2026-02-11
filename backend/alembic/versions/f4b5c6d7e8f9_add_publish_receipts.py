"""add_publish_receipts

Revision ID: f4b5c6d7e8f9
Revises: e3b1a2c4d5f6
Create Date: 2026-02-11 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f4b5c6d7e8f9"
down_revision: Union[str, None] = "e3b1a2c4d5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "publish_receipts",
        sa.Column("publish_decision_id", sa.String(), nullable=False),
        sa.Column("process_id", sa.String(), nullable=False),
        sa.Column("manifest_decision_id", sa.String(), nullable=True),
        sa.Column("pipeline_status", sa.String(), nullable=False),
        sa.Column("execution_status", sa.String(), nullable=False),
        sa.Column("target", sa.String(), nullable=False),
        sa.Column("external_post_id", sa.String(), nullable=True),
        sa.Column("error_type", sa.String(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("published_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("publish_decision_id"),
    )
    op.create_index(
        "ix_publish_receipts_process_id",
        "publish_receipts",
        ["process_id"],
        unique=False,
    )
    op.create_index(
        "ix_publish_receipts_manifest_decision_id",
        "publish_receipts",
        ["manifest_decision_id"],
        unique=False,
    )
    op.create_index(
        "ix_publish_receipts_created_at",
        "publish_receipts",
        ["created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_publish_receipts_created_at", table_name="publish_receipts")
    op.drop_index("ix_publish_receipts_manifest_decision_id", table_name="publish_receipts")
    op.drop_index("ix_publish_receipts_process_id", table_name="publish_receipts")
    op.drop_table("publish_receipts")
