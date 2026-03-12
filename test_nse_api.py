import requests
import json
import logging

logging.basicConfig(level=logging.INFO)

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'en-US,en;q=0.9',
}

session = requests.Session()
# Prime the session
try:
    session.get("https://www.nseindia.com", headers=headers, timeout=10)
except:
    pass

endpoints = {
    "circulars": "https://www.nseindia.com/api/circulars",
    "corp_actions": "https://www.nseindia.com/api/corporates-corporateActions?index=equities",
    "corp_announcements": "https://www.nseindia.com/api/corporate-announcements?index=equities",
    "event_calendar": "https://www.nseindia.com/api/event-calendar",
    "ofs": "https://www.nseindia.com/api/corporate-further-issues-ofs?index=equities&type=active",
    "tender": "https://www.nseindia.com/api/corporate-further-issues-tender?index=equities&type=active",
    "rits": "https://www.nseindia.com/api/ipo-current-issue" # guessing?
}

for name, url in endpoints.items():
    try:
        print(f"\n--- Testing {name} ---")
        res = session.get(url, headers=headers, timeout=10)
        print(f"Status: {res.status_code}")
        if res.status_code == 200:
            data = res.json()
            if isinstance(data, dict) and 'data' in data:
                items = data['data']
            elif isinstance(data, list):
                items = data
            else:
                items = [data]

            print(f"Count: {len(items)}")
            if len(items) > 0:
                print("Sample keys:", list(items[0].keys()))
                # Find any keys that look like attachments or PDFs
                for k, v in items[0].items():
                    if isinstance(v, str) and ('.pdf' in v.lower() or 'attachment' in k.lower() or 'file' in k.lower()):
                        print(f"Potential PDF key: {k} -> {v}")
        else:
            print("Failed.")
    except Exception as e:
        print(f"Error: {e}")
