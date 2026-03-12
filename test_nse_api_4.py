import requests
import json
from bs4 import BeautifulSoup

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
}

session = requests.Session()
session.get("https://www.nseindia.com", headers=headers, timeout=10)

url = "https://www.nseindia.com/market-data/public-issues-offer-for-sale-ofs"
print(f"Fetching {url}")
res = session.get(url, headers=headers, timeout=10)
print(res.status_code)

if res.status_code == 200:
    soup = BeautifulSoup(res.text, 'html.parser')
    # Look for any data-url attributes or script tags containing JSON paths
    for el in soup.find_all(attrs={"data-url": True}):
        print("Found data-url:", el['data-url'])
