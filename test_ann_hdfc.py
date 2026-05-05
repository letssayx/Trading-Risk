import requests
import json

url = "https://www.nseindia.com/api/corporate-announcements?index=equities&symbol=HDFCAMC"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'application/json',
    'Accept-Language': 'en-US,en;q=0.9',
}
session = requests.Session()
session.get('https://www.nseindia.com', headers=headers, timeout=5)
response = session.get(url, headers=headers, timeout=5)
if response.status_code == 200:
    data = response.json()
    for item in data:
        print(json.dumps(item, indent=2))
