import sys
sys.path.append('.')
from backend.infrastructure.db import SessionLocal
from backend.ingest.nse_models import BoardMeeting, CorporateAction
from sqlalchemy import text

def delete_duplicates(model_class, table_name):
    db = SessionLocal()
    try:
        print(f"Cleaning {table_name}...")
        # Keep the one with the highest ID for each date+symbol pair
        query = text(f"""
        DELETE FROM {table_name} a USING (
            SELECT MAX(id) as max_id, date, symbol
            FROM {table_name}
            GROUP BY date, symbol
            HAVING COUNT(*) > 1
        ) b
        WHERE a.date = b.date
          AND a.symbol = b.symbol
          AND a.id < b.max_id;
        """)

        result = db.execute(query)
        db.commit()
        print(f"Deleted {result.rowcount} duplicates from {table_name}.")
    except Exception as e:
        print(f"Error cleaning {table_name}: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    delete_duplicates(BoardMeeting, "board_meetings")
    delete_duplicates(CorporateAction, "corporate_actions")
