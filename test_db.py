import sys
sys.path.append("/app")
from backend.infrastructure.db import get_db, SessionLocal
from sqlalchemy import text

db = next(get_db())

try:
    idx_query = text("""
        SELECT trade_date, open_price, high_price, low_price, close_price
        FROM historical_index_data
        WHERE index_name = 'NIFTY'
        ORDER BY trade_date DESC
        LIMIT 10
    """)
    result = db.execute(idx_query).fetchall()
    print(f"historical_index_data rows: {len(result)}")
    print(f"Row length: {len(result[0]) if result else 0}")
except Exception as e:
    print("Error:", e)
