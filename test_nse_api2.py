import json
from curl_cffi import requests

session = requests.Session(impersonate="chrome120")
session.get("https://www.nseindia.com", timeout=10)

url = "https://www.nseindia.com/api/corporates-corporateActions?index=equities&from_date=01-01-2025&to_date=01-01-2025"
res = session.get(url)
print("01-01-2025 json status:", res.status_code)
if res.status_code == 200:
    try:
        data = res.json()
        print(len(data), "records found")
        if len(data) > 0:
             print(data[0])
    except:
        print("not json")

url2 = "https://www.nseindia.com/api/corporate-board-meetings?index=equities&from_date=01-01-2025&to_date=01-01-2025"
res2 = session.get(url2)
print("01-01-2025 BM status:", res2.status_code)
if res2.status_code == 200:
    try:
        data = res2.json()
        print(len(data), "records found")
    except:
        print("not json")
