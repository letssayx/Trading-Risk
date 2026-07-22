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

    if len(sys.argv) == 3:
        try:
            start_date = datetime.datetime.strptime(sys.argv[1], "%Y-%m-%d").date()
            end_date = datetime.datetime.strptime(sys.argv[2], "%Y-%m-%d").date()
        except Exception as e:
            print(f"Error parsing dates, expected format YYYY-MM-DD: {e}")
            sys.exit(1)
    else:
        end_date = datetime.date.today()
        start_date = end_date - datetime.timedelta(days=365)

    print(f"Starting historical Financials import from {end_date} back to {start_date}...")

    curr_end = end_date

    total_records = 0
    while curr_end > start_date:
        curr_start = curr_end - datetime.timedelta(days=90)
        if curr_start < start_date:
            curr_start = start_date

        print(f"Fetching Financial Results for range {curr_start} to {curr_end}...")

        url = f"{lib.BASE_URL}/api/corporates-financial-results?index=equities&period=Quarterly&from_date={curr_start.strftime('%d-%m-%Y')}&to_date={curr_end.strftime('%d-%m-%Y')}"

        try:
            resp = lib.get(url, use_curl=True)
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
                        att = item.get('attachment') or item.get('attchmntFile')

                        bdate_str = item.get('bm_timestamp') or item.get('seqDate') or item.get('an_dt')

                        bdate = None
                        if bdate_str:
                            try:
                                import re
                                bdate_clean = re.sub(r'\.\d+', '', str(bdate_str)).strip()
                                bdate = datetime.datetime.strptime(bdate_clean, "%d-%b-%Y %H:%M:%S").date()
                            except:
                                try:
                                    bdate = datetime.datetime.strptime(str(bdate_clean).split(' ')[0], "%d-%b-%Y").date()
                                except:
                                    pass
                        if not bdate:
                            bdate = curr_end

                        period = item.get('period', 'N/A')
                        reBasEPS = item.get('reBasEPS')
                        reDilEPS = item.get('reDilEPS')
                        netProfit = item.get('reProLossAftTaxAftExtrdItemAttDrtAndMnrit') or item.get('reProLossBefTax') or item.get('reNetPrftLoss')

                        try:
                            reBasEPS = float(reBasEPS) if reBasEPS else None
                            reDilEPS = float(reDilEPS) if reDilEPS else None
                            netProfit = float(netProfit) if netProfit else None
                        except:
                            pass

                        if symbol:
                            existing = db.query(FinancialResult).filter_by(
                                symbol=symbol,
                                date=bdate
                            ).first()

                            if not existing:
                                fr = FinancialResult(
                                    symbol=symbol,
                                    date=bdate,
                                    period=period,
                                    basic_eps=reBasEPS,
                                    diluted_eps=reDilEPS,
                                    net_profit=netProfit,
                                    attachment_url=att
                                )
                                db.add(fr)
                                total_records += 1
                            else:
                                if existing.basic_eps is None and reBasEPS is not None:
                                    existing.basic_eps = reBasEPS
                                if existing.net_profit is None and netProfit is not None:
                                    existing.net_profit = netProfit

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
