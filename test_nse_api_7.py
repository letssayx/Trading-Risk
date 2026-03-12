import requests

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
    'Accept': 'application/json',
}

session = requests.Session()
session.get("https://www.nseindia.com", headers=headers)

res = session.get("https://www.nseindia.com/api/ipo-detail?type=ofs", headers=headers)
if res.ok:
    print(res.json())
