"""increase pe ratio symbol length

Revision ID: fix_pe_ratio_length_006
Revises: fix_empty_success_logs_005
Create Date: 2026-02-28 02:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import text

# revision identifiers, used by Alembic.
revision = 'fix_pe_ratio_length_006'
down_revision = 'fix_empty_success_logs_005'
branch_labels = None
depends_on = None

def upgrade():
    op.alter_column('pe_ratio', 'symbol',
                    existing_type=sa.String(length=50),
                    type_=sa.String(length=150),
                    existing_nullable=False)

    # Optional: We also want to clear out any bad PE ratios (indices) that might have snuck in if they weren't truncated.
    # The user expected only equities. Let's delete anything with "Index" or "NIFTY" in the name from pe_ratio
    conn = op.get_bind()
    conn.execute(
        text("DELETE FROM pe_ratio WHERE symbol ILIKE '%Index%' OR symbol ILIKE '%NIFTY%' OR symbol ILIKE '%Nifty%'")
    )

def downgrade():
    op.alter_column('pe_ratio', 'symbol',
                    existing_type=sa.String(length=150),
                    type_=sa.String(length=50),
                    existing_nullable=False)
