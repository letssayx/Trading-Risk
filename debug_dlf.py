from backend.infrastructure.db import SessionLocal
from backend.ingest.nse_models import CorporateAction, BoardMeeting

db = SessionLocal()

print("--- DLF Corporate Actions ---")
cas = db.query(CorporateAction).filter(CorporateAction.symbol == 'DLF').order_by(CorporateAction.date.desc()).all()
for ca in cas:
    print(f"ID: {ca.id}, Date: {ca.date}, Ex-Date: {ca.ex_date}, Amount: {ca.parsed_dividend_amount}, Type: {ca.dividend_type}, Purpose: {ca.purpose}")

print("\n--- DLF Board Meetings ---")
bms = db.query(BoardMeeting).filter(BoardMeeting.symbol == 'DLF').order_by(BoardMeeting.date.desc()).all()
for bm in bms:
    print(f"ID: {bm.id}, Date: {bm.date}, Amount: {bm.extracted_dividend_amount}, Purpose: {bm.purpose}")
