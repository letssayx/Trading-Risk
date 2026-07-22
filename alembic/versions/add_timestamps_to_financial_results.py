"""add timestamps to financial results

Revision ID: 52a1b9c2a8c3
Revises:
Create Date: 2026-07-22 22:45:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '52a1b9c2a8c3'
down_revision = 'b6f693c0aeff'  # Hooking it into the recent tree
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Add created_at and updated_at columns
    op.add_column('financial_results', sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True))
    op.add_column('financial_results', sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True))

def downgrade() -> None:
    op.drop_column('financial_results', 'updated_at')
    op.drop_column('financial_results', 'created_at')
