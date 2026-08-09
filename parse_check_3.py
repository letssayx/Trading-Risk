from datetime import date, timedelta
from backend.ingest.nse_lib import NSELib
import json
import logging

logging.basicConfig(level=logging.DEBUG)

nselib = NSELib()
trade_date = date(2026, 7, 24)
from_date_str = (trade_date - timedelta(days=60)).strftime("%d-%m-%Y")
to_date_str = (trade_date + timedelta(days=180)).strftime("%d-%m-%Y")

url = f"https://www.nseindia.com/api/corporates-corporateActions?index=equities&from_date={from_date_str}&to_date={to_date_str}"
resp = nselib.get(url)
if resp:
    data = resp.json()
    for item in data:
        if item.get('symbol') in ('COALINDIA', 'RECLTD'):
            print("CA: ", item)
