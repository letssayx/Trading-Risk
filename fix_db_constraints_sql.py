import sys
sys.path.append('.')
from backend.infrastructure.db import SessionLocal
from sqlalchemy import text

db = SessionLocal()
try:
    print("Updating constraints in Postgres...")
    db.execute(text("ALTER TABLE board_meetings DROP CONSTRAINT IF EXISTS uq_board_meeting_unique;"))
    db.execute(text("ALTER TABLE board_meetings ADD CONSTRAINT uq_board_meeting_unique UNIQUE (date, symbol);"))
    db.commit()
    print("board_meetings constraint updated.")
except Exception as e:
    print(f"Error on board_meetings: {e}")
    db.rollback()

try:
    db.execute(text("ALTER TABLE corporate_actions DROP CONSTRAINT IF EXISTS uq_corporate_action_unique;"))
    db.execute(text("ALTER TABLE corporate_actions ADD CONSTRAINT uq_corporate_action_unique UNIQUE (date, symbol);"))
    db.commit()
    print("corporate_actions constraint updated.")
except Exception as e:
    print(f"Error on corporate_actions: {e}")
    db.rollback()

db.close()
