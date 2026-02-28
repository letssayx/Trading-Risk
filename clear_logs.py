from backend.infrastructure.db import SessionLocal
from sqlalchemy import text

def clear_logs():
    db = SessionLocal()
    try:
        # Delete ALL SUCCESS logs for mwpl_cli and pe_ratio to force a clean re-import
        result = db.execute(text("DELETE FROM import_logs WHERE table_name IN ('mwpl_cli', 'pe_ratio')"))
        print(f"Deleted {result.rowcount} import logs. Please try importing from the UI again.")

        # Also clean up any truncated/old Index P/E data from the pe_ratio table
        result2 = db.execute(text("DELETE FROM pe_ratio WHERE symbol ILIKE '%Index%' OR symbol ILIKE '%NIFTY%' OR symbol ILIKE '%Nifty%'"))
        print(f"Deleted {result2.rowcount} old Index PE rows.")

        db.commit()
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == '__main__':
    clear_logs()
