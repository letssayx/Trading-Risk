import logging
from sqlalchemy import text
from backend.infrastructure.db import engine

logger = logging.getLogger(__name__)

def fix_mto_schema():
    """
    Migration script to alter mto_delivery columns to BIGINT.
    Run this manually or via a startup hook.
    """
    try:
        with engine.connect() as conn:
            logger.info("Checking mto_delivery schema...")

            # Alter columns to BIGINT
            logger.info("Altering quantity_traded to BIGINT...")
            conn.execute(text("ALTER TABLE mto_delivery ALTER COLUMN quantity_traded TYPE BIGINT"))

            logger.info("Altering deliverable_qty to BIGINT...")
            conn.execute(text("ALTER TABLE mto_delivery ALTER COLUMN deliverable_qty TYPE BIGINT"))

            conn.commit()
            logger.info("Schema update successful.")

    except Exception as e:
        logger.error(f"Schema update failed: {e}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    fix_mto_schema()
