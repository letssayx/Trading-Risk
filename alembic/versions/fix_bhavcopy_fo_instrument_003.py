"""Add instrument_type to BhavcopyFO

Revision ID: fix_bhavcopy_fo_instrument_003
Revises: fix_timescale_pks_002
Create Date: 2026-02-26 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fix_bhavcopy_fo_instrument_003'
down_revision: Union[str, Sequence[str], None] = 'fix_timescale_pks_002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add instrument_type column to bhavcopy_fo
    op.add_column('bhavcopy_fo', sa.Column('instrument_type', sa.String(length=20), nullable=True))
    op.create_index('ix_bhavcopy_fo_instrument_type', 'bhavcopy_fo', ['instrument_type'], unique=False)


def downgrade() -> None:
    # Remove instrument_type column from bhavcopy_fo
    op.drop_index('ix_bhavcopy_fo_instrument_type', table_name='bhavcopy_fo')
    op.drop_column('bhavcopy_fo', 'instrument_type')
