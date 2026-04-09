"""Add OiAnalysisMetrics

Revision ID: f4a6ff141c09
Revises: 016_bhavcopy_fo_duplicates_fix
Create Date: 2026-04-08 04:35:41.572219

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'f4a6ff141c09'
down_revision: Union[str, Sequence[str], None] = '016_bhavcopy_fo_duplicates_fix'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'oi_analysis_metrics',
        sa.Column('id', sa.Integer(), sa.Identity(always=False, start=1), nullable=False),
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
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('trade_date', 'symbol', name='pk_oi_analysis_metrics'),
        sa.UniqueConstraint('trade_date', 'symbol', name='uq_oi_analysis_metrics_date_symbol')
    )
    op.create_index(op.f('ix_oi_analysis_metrics_symbol'), 'oi_analysis_metrics', ['symbol'], unique=False)
    op.create_index(op.f('ix_oi_analysis_metrics_trade_date'), 'oi_analysis_metrics', ['trade_date'], unique=False)
    try:
        op.execute("SELECT create_hypertable('oi_analysis_metrics', 'trade_date', if_not_exists => TRUE);")
    except Exception:
        pass


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_oi_analysis_metrics_trade_date'), table_name='oi_analysis_metrics')
    op.drop_index(op.f('ix_oi_analysis_metrics_symbol'), table_name='oi_analysis_metrics')
    op.drop_table('oi_analysis_metrics')
