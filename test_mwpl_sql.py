from backend.infrastructure.db import SessionLocal
from backend.ingest.nse_models import DailyDerivativesAnalysis
from sqlalchemy.orm import Session
import json

db = SessionLocal()
record = db.query(DailyDerivativesAnalysis.symbol, DailyDerivativesAnalysis.mwpl_array).filter(DailyDerivativesAnalysis.mwpl_array != None).first()
if record:
    print(record.symbol)
    print(record.mwpl_array)
    arr = record.mwpl_array
    if isinstance(arr, str):
        arr = json.loads(arr)
    print("Parsed arr:", arr)
else:
    print("No records with mwpl_array found.")
