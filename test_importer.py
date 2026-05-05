import sys
import os
sys.path.append('/app/backend')
from datetime import date
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from ingest.nse_importer import NSEImporter
from ingest.nse_models import Base, BoardMeeting, CorporateAction
from core.database import get_db

importer = NSEImporter()
# We will import for March 24, 2026 as per our findings (HDFCAMC intimation)
print("Importing board meetings...")
res = importer.import_date(date(2026, 3, 24), patterns=['board_meetings'], force=True)
print(res)

with next(get_db()) as db:
    cas = db.query(CorporateAction).filter(CorporateAction.symbol == 'HDFCAMC').all()
    for ca in cas:
        print(f"CA: {ca.date} {ca.symbol} {ca.purpose} {ca.parsed_dividend_amount} {ca.dividend_type}")
