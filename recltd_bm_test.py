import json
import logging
from datetime import date
from backend.ingest.nse_lib import NSELib
import pandas as pd

logging.basicConfig(level=logging.DEBUG)
nselib = NSELib()

url = "https://www.nseindia.com/api/corporate-announcements?index=equities&symbol=RECLTD"
resp = nselib.get(url)
if resp:
    data = resp.json()
    for item in data[:10]:
        print("ANN: ", item.get('an_dt'), item.get('desc'), item.get('attchmntText'))
