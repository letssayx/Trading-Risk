import sys
import logging
from backend.infrastructure.db import SessionLocal
from backend.ingest.nse_models import BhavcopyFO

logging.basicConfig(level=logging.INFO)
db = SessionLocal()

try:
    # Test the query
    valid_symbols = set([r[0] for r in db.query(BhavcopyFO.ticker_symb).distinct().limit(10).all()])
    print("Success. Extracted symbols:", valid_symbols)
except Exception as e:
    print("Error:", e)
