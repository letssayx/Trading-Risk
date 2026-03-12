import requests

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'en-US,en;q=0.9',
}

session = requests.Session()
session.get("https://www.nseindia.com", headers=headers, timeout=10)

# Check all possible data endpoints related to OFS and Tender from NSE docs/network tabs
endpoints = [
    "https://www.nseindia.com/api/live-analysis-ofs",
    "https://www.nseindia.com/api/live-ofs",
    "https://www.nseindia.com/api/ipo-ofs-issue?type=active",
    "https://www.nseindia.com/api/ipo-ofs-issue?type=forthcoming",
    "https://www.nseindia.com/api/ipo-ofs-issue?type=past",
    "https://www.nseindia.com/api/ipo-tender-offer?type=active",
    "https://www.nseindia.com/api/corporate-tender-offer?type=active",
    "https://www.nseindia.com/api/ipo-detail?type=ofs"
]

for url in endpoints:
    try:
        res = session.get(url, headers=headers, timeout=5)
        print(f"URL: {url} | Status: {res.status_code}")
        if res.status_code == 200:
            print(list(res.json().keys()))
    except:
        pass
