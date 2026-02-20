"""baseline runtime marker

Revision ID: d6a7b8c9e0f1
Revises: c5d9f8a1b2c3
Create Date: 2026-02-19 00:00:00.000000
"""

from typing import Sequence, Union


# revision identifiers, used by Alembic.
revision: str = "d6a7b8c9e0f1"
down_revision: Union[str, None] = "c5d9f8a1b2c3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Marcador de baseline para manter continuidade do histórico de migração
    entre ambientes que já foram promovidos para d6a7b8c9e0f1.
    """
    return None


def downgrade() -> None:
    return None
