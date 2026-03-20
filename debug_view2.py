import sys
import logging
from backend.infrastructure.db import SessionLocal
from backend.web.api.data.view_routes import get_model_for_type, process_results
import json

logging.basicConfig(level=logging.INFO)
model = get_model_for_type("dividend")
print("Model:", model)

try:
    cols = model.__table__.columns.keys()
    print("Columns:", cols)
except Exception as e:
    import traceback
    traceback.print_exc()
