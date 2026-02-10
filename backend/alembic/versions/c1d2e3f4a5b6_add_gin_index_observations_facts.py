"""add gin index on observations.facts

Revision ID: c1d2e3f4a5b6
Revises: b7d3c2f1a9e4
Create Date: 2026-02-10 04:15:00.000000
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "c1d2e3f4a5b6"
down_revision = "b7d3c2f1a9e4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index(
        "ix_observations_facts_gin",
        "observations",
        ["facts"],
        unique=False,
        postgresql_using="gin",
    )


def downgrade() -> None:
    op.drop_index("ix_observations_facts_gin", table_name="observations")
