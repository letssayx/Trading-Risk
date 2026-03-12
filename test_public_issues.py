import requests

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'en-US,en;q=0.9',
}

session = requests.Session()
session.get("https://www.nseindia.com", headers=headers, timeout=10)

endpoints = {
    'rights': "https://www.nseindia.com/api/corporate-further-issues-ri?index=equities&type=active",
    'ofs': "https://www.nseindia.com/api/corporate-further-issues-ofs?index=equities&type=active",
    'tender': "https://www.nseindia.com/api/corporate-further-issues-tender?index=equities&type=active"
}

for k, url in endpoints.items():
    res = session.get(url, headers=headers, timeout=5)
    print(f"{k}: {res.status_code}")
    if res.status_code == 200:
        print(f"Data length: {len(res.json().get('data', []))}")
