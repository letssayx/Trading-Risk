# Create tables so we don't get 500
from backend.infrastructure.db import engine, Base
from backend.ingest import nse_models
import datetime

Base.metadata.create_all(bind=engine)

# Insert dummy data for mwpl so we have something to see
from backend.infrastructure.db import SessionLocal

db = SessionLocal()
db.add(nse_models.MWPLClientPosition(
    date=datetime.date.today(),
    underlying_stock='RELIANCE',
    client_position_num=1,
    position_pct=15.5
))
db.add(nse_models.MWPLClientPosition(
    date=datetime.date.today(),
    underlying_stock='RELIANCE',
    client_position_num=2,
    position_pct=8.1
))
db.commit()
db.close()
