from sqlalchemy import text
import os
import sys

# Setup path and database connection
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.infrastructure.db import SessionLocal

db = SessionLocal()

try:
    print("Adding new columns to board_meetings table...")
    db.execute(text("ALTER TABLE board_meetings ADD COLUMN IF NOT EXISTS extracted_dividend_amount FLOAT;"))
    db.execute(text("ALTER TABLE board_meetings ADD COLUMN IF NOT EXISTS extracted_dividend_type VARCHAR(50);"))
    db.commit()
    print("Migration successful.")
except Exception as e:
    db.rollback()
    print(f"Error during migration: {e}")
finally:
    db.close()
