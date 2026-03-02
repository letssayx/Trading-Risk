import requests
import json

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'en-US,en;q=0.9',
}

session = requests.Session()
session.get("https://www.nseindia.com", headers=headers, timeout=10)

print("Fetching Corporate Actions...")
res = session.get("https://www.nseindia.com/api/corporates-corporateActions?index=equities", headers=headers, timeout=10)
if res.status_code == 200:
    data = res.json()
    if isinstance(data, list) and len(data) > 0:
        print("Corporate Actions Keys:", data[0].keys())
        print("First item:", json.dumps(data[0], indent=2))
    elif isinstance(data, dict) and 'data' in data and len(data['data']) > 0:
        print("Corporate Actions Keys:", data['data'][0].keys())
        print("First item:", json.dumps(data['data'][0], indent=2))
    else:
        print("Data is empty or unrecognized format.")
else:
    print("Failed to fetch CA:", res.status_code)

print("\nFetching Board Meetings...")
res2 = session.get("https://www.nseindia.com/api/corporate-board-meetings", headers=headers, timeout=10)
if res2.status_code == 200:
    data = res2.json()
    if isinstance(data, list) and len(data) > 0:
        print("Board Meetings Keys:", data[0].keys())
        print("First item:", json.dumps(data[0], indent=2))
    elif isinstance(data, dict) and 'data' in data and len(data['data']) > 0:
        print("Board Meetings Keys:", data['data'][0].keys())
        print("First item:", json.dumps(data['data'][0], indent=2))
    else:
        print("Data is empty or unrecognized format.")
else:
    print("Failed to fetch BM:", res2.status_code)
