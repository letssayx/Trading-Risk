
import sys
import os
import datetime
import re

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.ingest.nse_lib import NSELib
from backend.ingest.nse_models import CorporateAction, BoardMeeting
from dotenv import load_dotenv

load_dotenv()
db_url = os.environ.get("DATABASE_URL", "postgresql://jules:jules@localhost:5432/finance")
engine = create_engine(db_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def fetch_historical_agm_range(start_date, end_date):
    db = SessionLocal()
    lib = NSELib()
    print(f'Starting historical AGM import from {end_date} back to {start_date}...')
    curr_end = end_date
    total_records = 0
    while curr_end >= start_date:
        curr_start = curr_end - datetime.timedelta(days=90)
        if curr_start < start_date:
            curr_start = start_date
        print(f'Fetching AGM Announcements for range {curr_start} to {curr_end}...')
        url = f"{lib.BASE_URL}/api/corporate-announcements?index=equities&from_date={curr_start.strftime('%d-%m-%Y')}&to_date={curr_end.strftime('%d-%m-%Y')}"
        try:
            resp = lib.get(url)
            if resp and resp.status_code == 200:
                data = resp.json()
                if data:
                    for item in data:
                        symbol = item.get('symbol')
                        subject = (item.get('subject') or '').lower()
                        desc = (item.get('desc') or '').lower()
                        purpose = item.get('desc') or item.get('subject')
                        ann_dt_str = item.get('an_dt') # e.g. 13-May-2026 17:01:36
                        is_agm = 'annual general meeting' in subject or 'agm' in subject or 'shareholders meeting' in subject or 'annual general meeting' in desc or 'agm' in desc or 'shareholders meeting' in desc
                        if symbol and ann_dt_str and is_agm:
                            try:
                                ann_dt_clean = re.sub(r'\.\d+', '', str(ann_dt_str)).strip()
                                ann_date = datetime.datetime.strptime(ann_dt_clean, "%d-%b-%Y %H:%M:%S").date()
                            except:
                                try:
                                    ann_date = datetime.datetime.strptime(str(ann_dt_str).split(' ')[0], "%d-%b-%Y").date()
                                except:
                                    ann_date = None

                            agm_date = None
                            date_matches = re.findall(r'(\d{1,2})[-/ ]([A-Za-z]+|\d{1,2})[-/ ,]+(\d{2,4})', str(purpose))
                            if date_matches:
                                try:
                                    d, m, y = date_matches[0]
                                    from dateutil.parser import parse
                                    agm_date = parse(f"{d} {m} {y}").date()
                                except:
                                    pass

                            if ann_date:
                                existing = db.query(CorporateAction).filter_by(symbol=symbol, date=ann_date, dividend_type='AGM').first()
                                if not existing:
                                    ca = CorporateAction(
                                        symbol=symbol,
                                        date=ann_date,
                                        purpose=purpose,
                                        dividend_type='AGM',
                                        ex_date=None,
                                        record_date=None,
                                        face_value=None,
                                        parsed_dividend_amount=None,
                                        parsed_dividend_type='AGM',
                                        broadcast_date=ann_date,
                                        agm_date=agm_date
                                    )
                                    db.add(ca)
                                    total_records += 1
                db.commit()
        except Exception as e:
            print(f'Error fetching AGM range: {e}')
        curr_end = curr_start - datetime.timedelta(days=1)
    print(f'Historical AGM fetch complete. Inserted {total_records} standalone AGM records.')
    return total_records

def fetch_historical_agm():
    if len(sys.argv) == 3:
        try:
            start_date = datetime.datetime.strptime(sys.argv[1], "%Y-%m-%d").date()
            end_date = datetime.datetime.strptime(sys.argv[2], "%Y-%m-%d").date()
        except Exception as e:
            print(f"Error parsing dates, expected format YYYY-MM-DD: {e}")
            sys.exit(1)
    else:
        end_date = datetime.date.today()
        start_date = end_date - datetime.timedelta(days=365) # Default to 1 year back
    fetch_historical_agm_range(start_date, end_date)

if __name__ == "__main__":
    fetch_historical_agm()
