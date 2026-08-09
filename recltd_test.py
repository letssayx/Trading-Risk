import json
import logging
from datetime import date
from backend.ingest.nse_lib import NSELib

logging.basicConfig(level=logging.DEBUG)
nselib = NSELib()

url = "https://www.nseindia.com/api/corporates-corporateActions?index=equities&symbol=RECLTD"
resp = nselib.get(url)
if resp:
    data = resp.json()
    for item in data[:5]:
        print("CA: ", item)
