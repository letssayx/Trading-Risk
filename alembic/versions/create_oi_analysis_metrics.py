"""create_oi_analysis_metrics

Revision ID: create_oi_analysis_metrics
Revises: 5218b0821c97
Create Date: 2024-05-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'create_oi_analysis_metrics'
down_revision = '5218b0821c97'
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        'oi_analysis_metrics',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('trade_date', sa.Date(), nullable=False),
        sa.Column('symbol', sa.String(length=50), nullable=False),
        sa.Column('price', sa.Float(), nullable=True),
        sa.Column('price_chg_pct', sa.Float(), nullable=True),
        sa.Column('fut_oi', sa.BigInteger(), nullable=True),
        sa.Column('call_oi', sa.BigInteger(), nullable=True),
        sa.Column('put_oi', sa.BigInteger(), nullable=True),
        sa.Column('total_oi', sa.BigInteger(), nullable=True),
        sa.Column('fut_oi_chg_pct', sa.Float(), nullable=True),
        sa.Column('call_oi_chg_pct', sa.Float(), nullable=True),
        sa.Column('put_oi_chg_pct', sa.Float(), nullable=True),
        sa.Column('oi_chg_pct', sa.Float(), nullable=True),
        sa.Column('fut_oi_chg_pct_30d', sa.Float(), nullable=True),
        sa.Column('call_oi_chg_pct_30d', sa.Float(), nullable=True),
        sa.Column('put_oi_chg_pct_30d', sa.Float(), nullable=True),
        sa.Column('fut_oi_chg', sa.BigInteger(), nullable=True),
        sa.Column('call_oi_chg', sa.BigInteger(), nullable=True),
        sa.Column('put_oi_chg', sa.BigInteger(), nullable=True),
        sa.Column('pcr', sa.Float(), nullable=True),
        sa.Column('atm_iv', sa.Float(), nullable=True),
        sa.PrimaryKeyConstraint('trade_date', 'symbol', name='pk_oi_analysis_metrics'),
        sa.UniqueConstraint('trade_date', 'symbol', name='uq_oi_analysis_metrics_date_symbol')
    )
    op.create_index(op.f('ix_oi_analysis_metrics_symbol'), 'oi_analysis_metrics', ['symbol'], unique=False)
    op.create_index(op.f('ix_oi_analysis_metrics_trade_date'), 'oi_analysis_metrics', ['trade_date'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_oi_analysis_metrics_trade_date'), table_name='oi_analysis_metrics')
    op.drop_index(op.f('ix_oi_analysis_metrics_symbol'), table_name='oi_analysis_metrics')
    op.drop_table('oi_analysis_metrics')
