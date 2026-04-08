import asyncio
from backend.infrastructure.db import SessionLocal
from sqlalchemy import text

db = SessionLocal()
# Check index data
result = db.execute(text("SELECT count(*) FROM historical_index_data WHERE index_name = 'NIFTY'")).fetchone()
print(f"Index data count: {result[0]}")

# Check FO data
result = db.execute(text("SELECT count(*) FROM bhavcopy_fo WHERE ticker_symb = 'NIFTY'")).fetchone()
print(f"FO data count: {result[0]}")
