from backend.infrastructure.db import SessionLocal
from backend.web.api.data.derivatives_routes import compute_aggregated_oi_analysis, get_aggregated_oi_analysis
import json

db = SessionLocal()
print("Computing...")
res = compute_aggregated_oi_analysis(db)
print(res)

print("Getting...")
res2 = get_aggregated_oi_analysis(db)
print(f"Got {len(res2.get('data', []))} records.")
