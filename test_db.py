from datetime import date
from backend.infrastructure.db import SessionLocal
from backend.ingest import nse_models as models
from sqlalchemy import or_

db = SessionLocal()

print("Testing BHEL BMs...")
bhel_bms = db.query(models.BoardMeeting).filter(models.BoardMeeting.symbol == 'BHEL').all()
for bm in bhel_bms:
    print(f"BHEL BM: {bm.purpose} | Date: {bm.meeting_date} | Extracted: {bm.extracted_dividend_amount}")

print("\nTesting BHEL Corporate Announcements...")
bhel_anns = db.query(models.CorporateAnnouncement).filter(
    models.CorporateAnnouncement.symbol == 'BHEL',
    or_(models.CorporateAnnouncement.subject.ilike('%div%'), models.CorporateAnnouncement.subject.ilike('%record%'))
).all()
for ann in bhel_anns:
    print(f"BHEL ANN: {ann.subject} | {ann.broadcast_date}")
