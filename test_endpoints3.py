import requests

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
    'Accept': 'application/json',
}

session = requests.Session()
session.get("https://www.nseindia.com", headers=headers, timeout=10)

# Let's hit the main API page for these. Since "rights-rits" etc are the web pages, what API do they call?
urls = [
    "https://www.nseindia.com/api/ipo-current-issue?type=ofs",
    "https://www.nseindia.com/api/ipo-current-issue?type=tender",
    "https://www.nseindia.com/api/ipo-current-issue?type=rits",
    "https://www.nseindia.com/api/corporate-further-issues-ofs?index=equities",
    "https://www.nseindia.com/api/corporate-further-issues-tender?index=equities",
    "https://www.nseindia.com/api/corporate-further-issues-rits?index=equities"
]
for url in urls:
    res = session.get(url, headers=headers, timeout=5)
    print(f"\n{url}: {res.status_code}")
    if res.ok:
        try:
            print(res.json()[:2] if isinstance(res.json(), list) else list(res.json().keys()))
        except Exception as e:
            pass
