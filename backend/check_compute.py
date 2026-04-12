from backend.infrastructure.db import SessionLocal
from backend.web.api.data.derivatives_routes import compute_aggregated_oi_analysis
from backend.ingest.nse_models import OiAnalysisMetrics

db = SessionLocal()
res = compute_aggregated_oi_analysis(db)
print("RES:", res)
items = db.query(OiAnalysisMetrics).limit(5).all()
for item in items:
    print(item.symbol, item.trade_date, item.price, item.fut_oi, item.call_oi, item.put_oi, item.oi_chg_pct)
