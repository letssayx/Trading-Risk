"""Fix MTO and Bhavcopy Integer Overflow to BigInt

Revision ID: fix_mto_bigint_001
Revises: ea79cf6bfcdc
Create Date: 2026-02-26 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'fix_mto_bigint_001'
down_revision: Union[str, Sequence[str], None] = 'ea79cf6bfcdc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # mto_delivery
    op.alter_column('mto_delivery', 'quantity_traded', type_=sa.BigInteger(), existing_type=sa.Integer())
    op.alter_column('mto_delivery', 'deliverable_qty', type_=sa.BigInteger(), existing_type=sa.Integer())
    op.alter_column('mto_delivery', 'sr_no', type_=sa.BigInteger(), existing_type=sa.Integer())

    # bhavcopy_eq
    op.alter_column('bhavcopy_eq', 'total_traded_qty', type_=sa.BigInteger(), existing_type=sa.Integer())
    op.alter_column('bhavcopy_eq', 'deliverable_qty', type_=sa.BigInteger(), existing_type=sa.Integer())

    # bhavcopy_fo
    op.alter_column('bhavcopy_fo', 'open_interest', type_=sa.BigInteger(), existing_type=sa.Integer())
    op.alter_column('bhavcopy_fo', 'total_trading_vol', type_=sa.BigInteger(), existing_type=sa.Integer())

    # bulk_deals / block_deals
    op.alter_column('bulk_deals', 'quantity_traded', type_=sa.BigInteger(), existing_type=sa.Integer())
    op.alter_column('block_deals', 'quantity_traded', type_=sa.BigInteger(), existing_type=sa.Integer())


def downgrade() -> None:
    # Revert to Integer (might fail if data > 2B exists)
    op.alter_column('mto_delivery', 'quantity_traded', type_=sa.Integer(), existing_type=sa.BigInteger())
    op.alter_column('mto_delivery', 'deliverable_qty', type_=sa.Integer(), existing_type=sa.BigInteger())
    op.alter_column('mto_delivery', 'sr_no', type_=sa.Integer(), existing_type=sa.BigInteger())

    op.alter_column('bhavcopy_eq', 'total_traded_qty', type_=sa.Integer(), existing_type=sa.BigInteger())
    op.alter_column('bhavcopy_eq', 'deliverable_qty', type_=sa.Integer(), existing_type=sa.BigInteger())

    op.alter_column('bhavcopy_fo', 'open_interest', type_=sa.Integer(), existing_type=sa.BigInteger())
    op.alter_column('bhavcopy_fo', 'total_trading_vol', type_=sa.Integer(), existing_type=sa.BigInteger())

    op.alter_column('bulk_deals', 'quantity_traded', type_=sa.Integer(), existing_type=sa.BigInteger())
    op.alter_column('block_deals', 'quantity_traded', type_=sa.Integer(), existing_type=sa.BigInteger())
