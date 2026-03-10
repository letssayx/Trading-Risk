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
    op.add_column('daily_derivatives_analysis', sa.Column('pct_away_highest_pe', sa.Float(), nullable=True))
    op.add_column('daily_derivatives_analysis', sa.Column('pct_away_highest_ce', sa.Float(), nullable=True))
    op.add_column('daily_derivatives_analysis', sa.Column('near_expiry_date', sa.Date(), nullable=True))
    op.add_column('daily_derivatives_analysis', sa.Column('next_expiry_date', sa.Date(), nullable=True))
    op.add_column('daily_derivatives_analysis', sa.Column('far_expiry_date', sa.Date(), nullable=True))
    op.add_column('daily_derivatives_analysis', sa.Column('iv_rank_252', sa.Float(), nullable=True))
    op.add_column('daily_derivatives_analysis', sa.Column('iv_percentile_252', sa.Float(), nullable=True))
    op.add_column('daily_derivatives_analysis', sa.Column('price_pct_change', sa.Float(), nullable=True))
    op.add_column('daily_derivatives_analysis', sa.Column('relative_volume_20d', sa.Float(), nullable=True))

def downgrade() -> None:
    op.drop_column('daily_derivatives_analysis', 'relative_volume_20d')
    op.drop_column('daily_derivatives_analysis', 'price_pct_change')
    op.drop_column('daily_derivatives_analysis', 'iv_percentile_252')
    op.drop_column('daily_derivatives_analysis', 'iv_rank_252')
    op.drop_column('daily_derivatives_analysis', 'far_expiry_date')
    op.drop_column('daily_derivatives_analysis', 'next_expiry_date')
    op.drop_column('daily_derivatives_analysis', 'near_expiry_date')
    op.drop_column('daily_derivatives_analysis', 'pct_away_highest_ce')
    op.drop_column('daily_derivatives_analysis', 'pct_away_highest_pe')
