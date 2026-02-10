"""add_cognitive_runs

Revision ID: 9b2f1d3f4c5a
Revises: 645f0574a239
Create Date: 2026-02-07 01:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9b2f1d3f4c5a'
down_revision: Union[str, None] = '645f0574a239'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'cognitive_runs',
        sa.Column('process_id', sa.String(), nullable=False),
        sa.Column('pipeline_status', sa.String(), nullable=False),
        sa.Column('termination_reason', sa.String(), nullable=True),
        sa.Column('terminated', sa.Boolean(), nullable=True),
        sa.Column('source_observation_id', sa.String(), nullable=False),
        sa.Column('source_outcome_id', sa.String(), nullable=True),
        sa.Column('source_decision_id', sa.String(), nullable=True),
        sa.Column('execution_status', sa.String(), nullable=True),
        sa.Column('actions_executed', sa.Integer(), nullable=True),
        sa.Column('last_action_type', sa.String(), nullable=True),
        sa.Column('video_id', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('process_id')
    )
    op.create_index('ix_cognitive_runs_video_id', 'cognitive_runs', ['video_id'], unique=False)
    op.create_index('ix_cognitive_runs_created_at', 'cognitive_runs', ['created_at'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_cognitive_runs_created_at', table_name='cognitive_runs')
    op.drop_index('ix_cognitive_runs_video_id', table_name='cognitive_runs')
    op.drop_table('cognitive_runs')
