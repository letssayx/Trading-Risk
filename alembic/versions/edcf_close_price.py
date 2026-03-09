"""add_close_price

Revision ID: edcfb2e5c68f
Revises: 1234567890ab
Create Date: 2026-03-08 20:58:24.651774

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'edcfb2e5c68f'
down_revision: Union[str, Sequence[str], None] = '1234567890ab'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('daily_derivatives_analysis', sa.Column('close_price', sa.Float(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('daily_derivatives_analysis', 'close_price')
