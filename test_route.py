from datetime import datetime
from backend.ingest.nse_models import BoardMeeting
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import pandas as pd

engine = create_engine('postgresql://postgres:postgres@localhost:5432/postgres')
Session = sessionmaker(bind=engine)
db = Session()

res = db.query(BoardMeeting).limit(1).first()

if res:
    print(res.broadcast_date, type(res.broadcast_date))
    val = res.broadcast_date
    if isinstance(val, pd.Timestamp):
        val = val.isoformat()
    elif isinstance(val, datetime):
        val = val.isoformat()
    elif hasattr(val, 'isoformat'): # date
        val = val.isoformat()
    print("Serialized:", val)
