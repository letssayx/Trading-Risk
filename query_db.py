from backend.infrastructure.db import SessionLocal
from backend.ingest.nse_models import CorporateAction, BoardMeeting
import pandas as pd

db = SessionLocal()

print("--- COALINDIA CA ---")
cas = db.query(CorporateAction).filter(CorporateAction.symbol == 'COALINDIA').order_by(CorporateAction.date.desc()).all()
for c in cas[:5]:
    print(f"Date: {c.date}, ExDate: {c.ex_date}, RecordDate: {c.record_date}, Type: {c.dividend_type}, Amount: {c.amount}, Purpose: {c.purpose}")

print("\n--- COALINDIA BM ---")
bms = db.query(BoardMeeting).filter(BoardMeeting.symbol == 'COALINDIA').order_by(BoardMeeting.date.desc()).all()
for b in bms[:5]:
    print(f"Date: {b.date}, MeetingDate: {b.meeting_date}, BroadcastDate: {b.broadcast_date}, Purpose: {b.purpose}")

print("\n--- PFC CA ---")
cas = db.query(CorporateAction).filter(CorporateAction.symbol == 'PFC').order_by(CorporateAction.date.desc()).all()
for c in cas[:5]:
    print(f"Date: {c.date}, ExDate: {c.ex_date}, RecordDate: {c.record_date}, Type: {c.dividend_type}, Amount: {c.amount}, Purpose: {c.purpose}")

print("\n--- PFC BM ---")
bms = db.query(BoardMeeting).filter(BoardMeeting.symbol == 'PFC').order_by(BoardMeeting.date.desc()).all()
for b in bms[:5]:
    print(f"Date: {b.date}, MeetingDate: {b.meeting_date}, BroadcastDate: {b.broadcast_date}, Purpose: {b.purpose}")
