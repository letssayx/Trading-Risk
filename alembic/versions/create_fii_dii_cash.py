"""create fii dii cash table

Revision ID: 010_fii_dii_cash
Revises: 009_add_inst_type_bhav_fo
Create Date: 2026-03-10 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '010_fii_dii_cash'
down_revision = 'add_inst_type_bhav_fo_009'
branch_labels = None
depends_on = None

def upgrade() -> None:
    from sqlalchemy.engine.reflection import Inspector
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    tables = inspector.get_table_names()

    if 'fii_dii_cash' not in tables:
        # create table
        op.create_table('fii_dii_cash',
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('trade_date', sa.Date(), nullable=False),
            sa.Column('category', sa.String(length=50), nullable=False),
            sa.Column('buy_value', sa.Float(), nullable=True),
            sa.Column('sell_value', sa.Float(), nullable=True),
            sa.Column('net_value', sa.Float(), nullable=True),
            sa.PrimaryKeyConstraint('id', 'trade_date')
        )
        op.create_index('idx_fii_dii_cash_date', 'fii_dii_cash', ['trade_date'], unique=False)

        # Note: TimescaleDB hypertable is created by init_db scripts usually, but adding it here is safe.
        op.execute("SELECT create_hypertable('fii_dii_cash', 'trade_date', if_not_exists => TRUE);")

def downgrade() -> None:
    from sqlalchemy.engine.reflection import Inspector
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    tables = inspector.get_table_names()
    if 'fii_dii_cash' in tables:
        op.drop_index('idx_fii_dii_cash_date', table_name='fii_dii_cash')
        op.drop_table('fii_dii_cash')
