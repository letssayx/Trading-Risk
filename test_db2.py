from backend.infrastructure.db import SessionLocal
from backend.ingest.nse_models import BhavcopyFO
from sqlalchemy import text

db = SessionLocal()

print("Checking FO table structure:")
print(f"Total BhavcopyFO count: {db.query(BhavcopyFO).count()}")

distinct_types = db.execute(text("SELECT DISTINCT instrument_type FROM bhavcopy_fo")).fetchall()
print(f"Distinct Instrument Types: {distinct_types}")

db.close()
