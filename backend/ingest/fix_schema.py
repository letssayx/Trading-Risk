from sqlalchemy import create_engine, text
import os
import logging
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SchemaFix")

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    logger.error("DATABASE_URL not found")
    exit(1)

engine = create_engine(DATABASE_URL)

def safe_execute(conn, sql, description):
    try:
        conn.execute(text(sql))
        logger.info(f"✓ {description}")
    except Exception as e:
        # Check if error is "does not exist" or similar innocuous error
        msg = str(e).lower()
        if "does not exist" in msg or "already exists" in msg:
            logger.info(f"⚠ {description} (Skipped/Already done: {e})")
        else:
            logger.error(f"✗ {description} failed: {e}")

def fix_mto_delivery(conn):
    logger.info("--- Fixing mto_delivery ---")

    # 1. Fix Column Types (Integer Overflow)
    safe_execute(conn, "ALTER TABLE mto_delivery ALTER COLUMN quantity_traded TYPE BIGINT", "Alter quantity_traded to BIGINT")
    safe_execute(conn, "ALTER TABLE mto_delivery ALTER COLUMN deliverable_qty TYPE BIGINT", "Alter deliverable_qty to BIGINT")

    # 2. Fix Constraints for Hypertable (Must include trade_date)
    # Drop old constraints
    safe_execute(conn, "ALTER TABLE mto_delivery DROP CONSTRAINT IF EXISTS mto_delivery_pkey CASCADE", "Drop old PK")
    safe_execute(conn, "ALTER TABLE mto_delivery DROP CONSTRAINT IF EXISTS uq_mto_delivery_unique CASCADE", "Drop old Unique Constraint")

    # Add new constraints
    safe_execute(conn, "ALTER TABLE mto_delivery ADD CONSTRAINT mto_delivery_pkey PRIMARY KEY (trade_date, id)", "Add composite PK (trade_date, id)")
    safe_execute(conn, "ALTER TABLE mto_delivery ADD CONSTRAINT uq_mto_delivery_unique UNIQUE (trade_date, security_name)", "Add unique constraint (trade_date, security_name)")

def fix_pe_ratio(conn):
    logger.info("--- Fixing pe_ratio ---")

    safe_execute(conn, "ALTER TABLE pe_ratio DROP CONSTRAINT IF EXISTS pe_ratio_pkey CASCADE", "Drop old PK")
    safe_execute(conn, "ALTER TABLE pe_ratio DROP CONSTRAINT IF EXISTS uq_pe_ratio_unique CASCADE", "Drop old Unique Constraint")

    safe_execute(conn, "ALTER TABLE pe_ratio ADD CONSTRAINT pe_ratio_pkey PRIMARY KEY (date, id)", "Add composite PK (date, id)")
    safe_execute(conn, "ALTER TABLE pe_ratio ADD CONSTRAINT uq_pe_ratio_unique UNIQUE (date, symbol)", "Add unique constraint (date, symbol)")

def fix_deals(conn):
    logger.info("--- Fixing bulk_deals and block_deals ---")

    # Bulk Deals
    safe_execute(conn, "ALTER TABLE bulk_deals DROP CONSTRAINT IF EXISTS bulk_deals_pkey CASCADE", "Drop bulk_deals PK")
    safe_execute(conn, "ALTER TABLE bulk_deals ADD CONSTRAINT bulk_deals_pkey PRIMARY KEY (date, id)", "Add bulk_deals composite PK")
    # Remove unique constraint if any (we allow duplicates for deals now as per logic)
    safe_execute(conn, "ALTER TABLE bulk_deals DROP CONSTRAINT IF EXISTS uq_bulk_deals_unique CASCADE", "Drop bulk_deals unique constraint")

    # Block Deals
    safe_execute(conn, "ALTER TABLE block_deals DROP CONSTRAINT IF EXISTS block_deals_pkey CASCADE", "Drop block_deals PK")
    safe_execute(conn, "ALTER TABLE block_deals ADD CONSTRAINT block_deals_pkey PRIMARY KEY (date, id)", "Add block_deals composite PK")
    safe_execute(conn, "ALTER TABLE block_deals DROP CONSTRAINT IF EXISTS uq_block_deals_unique CASCADE", "Drop block_deals unique constraint")

def fix_mwpl(conn):
    logger.info("--- Fixing mwpl_client_position ---")
    safe_execute(conn, "ALTER TABLE mwpl_client_position DROP CONSTRAINT IF EXISTS mwpl_client_position_pkey CASCADE", "Drop old PK")
    safe_execute(conn, "ALTER TABLE mwpl_client_position ADD CONSTRAINT mwpl_client_position_pkey PRIMARY KEY (date, id)", "Add composite PK")

    safe_execute(conn, "ALTER TABLE mwpl_client_position DROP CONSTRAINT IF EXISTS uq_mwpl_unique CASCADE", "Drop old Unique")
    safe_execute(conn, "ALTER TABLE mwpl_client_position ADD CONSTRAINT uq_mwpl_unique UNIQUE (date, underlying_stock, client_position_num)", "Add Unique Constraint")

def fix_fii_stats(conn):
    logger.info("--- Fixing fii_derivatives_stats ---")
    safe_execute(conn, "ALTER TABLE fii_derivatives_stats DROP CONSTRAINT IF EXISTS fii_derivatives_stats_pkey CASCADE", "Drop old PK")
    safe_execute(conn, "ALTER TABLE fii_derivatives_stats ADD CONSTRAINT fii_derivatives_stats_pkey PRIMARY KEY (date, id)", "Add composite PK")

    safe_execute(conn, "ALTER TABLE fii_derivatives_stats DROP CONSTRAINT IF EXISTS uq_fii_stats_unique CASCADE", "Drop old Unique")
    safe_execute(conn, "ALTER TABLE fii_derivatives_stats ADD CONSTRAINT uq_fii_stats_unique UNIQUE (date, instrument_type)", "Add Unique Constraint")

def fix_bhavcopies(conn):
    logger.info("--- Fixing bhavcopies ---")
    # EQ
    safe_execute(conn, "ALTER TABLE bhavcopy_eq DROP CONSTRAINT IF EXISTS bhavcopy_eq_pkey CASCADE", "Drop EQ PK")
    safe_execute(conn, "ALTER TABLE bhavcopy_eq ADD CONSTRAINT bhavcopy_eq_pkey PRIMARY KEY (trade_date, id)", "Add EQ PK")

    # FO
    safe_execute(conn, "ALTER TABLE bhavcopy_fo DROP CONSTRAINT IF EXISTS bhavcopy_fo_pkey CASCADE", "Drop FO PK")
    safe_execute(conn, "ALTER TABLE bhavcopy_fo ADD CONSTRAINT bhavcopy_fo_pkey PRIMARY KEY (trade_date, id)", "Add FO PK")


if __name__ == "__main__":
    print("Starting Schema Fix...")
    try:
        with engine.connect() as conn:
            # We must commit after DDLS usually, or use autocommit
            conn.execution_options(isolation_level="AUTOCOMMIT")

            fix_mto_delivery(conn)
            fix_pe_ratio(conn)
            fix_deals(conn)
            fix_mwpl(conn)
            fix_fii_stats(conn)
            fix_bhavcopies(conn)

            print("Schema Fix Completed.")
    except Exception as e:
        print(f"Global Error: {e}")
