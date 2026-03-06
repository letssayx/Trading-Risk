"""add instrument_type to uq_bhavcopy_fo_unique

Revision ID: add_instrument_type_uq_bhavcopy_fo_009
Revises: ai_analysis_bank_009
Create Date: 2026-03-06 04:50:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_instrument_type_uq_bhavcopy_fo_009'
down_revision = 'ai_analysis_bank_009'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drop the old constraint
    op.drop_constraint('uq_bhavcopy_fo_unique', 'bhavcopy_fo', type_='unique')
    # Create the new constraint including instrument_type
    op.create_unique_constraint(
        'uq_bhavcopy_fo_unique',
        'bhavcopy_fo',
        ['trade_date', 'ticker_symb', 'instrument_type', 'expiry_date', 'strike_price', 'option_type']
    )


def downgrade() -> None:
    # Drop the new constraint
    op.drop_constraint('uq_bhavcopy_fo_unique', 'bhavcopy_fo', type_='unique')
    # Recreate the old constraint without instrument_type
    op.create_unique_constraint(
        'uq_bhavcopy_fo_unique',
        'bhavcopy_fo',
        ['trade_date', 'ticker_symb', 'expiry_date', 'strike_price', 'option_type']
    )
