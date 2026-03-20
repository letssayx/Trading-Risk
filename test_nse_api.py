import json
from curl_cffi import requests

session = requests.Session(impersonate="chrome120")
session.get("https://www.nseindia.com", timeout=10)

url = "https://www.nseindia.com/api/corporates-corporateActions?index=equities&from=01-01-2025&to=01-01-2025&csv=true"
res = session.get(url)
print("01-01-2025 status:", res.status_code)
if res.status_code == 200:
    print(res.text[:500])

url2 = "https://www.nseindia.com/api/corporate-board-meetings?index=equities&from=01-01-2025&to=01-01-2025&csv=true"
res2 = session.get(url2)
print("01-01-2025 BM status:", res2.status_code)
if res2.status_code == 200:
    print(res2.text[:500])
