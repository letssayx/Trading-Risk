"""Add close_price to DailyDerivativesAnalysis

Revision ID: add_close_price_to_daily_deriv
Revises: 1234567890ab
Create Date: 2024-03-08 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_close_price_to_daily_deriv'
down_revision = '1234567890ab'
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.add_column('daily_derivatives_analysis', sa.Column('close_price', sa.Float(), nullable=True))

def downgrade() -> None:
    op.drop_column('daily_derivatives_analysis', 'close_price')
