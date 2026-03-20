import asyncio
from datetime import date
from backend.ingest.nse_importer import NSEDataImporter
from backend.infrastructure.db import SessionLocal

db = SessionLocal()
importer = NSEDataImporter()
try:
    print("Testing CA import...")
    results = {}
    completed = []
    # Test a date that failed earlier
    importer._process_file(db, 'corporate_actions', date(2025, 7, 26), results, completed, force=True)
    print("CA Results:", results)

except Exception as e:
    import traceback
    traceback.print_exc()
