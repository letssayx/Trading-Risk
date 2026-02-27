from backend.infrastructure.db import SessionLocal
from backend.ingest.queries import get_import_stats
from datetime import date
import json

db = SessionLocal()
try:
    stats = get_import_stats(db)
    print(json.dumps(stats, default=str))
except Exception as e:
    print(f"Error: {e}")
finally:
    db.close()
