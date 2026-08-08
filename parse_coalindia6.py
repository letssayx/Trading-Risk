import sys
sys.path.append('.')
from backend.infrastructure.db import SessionLocal
from backend.ingest.nse_models import CorporateAction, BoardMeeting

db = SessionLocal()

print("--- COALINDIA BM ---")
bms = db.query(BoardMeeting).filter(BoardMeeting.symbol == 'COALINDIA', BoardMeeting.date >= '2025-01-01').order_by(BoardMeeting.date.desc()).all()
for bm in bms:
    if '2026' in str(bm.meeting_date):
        print(f"ID: {bm.id}, Date: {bm.date}, Meet: {bm.meeting_date}, Type: {bm.extracted_dividend_type}, Amt: {bm.extracted_dividend_amount}, Purp: {bm.purpose}")

print("--- DLF BM ---")
bms = db.query(BoardMeeting).filter(BoardMeeting.symbol == 'DLF', BoardMeeting.date >= '2025-01-01').order_by(BoardMeeting.date.desc()).all()
for bm in bms:
    if '2026' in str(bm.meeting_date):
        print(f"ID: {bm.id}, Date: {bm.date}, Meet: {bm.meeting_date}, Type: {bm.extracted_dividend_type}, Amt: {bm.extracted_dividend_amount}, Purp: {bm.purpose}")
db.close()
