import os
import sys
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.web.api.data.volatility_routes import get_volatility_cone

DATABASE_URL = "postgresql://myuser:mypassword@localhost:5432/stock_data"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

try:
    res = get_volatility_cone("NIFTY", 500, False, db)
    import json
    print(json.dumps(res, indent=2))
except Exception as e:
    import traceback
    traceback.print_exc()
finally:
    db.close()
