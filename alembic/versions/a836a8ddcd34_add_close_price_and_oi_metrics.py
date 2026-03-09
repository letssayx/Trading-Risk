"""add_close_price_and_oi_metrics

Revision ID: a836a8ddcd34
Revises: 1234567890ab
Create Date: 2026-03-09 11:26:48.938785

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector


# revision identifiers, used by Alembic.
revision: str = 'a836a8ddcd34'
down_revision: Union[str, Sequence[str], None] = '1234567890ab'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    existing_columns = [col['name'] for col in inspector.get_columns('daily_derivatives_analysis')]

    if 'close_price' not in existing_columns:
        op.add_column('daily_derivatives_analysis', sa.Column('close_price', sa.Float(), nullable=True))
    if 'highest_oi_strike_pe' not in existing_columns:
        op.add_column('daily_derivatives_analysis', sa.Column('highest_oi_strike_pe', sa.Float(), nullable=True))
    if 'highest_oi_strike_ce' not in existing_columns:
        op.add_column('daily_derivatives_analysis', sa.Column('highest_oi_strike_ce', sa.Float(), nullable=True))
    if 'chg_oi_options' not in existing_columns:
        op.add_column('daily_derivatives_analysis', sa.Column('chg_oi_options', sa.BigInteger(), nullable=True))
    if 'chg_oi_futures' not in existing_columns:
        op.add_column('daily_derivatives_analysis', sa.Column('chg_oi_futures', sa.BigInteger(), nullable=True))
    if 'total_options_call_oi' not in existing_columns:
        op.add_column('daily_derivatives_analysis', sa.Column('total_options_call_oi', sa.BigInteger(), nullable=True))
    if 'total_options_put_oi' not in existing_columns:
        op.add_column('daily_derivatives_analysis', sa.Column('total_options_put_oi', sa.BigInteger(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    existing_columns = [col['name'] for col in inspector.get_columns('daily_derivatives_analysis')]

    if 'total_options_put_oi' in existing_columns:
        op.drop_column('daily_derivatives_analysis', 'total_options_put_oi')
    if 'total_options_call_oi' in existing_columns:
        op.drop_column('daily_derivatives_analysis', 'total_options_call_oi')
    if 'chg_oi_futures' in existing_columns:
        op.drop_column('daily_derivatives_analysis', 'chg_oi_futures')
    if 'chg_oi_options' in existing_columns:
        op.drop_column('daily_derivatives_analysis', 'chg_oi_options')
    if 'highest_oi_strike_ce' in existing_columns:
        op.drop_column('daily_derivatives_analysis', 'highest_oi_strike_ce')
    if 'highest_oi_strike_pe' in existing_columns:
        op.drop_column('daily_derivatives_analysis', 'highest_oi_strike_pe')
    if 'close_price' in existing_columns:
        op.drop_column('daily_derivatives_analysis', 'close_price')
