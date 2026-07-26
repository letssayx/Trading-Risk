from backend.ingest.nse_lib import NSELib
import json
import pandas as pd

nselib = NSELib()
url = "https://www.nseindia.com/api/corporate-announcements?index=equities&symbol=COALINDIA"
resp = nselib.get(url)
print("Announcements for COALINDIA:")
if resp and resp.status_code == 200:
    data = resp.json()
    for d in data[:5]:
        print(d)
