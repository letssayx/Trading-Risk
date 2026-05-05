import requests

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
}
session = requests.Session()
session.get('https://www.nseindia.com', headers=headers, timeout=10)

url = "https://www.nseindia.com/api/corporate-announcements?index=equities&symbol=HDFCAMC"
res = session.get(url, headers={'User-Agent': headers['User-Agent']})
for item in res.json():
    if item.get("seq_id") == "106591395":
        xbrl_file = item.get("attchmntFile").replace(".pdf", ".xml")
        print(f"Trying to fetch: {xbrl_file}")
        r = session.get(xbrl_file, headers=headers)
        print(r.status_code)
