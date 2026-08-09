import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.ingest.nse_lib import NSELib
from backend.ingest.nse_models import FinancialResult
from dotenv import load_dotenv

load_dotenv()
db_url = os.environ.get("DATABASE_URL", "postgresql://jules:jules@localhost:5432/finance")
engine = create_engine(db_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def fetch_historical_financials():
    db = SessionLocal()
    lib = NSELib()

    end_date = datetime.date(2026, 7, 19)
    start_date = datetime.date(2020, 1, 1)

    print(f"Starting historical Financials import from {end_date} back to {start_date}...")

    curr_end = end_date

    total_records = 0
    while curr_end > start_date:
        curr_start = curr_end - datetime.timedelta(days=90)
        if curr_start < start_date:
            curr_start = start_date

        print(f"Fetching Financial Results for range {curr_start} to {curr_end}...")

        url = f"{lib.BASE_URL}/api/corporate-announcements?index=equities&subject=Financial%20Results&from_date={curr_start.strftime('%d-%m-%Y')}&to_date={curr_end.strftime('%d-%m-%Y')}"

        try:
            resp = lib.get(url)
            print(f"Response status: {resp.status_code if resp else 'None'}")
            if resp and resp.status_code == 200:
                data = resp.json()
                if data:
                    records = []
                    if isinstance(data, list):
                        items = data
                    elif isinstance(data, dict) and 'data' in data:
                        items = data['data']
                    else:
                        items = []

                    for item in items:
                        symbol = item.get('symbol')
                        att = item.get('attchmntFile')

                        bdate_str = item.get('an_dt')

                        bdate = None
                        if bdate_str:
                            try:
                                import re
                                bdate_clean = re.sub(r'\.\d+', '', str(bdate_str)).strip()
                                bdate = datetime.datetime.strptime(bdate_clean, "%d-%b-%Y %H:%M:%S").date()
                            except:
                                try:
                                    bdate = datetime.datetime.strptime(bdate_clean.split(' ')[0], "%d-%b-%Y").date()
                                except:
                                    pass

                        if not bdate:
                            bdate = curr_end # Fallback

                        if symbol:
                            existing = db.query(FinancialResult).filter_by(
                                symbol=symbol,
                                date=bdate
                            ).first()

                            if not existing:
                                fr = FinancialResult(
                                    symbol=symbol,
                                    date=bdate,
                                    period="N/A", # Will be patched by yfinance
                                    attachment_url=att
                                )
                                db.add(fr)
                                total_records += 1

                    db.commit()
                    print(f"Added {total_records} records so far.")
        except Exception as e:
            print(f"Error fetching range {curr_start} to {curr_end}: {e}")

        curr_end = curr_start - datetime.timedelta(days=1)
        import time
        time.sleep(1) # Be nice to NSE

    print(f"Finished! Total records inserted: {total_records}")
    db.close()

if __name__ == "__main__":
    fetch_historical_financials()
