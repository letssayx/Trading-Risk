import asyncio
from backend.infrastructure.db import SessionLocal
from backend.web.api.data.view_routes import get_model_for_type
from sqlalchemy import text

db = SessionLocal()

try:
    print("Trying to execute query with missing DB...")
    # Just checking syntax of execute_export_query indirectly
    import backend.web.api.data.view_routes as vr
    print("Methods:", dir(vr))
except Exception as e:
    print("Error:", e)
