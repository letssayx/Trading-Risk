import requests
from bs4 import BeautifulSoup
import json

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'application/json',
    'Accept-Language': 'en-US,en;q=0.9',
}
session = requests.Session()
session.get('https://www.nseindia.com', headers=headers, timeout=10)

url = "https://www.nseindia.com/api/corporate-announcements?index=equities&from_date=24-03-2026&to_date=25-04-2026&symbol=HDFCAMC"
response = session.get(url, headers=headers, timeout=10)
if response.status_code == 200:
    data = response.json()
    for item in data:
         if item.get("seq_id") == "106591395":
             # Try scraping the xbrl URL directly from the announcements board page? No, we need the XML file.
             # The zip file contains the xml?
             print(item)
