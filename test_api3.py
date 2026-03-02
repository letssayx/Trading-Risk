import requests
import json

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'en-US,en;q=0.9',
}

session = requests.Session()
session.get("https://www.nseindia.com", headers=headers, timeout=10)

print("\nFetching Board Meetings with index=equities...")
res2 = session.get("https://www.nseindia.com/api/corporate-board-meetings?index=equities", headers=headers, timeout=10)
print("BM Response:", res2.status_code)
if res2.status_code == 200:
    try:
        data = res2.json()
        print("Preview:", str(data)[:200])
        if isinstance(data, list) and len(data) > 0:
            print("Board Meetings Keys:", data[0].keys())
        elif isinstance(data, dict) and 'data' in data and len(data['data']) > 0:
             print("Board Meetings Keys:", data['data'][0].keys())
    except Exception as e:
        print("Error parsing json", e)
