"""Add missing PG16 performance indexes

Revision ID: db82b7bab012
Revises: 20260714072610
Create Date: 2026-07-14 09:39:16.503319

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'db82b7bab012'
down_revision: Union[str, Sequence[str], None] = '20260714072610'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_index('idx_bhavcopy_eq_sym_series_date', 'bhavcopy_eq', ['symbol', 'series', 'trade_date'], if_not_exists=True)
    op.create_index('idx_bhavcopy_fo_inst_type', 'bhavcopy_fo', ['instrument_type'], if_not_exists=True)
    op.create_index('idx_bhavcopy_fo_sym_date_inst', 'bhavcopy_fo', ['ticker_symb', 'trade_date', 'instrument_type'], if_not_exists=True)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('idx_bhavcopy_eq_sym_series_date', table_name='bhavcopy_eq', if_exists=True)
    op.drop_index('idx_bhavcopy_fo_inst_type', table_name='bhavcopy_fo', if_exists=True)
    op.drop_index('idx_bhavcopy_fo_sym_date_inst', table_name='bhavcopy_fo', if_exists=True)
