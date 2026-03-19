import sys
import logging
from datetime import date
from backend.ingest.nse_importer import NSEDataImporter
from backend.infrastructure.db import SessionLocal
from backend.ingest.nse_models import CorporateAction, BoardMeeting, ImportLog

logging.basicConfig(level=logging.INFO)
db = SessionLocal()
divs = db.query(CorporateAction).count()
print(f"Total Corporate Actions in DB: {divs}")

pfc_divs = db.query(CorporateAction).filter(CorporateAction.symbol == 'PFC').all()
print(f"PFC Corporate Actions in DB: {len(pfc_divs)}")

# Look at ImportLogs for corporate_actions
logs = db.query(ImportLog).filter(ImportLog.table_name == 'corporate_actions').order_by(ImportLog.import_date.desc()).limit(15).all()
for l in logs:
    print(f"Log {l.import_date}: status={l.status}, rows_inserted={l.rows_inserted}, msg={l.error_message}")
