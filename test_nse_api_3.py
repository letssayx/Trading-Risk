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
    "ofs_1": "https://www.nseindia.com/api/live-ofs-issue?type=active",
    "ofs_2": "https://www.nseindia.com/api/ipo-ofs-issue",
    "ofs_3": "https://www.nseindia.com/api/corporates-ofs",
    "tender_1": "https://www.nseindia.com/api/tender-offer",
    "tender_2": "https://www.nseindia.com/api/corporates-tender",
    "rights_rits": "https://www.nseindia.com/api/corporate-further-issues-ri",
    "rights_rits_2": "https://www.nseindia.com/api/corporates-rits",
    "buyback": "https://www.nseindia.com/api/live-buyback-issue"
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
        else:
            print("Failed.")
    except Exception as e:
        print(f"Error: {e}")
