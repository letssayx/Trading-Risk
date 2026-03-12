import requests

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'en-US,en;q=0.9',
}

session = requests.Session()
session.get("https://www.nseindia.com", headers=headers, timeout=10)

endpoints = [
    "https://www.nseindia.com/api/corporate-further-issues-ofs",
    "https://www.nseindia.com/api/corporate-further-issues-tender"
]

for url in endpoints:
    res = session.get(url, headers=headers, timeout=5)
    print(url, res.status_code)
