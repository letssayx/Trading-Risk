"""Recreate FII DII Cash and Historical Index tables

Revision ID: 20260714062540
Revises:
Create Date: 2026-07-14T06:25:40.312085

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20260714062540'
down_revision = '440393f5b569'  # We will manually set this if needed, or user can merge heads
branch_labels = None
depends_on = None

def upgrade() -> None:
    # 1. Recreate fii_dii_cash
    op.create_table('fii_dii_cash',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('trade_date', sa.Date(), nullable=False),
        sa.Column('category', sa.String(length=50), nullable=False),
        sa.Column('buy_value', sa.Float(), nullable=True),
        sa.Column('sell_value', sa.Float(), nullable=True),
        sa.Column('net_value', sa.Float(), nullable=True),
        sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id', 'trade_date')
    )
    op.create_index('idx_fii_dii_cash_date', 'fii_dii_cash', ['trade_date'], unique=False)
    op.create_unique_constraint('uq_fii_dii_cash_unique', 'fii_dii_cash', ['trade_date', 'category'])

    # 2. Recreate historical_index_data
    op.create_table('historical_index_data',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('index_name', sa.String(length=100), nullable=False),
        sa.Column('trade_date', sa.Date(), nullable=False),
        sa.Column('open_price', sa.Float(), nullable=True),
        sa.Column('high_price', sa.Float(), nullable=True),
        sa.Column('low_price', sa.Float(), nullable=True),
        sa.Column('close_price', sa.Float(), nullable=True),
        sa.Column('previous_close', sa.Float(), nullable=True),
        sa.Column('volume', sa.Float(), nullable=True),
        sa.Column('turnover', sa.Float(), nullable=True),
        sa.Column('pe_ratio', sa.Float(), nullable=True),
        sa.Column('pb_ratio', sa.Float(), nullable=True),
        sa.Column('div_yield', sa.Float(), nullable=True),
        sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id', 'trade_date')
    )
    op.create_index('idx_historical_index_data_name_date', 'historical_index_data', ['index_name', 'trade_date'], unique=False)
    op.create_unique_constraint('uq_historical_index_data_unique', 'historical_index_data', ['index_name', 'trade_date'])

def downgrade() -> None:
    op.drop_table('historical_index_data')
    op.drop_table('fii_dii_cash')
