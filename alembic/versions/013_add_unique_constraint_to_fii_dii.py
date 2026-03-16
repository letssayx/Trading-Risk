"""Add unique constraint to fii_dii_cash

Revision ID: 013_fii_dii_unique
Revises: 012_add_vwap
Create Date: 2024-05-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '013_fii_dii_unique'
down_revision = '012_add_vwap'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Add unique constraint to fii_dii_cash table
    op.create_unique_constraint('uq_fii_dii_cash_unique', 'fii_dii_cash', ['trade_date', 'category'])

def downgrade() -> None:
    # Remove unique constraint
    op.drop_constraint('uq_fii_dii_cash_unique', 'fii_dii_cash', type_='unique')
