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

    # We will fetch roughly 5 years of historical financial results
    # NSE provides this by searching date ranges.
    # To avoid timeouts, we do it in 6 month chunks from today (19-07-2026) back to 2020.
    end_date = datetime.date(2026, 7, 19)
    start_date = datetime.date(2020, 1, 1)

    print(f"Starting historical Financials import from {end_date} back to {start_date}...")

    curr_end = end_date

    total_records = 0
    while curr_end > start_date:
        curr_start = curr_end - datetime.timedelta(days=180)
        if curr_start < start_date:
            curr_start = start_date

        print(f"Fetching Financial Results for range {curr_start} to {curr_end}...")

        url = f"{lib.BASE_URL}/api/corporate-financial-results?index=equities&from_date={curr_start.strftime('%d-%m-%Y')}&to_date={curr_end.strftime('%d-%m-%Y')}"

        try:
            resp = lib.get(url)
            if resp and resp.status_code == 200:
                data = resp.json()
                if data:
                    records = []
                    for item in data:
                        reDilEPS = item.get('reDilEPS')
                        reBasEPS = item.get('reBasEPS')
                        netProfit = item.get('reProLossAftTaxAftExtrdItemAttDrtAndMnrit') or item.get('reProLossBefTax') or item.get('reNetPrftLoss')

                        symbol = item.get('symbol')
                        period = item.get('period')
                        bdate_str = item.get('bm_timestamp', item.get('seqDate'))
                        pend_str = item.get('period_end_date', item.get('toDate'))
                        att = item.get('attachment')

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

                        pend = None
                        if pend_str:
                            try:
                                pend = datetime.datetime.strptime(str(pend_str).split(' ')[0], "%d-%b-%Y").date()
                            except:
                                pass

                        if not bdate:
                            bdate = curr_end # Fallback

                        def safe_float(v):
                            try: return float(v)
                            except: return None

                        if symbol:
                            existing = db.query(FinancialResult).filter_by(
                                symbol=symbol,
                                period=period,
                                date=bdate
                            ).first()

                            if not existing:
                                fr = FinancialResult(
                                    symbol=symbol,
                                    date=bdate,
                                    period=period,
                                    period_end_date=pend,
                                    basic_eps=safe_float(reBasEPS),
                                    diluted_eps=safe_float(reDilEPS),
                                    net_profit=safe_float(netProfit),
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
