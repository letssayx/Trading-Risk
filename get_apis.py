import requests
from bs4 import BeautifulSoup
import re

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
}

session = requests.Session()
session.get("https://www.nseindia.com", headers=headers, timeout=10)

urls = [
    "https://www.nseindia.com/market-data/public-issues-rights-rits",
    "https://www.nseindia.com/market-data/public-issues-offer-for-sale-ofs",
    "https://www.nseindia.com/market-data/public-issues-tender"
]

for url in urls:
    res = session.get(url, headers=headers, timeout=10)
    print(f"\n--- {url} ({res.status_code}) ---")
    if res.status_code == 200:
        matches = re.findall(r'(/api/[a-zA-Z0-9\-\_\?=]+)', res.text)
        print(set(matches))
