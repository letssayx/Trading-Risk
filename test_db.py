from backend.infrastructure.db import SessionLocal
from backend.ingest.nse_models import BhavcopyFO
import sys

def test_futures():
    db = SessionLocal()
    # Try fetching WIPRO FUT
    latest_fo_date_record = db.query(BhavcopyFO).filter(
        BhavcopyFO.ticker_symb == 'WIPRO',
        BhavcopyFO.instrument_type.in_(['FUTSTK', 'FUTIDX'])
    ).order_by(BhavcopyFO.trade_date.desc()).first()

    if latest_fo_date_record:
        latest_fo_date = latest_fo_date_record.trade_date
        futures = db.query(BhavcopyFO).filter(
            BhavcopyFO.ticker_symb == 'WIPRO',
            BhavcopyFO.trade_date == latest_fo_date,
            BhavcopyFO.instrument_type.in_(['FUTSTK', 'FUTIDX'])
        ).order_by(BhavcopyFO.expiry_date.asc()).limit(3).all()

        for f in futures:
            print(f.trade_date, f.instrument_type, f.expiry_date, f.close_price)
    else:
        print("No records found.")

test_futures()
