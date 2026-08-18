import asyncio
from backend.dependencies import get_db
from backend.ingest.nse_models import CorporateAction, BoardMeeting, DividendDatabank
from sqlalchemy import select
import json

def main():
    db_gen = get_db()
    db = next(db_gen)

    # Get CA
    cas = db.query(CorporateAction).filter(CorporateAction.symbol.in_(['RECLTD', 'COALINDIA'])).all()
    print("--- Corporate Actions ---")
    for ca in cas:
        if 'div' in (ca.purpose or '').lower() or ca.extracted_dividend_amount:
            print(f"{ca.symbol} | EX: {ca.ex_date} | REC: {ca.record_date} | BC: {ca.broadcast_date} | AMT: {ca.extracted_dividend_amount} | TYPE: {ca.extracted_dividend_type} | PURP: {ca.purpose}")

    # Get BM
    bms = db.query(BoardMeeting).filter(BoardMeeting.symbol.in_(['RECLTD', 'COALINDIA'])).all()
    print("\n--- Board Meetings ---")
    for bm in bms:
        if 'div' in (bm.purpose or '').lower() or bm.extracted_dividend_amount:
            print(f"{bm.symbol} | MEET: {bm.meeting_date} | BC: {bm.broadcast_date} | AMT: {bm.extracted_dividend_amount} | TYPE: {bm.extracted_dividend_type} | EX: {bm.extracted_record_date} | PURP: {bm.purpose}")

if __name__ == '__main__':
    main()
