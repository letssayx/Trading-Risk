import sys
import logging
from backend.infrastructure.db import SessionLocal
from backend.web.api.data.view_routes import get_model_for_type, process_results
import json

logging.basicConfig(level=logging.INFO)
db = SessionLocal()

model = get_model_for_type("dividend")
print("Model:", model)

try:
    results = db.query(model).limit(2).all()
    print("Found:", len(results))
    data = process_results(results, model)
    print("Processed:", json.dumps(data[:1], indent=2))
except Exception as e:
    import traceback
    traceback.print_exc()
