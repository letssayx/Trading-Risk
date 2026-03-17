"""Add highest OI and eq close columns

Revision ID: highest_oi_cols
Revises: straddle_cols
Create Date: 2024-03-20 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector

# revision identifiers, used by Alembic.
revision = 'highest_oi_cols'
down_revision = "create_historical_index"
branch_labels = None
depends_on = None

def upgrade() -> None:
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    existing_columns = [c['name'] for c in inspector.get_columns('daily_derivatives_analysis')]

    if 'highest_oi_pe_oi' not in existing_columns:
        op.add_column('daily_derivatives_analysis', sa.Column('highest_oi_pe_oi', sa.BigInteger(), nullable=True))
    if 'highest_oi_ce_oi' not in existing_columns:
        op.add_column('daily_derivatives_analysis', sa.Column('highest_oi_ce_oi', sa.BigInteger(), nullable=True))

def downgrade() -> None:
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    existing_columns = [c['name'] for c in inspector.get_columns('daily_derivatives_analysis')]

    if 'highest_oi_pe_oi' in existing_columns:
        op.drop_column('daily_derivatives_analysis', 'highest_oi_pe_oi')
    if 'highest_oi_ce_oi' in existing_columns:
        op.drop_column('daily_derivatives_analysis', 'highest_oi_ce_oi')
