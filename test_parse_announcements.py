import re
import requests
import pandas as pd
from backend.ingest.nse_lib import NSELib
import json

nselib = NSELib()

def fetch_announcements(symbol):
    url = f"https://www.nseindia.com/api/corporate-announcements?index=equities&symbol={symbol}"
    resp = nselib.get(url)
    if resp and resp.status_code == 200:
        return resp.json()
    return []

announcements = fetch_announcements("COALINDIA")
for ann in announcements[:10]:
    if "AGM" in ann.get('attchmntText', '') or "Record date" in ann.get('attchmntText', ''):
        print(ann)
