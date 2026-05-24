from datetime import date
from backend.ingest.nse_lib import NSELib

lib = NSELib()
resp = lib.get("https://www.nseindia.com/api/corporates-corporateActions?index=equities")
if resp and resp.status_code == 200:
    data = resp.json()
    if data:
        for i in range(min(15, len(data))):
            print(f"Item {i}: symbol={data[i].get('symbol')} | update_date={data[i].get('update_date')} | nd_start_date={data[i].get('nd_start_date')} | date={data[i].get('ex_date')} | caBroadcastDate={data[i].get('caBroadcastDate')}")
else:
    print(f"Failed: {resp.status_code if resp else 'None'}")
