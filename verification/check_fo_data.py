from sqlalchemy import create_engine, select, func
from sqlalchemy.orm import sessionmaker
from backend.ingest import nse_models as models
from backend.infrastructure.db import SessionLocal
import pandas as pd
from datetime import date, timedelta

def check_fo_data():
    db = SessionLocal()
    try:
        # Check BhavcopyFO count
        count = db.query(models.BhavcopyFO).count()
        print(f"Total FO Records: {count}")

        if count == 0:
            print("No FO data found.")
            return

        # Check latest date
        latest_date = db.query(func.max(models.BhavcopyFO.trade_date)).scalar()
        print(f"Latest FO Date: {latest_date}")

        # Check records for latest date
        records = db.query(models.BhavcopyFO).filter(models.BhavcopyFO.trade_date == latest_date).limit(5).all()
        print("\nSample Records (Latest Date):")
        for r in records:
            print(f"Symbol: {r.ticker_symb}, Type: {r.instrument_type}, Name: {r.instrument_name}, Expiry: {r.expiry_date}")

        # Check specifically for NULL instrument_type
        null_type_count = db.query(models.BhavcopyFO).filter(models.BhavcopyFO.instrument_type == None).count()
        print(f"\nRecords with NULL instrument_type: {null_type_count}")

        # Check unique instrument types
        distinct_types = db.query(models.BhavcopyFO.instrument_type).distinct().all()
        print(f"Distinct Instrument Types: {[t[0] for t in distinct_types]}")

    finally:
        db.close()

if __name__ == "__main__":
    check_fo_data()
