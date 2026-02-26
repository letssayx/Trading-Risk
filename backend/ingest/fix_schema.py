import logging
from sqlalchemy import text
from backend.infrastructure.db import engine

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

def fix_schema():
    """
    Consolidated migration script to fix schema issues.

    1. Alters mto_delivery columns to BIGINT (quantity_traded, deliverable_qty, sr_no).
    2. Drops UNIQUE constraints on bulk_deals and block_deals to allow duplicate entries.
    """
    logger.info("Starting schema fix migration...")

    with engine.connect() as conn:
        with conn.begin(): # Start a transaction

            # --- 1. Fix mto_delivery columns ---
            logger.info("--- Fixing mto_delivery columns ---")
            mto_commands = [
                "ALTER TABLE mto_delivery ALTER COLUMN quantity_traded TYPE BIGINT;",
                "ALTER TABLE mto_delivery ALTER COLUMN deliverable_qty TYPE BIGINT;",
                "ALTER TABLE mto_delivery ALTER COLUMN sr_no TYPE BIGINT;"
            ]

            for cmd in mto_commands:
                try:
                    logger.info(f"Executing: {cmd}")
                    conn.execute(text(cmd))
                except Exception as e:
                    # Log error but continue (might already be BIGINT)
                    logger.warning(f"Failed to execute {cmd}: {e}")

            # --- 2. Drop unique constraints on deals ---
            logger.info("--- Dropping unique constraints on deals ---")
            tables_to_fix = ['bulk_deals', 'block_deals']

            for table in tables_to_fix:
                # Find unique constraints (contype='u') on the table
                query = text("""
                    SELECT conname
                    FROM pg_constraint
                    WHERE conrelid = :table::regclass AND contype = 'u';
                """)

                try:
                    constraints = conn.execute(query, {"table": table}).fetchall()

                    if not constraints:
                        logger.info(f"No unique constraints found on {table}.")
                        continue

                    for row in constraints:
                        constraint_name = row[0] # row is a tuple/Row object
                        drop_cmd = f"ALTER TABLE {table} DROP CONSTRAINT IF EXISTS {constraint_name};"
                        logger.info(f"Dropping constraint {constraint_name} on {table}...")
                        try:
                            conn.execute(text(drop_cmd))
                            logger.info(f"Successfully dropped {constraint_name}.")
                        except Exception as e:
                            logger.error(f"Failed to drop constraint {constraint_name}: {e}")

                except Exception as e:
                    logger.error(f"Error checking constraints for {table}: {e}")

    logger.info("Schema fix migration completed.")

if __name__ == "__main__":
    fix_schema()
