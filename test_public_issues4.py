import requests
import json

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
    'Accept': 'application/json',
}

session = requests.Session()
session.get("https://www.nseindia.com", headers=headers, timeout=10)

# Check the old endpoints again but with active/forthcoming/past parameters as mentioned by the user
urls = [
    "https://www.nseindia.com/api/ipo-ofs-issue?type=active",
    "https://www.nseindia.com/api/ipo-ofs-issue?type=forthcoming",
    "https://www.nseindia.com/api/ipo-ofs-issue?type=past",
    "https://www.nseindia.com/api/live-analysis-ofs",
    "https://www.nseindia.com/api/corporate-tender-offer"
]
for url in urls:
    res = session.get(url, headers=headers, timeout=5)
    print(f"{url}: {res.status_code}")
