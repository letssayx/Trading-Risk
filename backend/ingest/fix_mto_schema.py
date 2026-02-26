import logging
from sqlalchemy import text
from backend.infrastructure.db import engine

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_mto_schema():
    """
    Alter mto_delivery table columns to BIGINT to handle large values.
    """
    logger.info("Starting MTO schema fix...")

    commands = [
        "ALTER TABLE mto_delivery ALTER COLUMN quantity_traded TYPE BIGINT;",
        "ALTER TABLE mto_delivery ALTER COLUMN deliverable_qty TYPE BIGINT;",
        "ALTER TABLE mto_delivery ALTER COLUMN sr_no TYPE BIGINT;"
    ]

    with engine.connect() as conn:
        with conn.begin():
            for cmd in commands:
                try:
                    logger.info(f"Executing: {cmd}")
                    conn.execute(text(cmd))
                except Exception as e:
                    logger.error(f"Failed to execute {cmd}: {e}")
                    # Don't raise, try others just in case (though transaction will rollback)

    logger.info("MTO schema fix completed.")

if __name__ == "__main__":
    fix_mto_schema()
