import requests

url = "https://www.nseindia.com/api/corporate-announcements?index=equities&symbol=HDFCAMC"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'application/json',
    'Accept-Language': 'en-US,en;q=0.9',
}
session = requests.Session()
session.get('https://www.nseindia.com', headers=headers, timeout=10)
response = session.get(url, headers=headers, timeout=10)
if response.status_code == 200:
    data = response.json()
    for item in data:
         if item.get("an_dt", "").startswith("16-Apr-2026"):
             if item.get("hasXbrl") and item.get("desc") == "Outcome of Board Meeting":
                 # Maybe the xbrl is just attached to the general endpoint?
                 # nsearchives.nseindia.com/corporate/xbrl/ ... let's see how BM xbrl was named.
                 # PIBM_541729_2432026181717_PRIOR_INTIMATION_WebXMLFile_20260324_181720352.xml
                 print(item)
