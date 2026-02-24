import requests
from datetime import datetime

BASE_URL = "https://nsearchives.nseindia.com"
HEADERS = {'User-Agent': 'Mozilla/5.0'}
TEST_DATE = datetime(2026, 2, 20)

FORMATS = [
    "%d%m%Y", # 20022026
    "%d%b%Y", # 20Feb2026
    "%d-%m-%Y", # 20-02-2026
    "%d-%b-%Y", # 20-Feb-2026
]

for fmt in FORMATS:
    d = TEST_DATE.strftime(fmt)
    url = f"{BASE_URL}/archives/equities/mto/bulk_deals_{d}.csv"
    try:
        resp = requests.head(url, headers=HEADERS, timeout=2)
        if resp.status_code == 200:
            print(f"FOUND: {url}")
    except: pass
