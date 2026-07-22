import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.ingest.nse_lib import NSELib
from backend.ingest.nse_models import CorporateAction, BoardMeeting
from dotenv import load_dotenv

load_dotenv()
db_url = os.environ.get("DATABASE_URL", "postgresql://jules:jules@localhost:5432/finance")
engine = create_engine(db_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def fetch_historical_agm():
    db = SessionLocal()
    lib = NSELib()

    end_date = datetime.date(2026, 7, 19)
    start_date = datetime.date(2020, 1, 1)

    print(f"Starting historical AGM import from {end_date} back to {start_date}...")

    curr_end = end_date
    total_records = 0

    while curr_end > start_date:
        curr_start = curr_end - datetime.timedelta(days=90)
        if curr_start < start_date:
            curr_start = start_date

        print(f"Fetching AGM Announcements for range {curr_start} to {curr_end}...")

        # We search specifically for 'Shareholders meeting' subject since we know that's how NSE classifies them
        url = f"{lib.BASE_URL}/api/corporate-announcements?index=equities&subject=Shareholders%20meeting&from_date={curr_start.strftime('%d-%m-%Y')}&to_date={curr_end.strftime('%d-%m-%Y')}"

        try:
            resp = lib.get(url)
            if resp and resp.status_code == 200:
                data = resp.json()
                if data:
                    for item in data:
                        symbol = item.get('symbol')
                        purpose = item.get('desc') or item.get('subject')
                        ann_dt_str = item.get('an_dt') # e.g. 13-May-2026 17:01:36

                        if symbol and ann_dt_str:
                            try:
                                import re
                                ann_dt_clean = re.sub(r'\.\d+', '', str(ann_dt_str)).strip()
                                ann_date = datetime.datetime.strptime(ann_dt_clean, "%d-%b-%Y %H:%M:%S").date()
                            except:
                                try:
                                    ann_date = datetime.datetime.strptime(str(ann_dt_str).split(' ')[0], "%d-%b-%Y").date()
                                except:
                                    ann_date = None

                            # Extract actual AGM date from purpose
                            import re
                            agm_date = None
                            # Match dates like "09-Aug-2023", "09-August-2023", "9 August, 2023"
                            date_matches = re.findall(r'(\d{1,2})[-/ ]([A-Za-z]+|\d{1,2})[-/ ,]+(\d{2,4})', str(purpose))
                            if date_matches:
                                try:
                                    # take the first matching date as the AGM date
                                    d, m, y = date_matches[0]
                                    if len(y) == 2:
                                        y = "20" + y
                                    if m.isdigit():
                                        agm_date = datetime.datetime.strptime(f"{d}-{m}-{y}", "%d-%m-%Y").date()
                                    else:
                                        m = m[:3] # Jan, Feb
                                        agm_date = datetime.datetime.strptime(f"{d}-{m}-{y}", "%d-%b-%Y").date()
                                except:
                                    pass

                            if ann_date:
                                # We store AGMs as Corporate Actions (or Board Meetings) with 'AGM' type/purpose
                                # Since they don't have amounts, just the date and purpose matters.
                                # Check if it exists
                                existing = db.query(BoardMeeting).filter_by(
                                    symbol=symbol,
                                    date=ann_date,
                                    purpose=purpose
                                ).first()

                                if not existing:
                                    bm = BoardMeeting(
                                        symbol=symbol,
                                        date=ann_date,
                                        broadcast_date=ann_date,
                                        purpose=purpose,
                                        company_name=item.get('compName')
                                    )
                                    db.add(bm)
                                    total_records += 1

                    db.commit()
                    print(f"Added {total_records} records so far.")
        except Exception as e:
            print(f"Error fetching range {curr_start} to {curr_end}: {e}")

        curr_end = curr_start - datetime.timedelta(days=1)
        import time
        time.sleep(1)

    print(f"Finished! Total records inserted: {total_records}")
    db.close()

if __name__ == "__main__":
    fetch_historical_agm()
