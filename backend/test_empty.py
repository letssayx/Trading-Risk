import sys
from backend.infrastructure.db import SessionLocal
from backend.ingest.nse_models import OiAnalysisMetrics

db = SessionLocal()
item = db.query(OiAnalysisMetrics).first()
if not item:
    print("NO METRICS AT ALL")
else:
    print("Has items:", item.symbol)
