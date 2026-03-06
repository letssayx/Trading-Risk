"""add_bhavcopy_fo_composite_index

Revision ID: 1234567890ab
Revises: add_inst_type_bhav_fo_009
Create Date: 2026-03-06 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '1234567890ab'
down_revision = 'add_inst_type_bhav_fo_009'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Add composite index for sorting by trade_date DESC, ticker_symb ASC
    op.create_index('idx_bhavcopy_fo_date_symb', 'bhavcopy_fo', ['trade_date', 'ticker_symb'], unique=False)

def downgrade() -> None:
    # Remove the index if we need to rollback
    op.drop_index('idx_bhavcopy_fo_date_symb', table_name='bhavcopy_fo')
