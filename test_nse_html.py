import requests
import json
import re
from bs4 import BeautifulSoup

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
    'Accept': 'text/html,application/xhtml+xml',
}

session = requests.Session()
session.get("https://www.nseindia.com", headers=headers, timeout=10)

urls = [
    "https://www.nseindia.com/market-data/public-issues-rights-rits",
    "https://www.nseindia.com/companies-listing/corporate-filings-actions",
    "https://www.nseindia.com/companies-listing/corporate-filings-announcements",
    "https://www.nseindia.com/companies-listing/corporate-filings-event-calendar"
]

for url in urls:
    print(f"\n--- Scraping {url} ---")
    res = session.get(url, headers=headers, timeout=10)
    if res.ok:
        soup = BeautifulSoup(res.text, 'html.parser')
        # find all data-url attributes
        for tag in soup.find_all(attrs={"data-url": True}):
            print(f"data-url: {tag['data-url']}")

        # look for typical api paths in scripts
        apis = set(re.findall(r'(/api/[a-zA-Z0-9\-\_\?\=\&]+)', res.text))
        print("Found API strings in HTML:", apis)
