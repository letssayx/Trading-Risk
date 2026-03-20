import asyncio
from datetime import date
from backend.infrastructure.db import SessionLocal
from backend.ingest.nse_models import CorporateAction
from sqlalchemy.dialects.postgresql import insert as pg_insert
import string

db = SessionLocal()
table = CorporateAction.__table__

try:
    chunk = [
        {'date': date(2025,1,1), 'symbol': 'SURYAROSNI', 'purpose': 'Bonus 1:1', 'face_value': 5.0, 'dividend_type': 'Bonus'},
        {'date': date(2025,1,1), 'symbol': 'SURYAROSNI', 'purpose': 'Bonus 1:1', 'face_value': 5.0, 'dividend_type': 'Bonus'}
    ]
    unique_fields = ['date', 'symbol', 'purpose']

    # Emulate deduplication
    seen = {}
    for r in chunk:
         key = tuple(r.get(f) for f in unique_fields)
         seen[key] = r
    deduped = list(seen.values())

    print("Deduped:", len(deduped))
    stmt = pg_insert(table).values(deduped)
    update_cols = {c.name: c for c in stmt.excluded if c.name not in unique_fields and c.name not in ['id', 'created_at']}

    if update_cols:
        stmt = stmt.on_conflict_do_update(index_elements=unique_fields, set_=update_cols)
    else:
        stmt = stmt.on_conflict_do_nothing(index_elements=unique_fields)

    print("Executing query...")
    result = db.execute(stmt)
    print("Rowcount:", result.rowcount)

except Exception as e:
    print("Upsert Error:", e)
