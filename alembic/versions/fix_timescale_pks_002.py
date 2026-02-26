"""Fix TimescaleDB Constraints (Composite PKs)

Revision ID: fix_timescale_pks_002
Revises: fix_mto_bigint_001
Create Date: 2026-02-26 13:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'fix_timescale_pks_002'
down_revision: Union[str, Sequence[str], None] = 'fix_mto_bigint_001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. MTO Delivery
    # Drop old constraints
    op.execute("ALTER TABLE mto_delivery DROP CONSTRAINT IF EXISTS mto_delivery_pkey CASCADE")
    op.execute("ALTER TABLE mto_delivery DROP CONSTRAINT IF EXISTS uq_mto_delivery_unique CASCADE")
    # Add new constraints (include trade_date for hypertable)
    op.create_primary_key("mto_delivery_pkey", "mto_delivery", ["trade_date", "id"])
    op.create_unique_constraint("uq_mto_delivery_unique", "mto_delivery", ["trade_date", "security_name"])

    # 2. PE Ratio
    op.execute("ALTER TABLE pe_ratio DROP CONSTRAINT IF EXISTS pe_ratio_pkey CASCADE")
    op.execute("ALTER TABLE pe_ratio DROP CONSTRAINT IF EXISTS uq_pe_ratio_unique CASCADE")
    op.create_primary_key("pe_ratio_pkey", "pe_ratio", ["date", "id"])
    op.create_unique_constraint("uq_pe_ratio_unique", "pe_ratio", ["date", "symbol"])

    # 3. MWPL Client Position
    op.execute("ALTER TABLE mwpl_client_position DROP CONSTRAINT IF EXISTS mwpl_client_position_pkey CASCADE")
    op.execute("ALTER TABLE mwpl_client_position DROP CONSTRAINT IF EXISTS uq_mwpl_unique CASCADE")
    op.create_primary_key("mwpl_client_position_pkey", "mwpl_client_position", ["date", "id"])
    op.create_unique_constraint("uq_mwpl_unique", "mwpl_client_position", ["date", "underlying_stock", "client_position_num"])

    # 4. FII Derivatives Stats
    op.execute("ALTER TABLE fii_derivatives_stats DROP CONSTRAINT IF EXISTS fii_derivatives_stats_pkey CASCADE")
    op.execute("ALTER TABLE fii_derivatives_stats DROP CONSTRAINT IF EXISTS uq_fii_stats_unique CASCADE")
    op.create_primary_key("fii_derivatives_stats_pkey", "fii_derivatives_stats", ["date", "id"])
    op.create_unique_constraint("uq_fii_stats_unique", "fii_derivatives_stats", ["date", "instrument_type"])

    # 5. Bhavcopy EQ
    op.execute("ALTER TABLE bhavcopy_eq DROP CONSTRAINT IF EXISTS bhavcopy_eq_pkey CASCADE")
    # Unique constraint uq_bhavcopy_eq_unique already includes trade_date, usually?
    # Let's check model: UniqueConstraint('symbol', 'series', 'trade_date') - Yes.
    # But PK needs to be composite.
    op.create_primary_key("bhavcopy_eq_pkey", "bhavcopy_eq", ["trade_date", "id"])

    # 6. Bhavcopy FO
    op.execute("ALTER TABLE bhavcopy_fo DROP CONSTRAINT IF EXISTS bhavcopy_fo_pkey CASCADE")
    # Unique constraint uq_bhavcopy_fo_unique already includes trade_date?
    # Model: ('trade_date', 'ticker_symb', 'expiry_date', ...) - Yes.
    op.create_primary_key("bhavcopy_fo_pkey", "bhavcopy_fo", ["trade_date", "id"])

    # 7. Deals (Remove Unique Constraints to allow duplicates/Delete-Insert)
    op.execute("ALTER TABLE bulk_deals DROP CONSTRAINT IF EXISTS uq_bulk_deals_unique CASCADE")
    op.execute("ALTER TABLE bulk_deals DROP CONSTRAINT IF EXISTS bulk_deals_pkey CASCADE")
    op.create_primary_key("bulk_deals_pkey", "bulk_deals", ["date", "id"])

    op.execute("ALTER TABLE block_deals DROP CONSTRAINT IF EXISTS uq_block_deals_unique CASCADE")
    op.execute("ALTER TABLE block_deals DROP CONSTRAINT IF EXISTS block_deals_pkey CASCADE")
    op.create_primary_key("block_deals_pkey", "block_deals", ["date", "id"])


def downgrade() -> None:
    # Revert is complex because we need to know original constraints.
    # Assuming original was just PK on ID and Unique without date (for some tables).

    # This is a best-effort downgrade.

    # MTO
    op.execute("ALTER TABLE mto_delivery DROP CONSTRAINT IF EXISTS mto_delivery_pkey CASCADE")
    op.create_primary_key("mto_delivery_pkey", "mto_delivery", ["id"])
    # Original unique might have been just security_name (unlikely for time series) but let's assume so or leave it dropped.

    # PE
    op.execute("ALTER TABLE pe_ratio DROP CONSTRAINT IF EXISTS pe_ratio_pkey CASCADE")
    op.create_primary_key("pe_ratio_pkey", "pe_ratio", ["id"])

    # MWPL
    op.execute("ALTER TABLE mwpl_client_position DROP CONSTRAINT IF EXISTS mwpl_client_position_pkey CASCADE")
    op.create_primary_key("mwpl_client_position_pkey", "mwpl_client_position", ["id"])

    # FII
    op.execute("ALTER TABLE fii_derivatives_stats DROP CONSTRAINT IF EXISTS fii_derivatives_stats_pkey CASCADE")
    op.create_primary_key("fii_derivatives_stats_pkey", "fii_derivatives_stats", ["id"])

    # Bhavcopies
    op.execute("ALTER TABLE bhavcopy_eq DROP CONSTRAINT IF EXISTS bhavcopy_eq_pkey CASCADE")
    op.create_primary_key("bhavcopy_eq_pkey", "bhavcopy_eq", ["id"])

    op.execute("ALTER TABLE bhavcopy_fo DROP CONSTRAINT IF EXISTS bhavcopy_fo_pkey CASCADE")
    op.create_primary_key("bhavcopy_fo_pkey", "bhavcopy_fo", ["id"])

    # Deals
    op.execute("ALTER TABLE bulk_deals DROP CONSTRAINT IF EXISTS bulk_deals_pkey CASCADE")
    op.create_primary_key("bulk_deals_pkey", "bulk_deals", ["id"])

    op.execute("ALTER TABLE block_deals DROP CONSTRAINT IF EXISTS block_deals_pkey CASCADE")
    op.create_primary_key("block_deals_pkey", "block_deals", ["id"])
