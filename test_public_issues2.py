import requests

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
    'Accept': 'application/json',
}

session = requests.Session()
session.get("https://www.nseindia.com", headers=headers, timeout=10)

# Let's try to find the actual API urls for OFS and tender.
urls = [
    "https://www.nseindia.com/api/live-analysis-ofs",
    "https://www.nseindia.com/api/live-ofs",
    "https://www.nseindia.com/api/corporate-tender",
    "https://www.nseindia.com/api/live-tender",
    "https://www.nseindia.com/api/tender-offer",
    "https://www.nseindia.com/api/ipo-detail?type=tender",
    "https://www.nseindia.com/api/ipo-detail?type=ofs",
]

for url in urls:
    res = session.get(url, headers=headers, timeout=5)
    print(f"{url}: {res.status_code}")
