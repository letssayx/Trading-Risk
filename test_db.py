from backend.infrastructure.db import SessionLocal
from backend.ingest import nse_models as models

db = SessionLocal()
print(db.query(models.SecurityMaster).count())
