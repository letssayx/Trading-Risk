from datetime import date
from backend.ingest.nse_lib import NSELib

lib = NSELib()
resp = lib.get("https://www.nseindia.com/api/corporate-board-meetings?index=equities")
if resp and resp.status_code == 200:
    data = resp.json()
    if data:
        for i in range(min(15, len(data))):
            print(f"Item {i}: bm_timestamp={data[i].get('bm_timestamp')} | date={data[i].get('bm_date')}")
else:
    print(f"Failed: {resp.status_code if resp else 'None'}")
