"""add straddle and eq cols

Revision ID: create_straddle_cols
Revises: 013_fii_dii_unique
Create Date: 2024-03-12 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'create_straddle_cols'
down_revision = '013_fii_dii_unique'
branch_labels = None
depends_on = None


def upgrade() -> None:
    from sqlalchemy.engine.reflection import Inspector
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    existing_columns = [col['name'] for col in inspector.get_columns('daily_derivatives_analysis')]

    if 'eq_close_price' not in existing_columns:
        op.add_column('daily_derivatives_analysis', sa.Column('eq_close_price', sa.Float(), nullable=True))
    if 'highest_oi_pe_value' not in existing_columns:
        op.add_column('daily_derivatives_analysis', sa.Column('highest_oi_pe_value', sa.Float(), nullable=True))
    if 'highest_oi_ce_value' not in existing_columns:
        op.add_column('daily_derivatives_analysis', sa.Column('highest_oi_ce_value', sa.Float(), nullable=True))
    if 'atm_straddle_near_month' not in existing_columns:
        op.add_column('daily_derivatives_analysis', sa.Column('atm_straddle_near_month', sa.Float(), nullable=True))
    if 'atm_straddle_weekly_nifty' not in existing_columns:
        op.add_column('daily_derivatives_analysis', sa.Column('atm_straddle_weekly_nifty', sa.Float(), nullable=True))

def downgrade() -> None:
    from sqlalchemy.engine.reflection import Inspector
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    existing_columns = [col['name'] for col in inspector.get_columns('daily_derivatives_analysis')]

    if 'eq_close_price' in existing_columns:
        op.drop_column('daily_derivatives_analysis', 'eq_close_price')
    if 'highest_oi_pe_value' in existing_columns:
        op.drop_column('daily_derivatives_analysis', 'highest_oi_pe_value')
    if 'highest_oi_ce_value' in existing_columns:
        op.drop_column('daily_derivatives_analysis', 'highest_oi_ce_value')
    if 'atm_straddle_near_month' in existing_columns:
        op.drop_column('daily_derivatives_analysis', 'atm_straddle_near_month')
    if 'atm_straddle_weekly_nifty' in existing_columns:
        op.drop_column('daily_derivatives_analysis', 'atm_straddle_weekly_nifty')
