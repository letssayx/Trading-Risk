import requests
import io
import pandas as pd
from datetime import datetime

BASE_URL = "https://nsearchives.nseindia.com"
HEADERS = {'User-Agent': 'Mozilla/5.0'}
TEST_DATE = datetime(2026, 2, 20)
DT_DMY = TEST_DATE.strftime("%d%m%Y")

def probe_path(path):
    url = f"{BASE_URL}/{path}"
    try:
        resp = requests.head(url, headers=HEADERS, timeout=2)
        if resp.status_code == 200 and 'html' not in resp.headers.get('Content-Type', ''):
            return url
    except:
        pass
    return None

def find_deals():
    # Attempt to find bulk deals
    prefixes = [
        "archives/equities/mto", "content/equities", "products/content",
        "archives/equities", "content/mto"
    ]
    filenames = [f"bulk_deals_{DT_DMY}.csv", f"bulk_deals.csv"]

    for p in prefixes:
        for f in filenames:
            path = f"{p}/{f}"
            found = probe_path(path)
            if found:
                print(f"FOUND BULK: {found}")
                return

find_deals()
