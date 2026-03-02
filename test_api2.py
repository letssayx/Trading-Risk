import requests
import json

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'en-US,en;q=0.9',
}

session = requests.Session()
session.get("https://www.nseindia.com", headers=headers, timeout=10)

print("\nFetching Board Meetings...")
res2 = session.get("https://www.nseindia.com/api/corporate-board-meetings", headers=headers, timeout=10)
print("BM Response:", res2.status_code)
if res2.status_code == 200:
    try:
        print("Raw JSON length:", len(res2.content))
        print("Preview:", res2.text[:200])
    except Exception as e:
        print("Error parsing json", e)
