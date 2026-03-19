from backend.infrastructure.db import SessionLocal
from backend.ingest.nse_models import Dividend, BoardMeeting

db = SessionLocal()
divs = db.query(Dividend).count()
bms = db.query(BoardMeeting).count()
print(f"Total Dividends: {divs}")
print(f"Total Board Meetings: {bms}")

pfc_divs = db.query(Dividend).filter(Dividend.symbol == 'PFC').all()
print(f"PFC Dividends: {len(pfc_divs)}")
for d in pfc_divs:
    print(d.symbol, d.ex_date, d.amount, d.purpose)
