import requests

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
    'Accept': 'application/json',
}

session = requests.Session()
session.get("https://www.nseindia.com", headers=headers, timeout=10)

print("\n--- Examining Public Issues Working Endpoints ---")
urls = [
    "https://www.nseindia.com/api/ipo-current-issue",
    "https://www.nseindia.com/api/ipo-detail?type=tender",
    "https://www.nseindia.com/api/ipo-detail?type=ofs"
]
for url in urls:
    res = session.get(url, headers=headers, timeout=5)
    print(f"\n{url}: {res.status_code}")
    if res.ok:
        try:
            print(res.json())
        except Exception as e:
            print("Failed to decode JSON:", e)
            print(res.text[:200])
