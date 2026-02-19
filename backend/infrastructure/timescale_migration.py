from sqlalchemy.orm import Session
from sqlalchemy import text
import logging

logger = logging.getLogger(__name__)

def enable_timescaledb(db: Session):
    """
    Attempts to enable TimescaleDB extension and convert 'bhavcopy' to a hypertable.
    """
    try:
        print(">>> Attempting to enable TimescaleDB extension...")
        # 1. Enable Extension
        db.execute(text("CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;"))
        db.commit()
        print(">>> TimescaleDB extension enabled.")

        # 2. Convert Bhavcopy to Hypertable
        # migrate_data=True allows converting a table that already has data
        # chunk_time_interval='1 month' is good for daily data

        # Check if already hypertable to avoid errors?
        # if_not_exists=TRUE handles create, but 'migrate_data' might be needed only if not exists.
        # The standard command: SELECT create_hypertable('bhavcopy', 'trade_date', ...);

        print(">>> Converting 'bhavcopy' to hypertable...")
        # We catch specific error if it's already a hypertable
        try:
            db.execute(text("""
                SELECT create_hypertable(
                    'bhavcopy',
                    'trade_date',
                    chunk_time_interval => INTERVAL '1 month',
                    if_not_exists => TRUE,
                    migrate_data => TRUE
                );
            """))
            db.commit()
            print(">>> 'bhavcopy' is now a TimescaleDB hypertable.")
        except Exception as e:
            # Postgres error code for "table is already a hypertable" usually handled by if_not_exists,
            # but sometimes migrate_data causes issues if already migrated.
            if "already a hypertable" in str(e):
                print(">>> 'bhavcopy' is already a hypertable.")
                db.rollback()
            else:
                raise e

    except Exception as e:
        print(f"!!! TimescaleDB Setup Failed: {e}")
        print("!!! Ensure TimescaleDB is installed on the PostgreSQL server.")
        # We do not crash the app, just log.
        db.rollback()
