import requests

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'application/json',
    'Accept-Language': 'en-US,en;q=0.9',
}
session = requests.Session()
session.get('https://www.nseindia.com', headers=headers, timeout=10)

url = "https://www.nseindia.com/api/corporate-board-meetings?index=equities&symbol=HDFCAMC"
response = session.get(url, headers=headers, timeout=5)
if response.status_code == 200:
    data = response.json()
    for item in data:
         if item.get("bm_date") == "16-Apr-2026":
             print(f"BM Item: {item.get('bm_purpose')} | XBRL: {item.get('ixbrl')} | XML: {item.get('attachment')}")
