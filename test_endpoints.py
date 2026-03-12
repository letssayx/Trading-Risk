import requests

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
    'Accept': 'application/json',
}

session = requests.Session()
session.get("https://www.nseindia.com", headers=headers, timeout=10)

print("\n--- Testing Corporate Filings ---")
endpoints = [
    "https://www.nseindia.com/api/corporates-corporateActions?index=equities",
    "https://www.nseindia.com/api/corporate-announcements?index=equities",
    "https://www.nseindia.com/api/event-calendar"
]
for url in endpoints:
    res = session.get(url, headers=headers, timeout=5)
    print(f"{url}: {res.status_code}")

print("\n--- Testing Public Issues API Guesses ---")
guesses = [
    "https://www.nseindia.com/api/live-analysis-ofs?type=active",
    "https://www.nseindia.com/api/live-analysis-ofs",
    "https://www.nseindia.com/api/ipo-ofs-issue",
    "https://www.nseindia.com/api/corporate-tender-offer",
    "https://www.nseindia.com/api/ipo-tender-offer",
    "https://www.nseindia.com/api/ipo-current-issue",
    "https://www.nseindia.com/api/corporate-further-issues-rits",
    "https://www.nseindia.com/api/ipo-detail?type=tender",
    "https://www.nseindia.com/api/ipo-detail?type=ofs"
]
for url in guesses:
    try:
        res = session.get(url, headers=headers, timeout=5)
        print(f"{url}: {res.status_code}")
    except:
        print(f"{url}: Error")
