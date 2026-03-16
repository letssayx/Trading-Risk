"""create historical index data

Revision ID: create_historical_index
Revises: create_straddle_cols
Create Date: 2024-03-12 11:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'create_historical_index'
down_revision = 'create_straddle_cols'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Use raw SQL to handle table creation specifically for TimescaleDB compatibility
    conn = op.get_bind()

    # Check if table exists
    tables = sa.inspect(conn).get_table_names()
    if 'historical_index_data' not in tables:
        # Create standard PostgreSQL table first
        op.create_table('historical_index_data',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('index_name', sa.String(length=100), nullable=False),
            sa.Column('trade_date', sa.Date(), nullable=False),
            sa.Column('open_price', sa.Float(), nullable=True),
            sa.Column('high_price', sa.Float(), nullable=True),
            sa.Column('low_price', sa.Float(), nullable=True),
            sa.Column('close_price', sa.Float(), nullable=True),
            sa.Column('total_traded_qty', sa.BigInteger(), nullable=True),
            sa.Column('turnover_cr', sa.Float(), nullable=True),
            sa.Column('pe_ratio', sa.Float(), nullable=True),
            sa.Column('pb_ratio', sa.Float(), nullable=True),
            sa.Column('div_yield', sa.Float(), nullable=True),
            sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
            sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
            sa.PrimaryKeyConstraint('trade_date', 'id')
        )

        # Create standard constraints and indexes
        op.create_unique_constraint('uq_historical_index_data_unique', 'historical_index_data', ['index_name', 'trade_date'])
        op.create_index('idx_historical_index_data_name_date', 'historical_index_data', ['index_name', 'trade_date'], unique=False)
        op.create_index('ix_historical_index_data_trade_date', 'historical_index_data', ['trade_date'], unique=False)
        op.create_index('ix_historical_index_data_index_name', 'historical_index_data', ['index_name'], unique=False)

        # Convert to TimescaleDB hypertable
        op.execute("SELECT create_hypertable('historical_index_data', 'trade_date', if_not_exists => TRUE);")


def downgrade() -> None:
    conn = op.get_bind()
    tables = sa.inspect(conn).get_table_names()

    if 'historical_index_data' in tables:
        op.drop_index('ix_historical_index_data_index_name', table_name='historical_index_data')
        op.drop_index('ix_historical_index_data_trade_date', table_name='historical_index_data')
        op.drop_index('idx_historical_index_data_name_date', table_name='historical_index_data')
        op.drop_constraint('uq_historical_index_data_unique', 'historical_index_data', type_='unique')
        op.drop_table('historical_index_data')
