from backend.infrastructure.db import SessionLocal
from backend.ingest import nse_models as models
from backend.models.audit import SymbolMaster

db = SessionLocal()
sym = models.SecurityMaster(
    symbol="RELIANCE",
    company_name="Reliance Industries",
    instrument_type="EQ",
    fin_instrm_id=123,
    status="Active",
    listing_date="2020-01-01"
)
db.add(sym)
db.commit()
print("Added RELIANCE to SecurityMaster")
