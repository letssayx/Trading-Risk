"""create mr new metrics

Revision ID: 011_mr_metrics
Revises: 010_fii_dii_cash
Create Date: 2026-03-10 12:05:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '011_mr_metrics'
down_revision = '010_fii_dii_cash'
branch_labels = None
depends_on = None

def upgrade() -> None:
    from sqlalchemy.engine.reflection import Inspector
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    existing_columns = [col['name'] for col in inspector.get_columns('daily_derivatives_analysis')]

    if 'pct_away_highest_pe' not in existing_columns:
        op.add_column('daily_derivatives_analysis', sa.Column('pct_away_highest_pe', sa.Float(), nullable=True))
    if 'pct_away_highest_ce' not in existing_columns:
        op.add_column('daily_derivatives_analysis', sa.Column('pct_away_highest_ce', sa.Float(), nullable=True))
    if 'near_expiry_date' not in existing_columns:
        op.add_column('daily_derivatives_analysis', sa.Column('near_expiry_date', sa.Date(), nullable=True))
    if 'next_expiry_date' not in existing_columns:
        op.add_column('daily_derivatives_analysis', sa.Column('next_expiry_date', sa.Date(), nullable=True))
    if 'far_expiry_date' not in existing_columns:
        op.add_column('daily_derivatives_analysis', sa.Column('far_expiry_date', sa.Date(), nullable=True))
    if 'iv_rank_252' not in existing_columns:
        op.add_column('daily_derivatives_analysis', sa.Column('iv_rank_252', sa.Float(), nullable=True))
    if 'iv_percentile_252' not in existing_columns:
        op.add_column('daily_derivatives_analysis', sa.Column('iv_percentile_252', sa.Float(), nullable=True))
    if 'price_pct_change' not in existing_columns:
        op.add_column('daily_derivatives_analysis', sa.Column('price_pct_change', sa.Float(), nullable=True))
    if 'relative_volume_20d' not in existing_columns:
        op.add_column('daily_derivatives_analysis', sa.Column('relative_volume_20d', sa.Float(), nullable=True))

def downgrade() -> None:
    from sqlalchemy.engine.reflection import Inspector
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    existing_columns = [col['name'] for col in inspector.get_columns('daily_derivatives_analysis')]

    if 'relative_volume_20d' in existing_columns:
        op.drop_column('daily_derivatives_analysis', 'relative_volume_20d')
    if 'price_pct_change' in existing_columns:
        op.drop_column('daily_derivatives_analysis', 'price_pct_change')
    if 'iv_percentile_252' in existing_columns:
        op.drop_column('daily_derivatives_analysis', 'iv_percentile_252')
    if 'iv_rank_252' in existing_columns:
        op.drop_column('daily_derivatives_analysis', 'iv_rank_252')
    if 'far_expiry_date' in existing_columns:
        op.drop_column('daily_derivatives_analysis', 'far_expiry_date')
    if 'next_expiry_date' in existing_columns:
        op.drop_column('daily_derivatives_analysis', 'next_expiry_date')
    if 'near_expiry_date' in existing_columns:
        op.drop_column('daily_derivatives_analysis', 'near_expiry_date')
    if 'pct_away_highest_ce' in existing_columns:
        op.drop_column('daily_derivatives_analysis', 'pct_away_highest_ce')
    if 'pct_away_highest_pe' in existing_columns:
        op.drop_column('daily_derivatives_analysis', 'pct_away_highest_pe')
