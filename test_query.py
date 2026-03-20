import sys
import logging
from backend.infrastructure.db import SessionLocal
from backend.web.api.data.view_routes import get_model_for_type, process_results

logging.basicConfig(level=logging.DEBUG)
db = SessionLocal()

model = get_model_for_type("dividend")
print("Model:", model)

try:
    results = db.query(model).filter(model.symbol == 'HDFCBANK').limit(10).all()
    print("Found:", len(results))
    print("Rows:", results)
except Exception as e:
    import traceback
    traceback.print_exc()
