"""add_close_price_and_oi_metrics

Revision ID: a836a8ddcd34
Revises: 1234567890ab
Create Date: 2026-03-09 11:26:48.938785

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a836a8ddcd34'
down_revision: Union[str, Sequence[str], None] = '1234567890ab'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('daily_derivatives_analysis', sa.Column('close_price', sa.Float(), nullable=True))
    op.add_column('daily_derivatives_analysis', sa.Column('highest_oi_strike_pe', sa.Float(), nullable=True))
    op.add_column('daily_derivatives_analysis', sa.Column('highest_oi_strike_ce', sa.Float(), nullable=True))
    op.add_column('daily_derivatives_analysis', sa.Column('chg_oi_options', sa.BigInteger(), nullable=True))
    op.add_column('daily_derivatives_analysis', sa.Column('chg_oi_futures', sa.BigInteger(), nullable=True))
    op.add_column('daily_derivatives_analysis', sa.Column('total_options_call_oi', sa.BigInteger(), nullable=True))
    op.add_column('daily_derivatives_analysis', sa.Column('total_options_put_oi', sa.BigInteger(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('daily_derivatives_analysis', 'total_options_put_oi')
    op.drop_column('daily_derivatives_analysis', 'total_options_call_oi')
    op.drop_column('daily_derivatives_analysis', 'chg_oi_futures')
    op.drop_column('daily_derivatives_analysis', 'chg_oi_options')
    op.drop_column('daily_derivatives_analysis', 'highest_oi_strike_ce')
    op.drop_column('daily_derivatives_analysis', 'highest_oi_strike_pe')
    op.drop_column('daily_derivatives_analysis', 'close_price')
