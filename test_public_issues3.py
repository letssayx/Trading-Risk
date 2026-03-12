import requests
import json

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
    'Accept': 'application/json',
}

session = requests.Session()
session.get("https://www.nseindia.com", headers=headers, timeout=10)

url = "https://www.nseindia.com/api/ipo-detail?type=ofs"
res = session.get(url, headers=headers, timeout=10)
try:
    print(json.dumps(res.json(), indent=2)[:500])
except Exception as e:
    print(res.text[:500])
    print("Error:", e)
