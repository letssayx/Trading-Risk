from curl_cffi import requests
import time

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Connection": "keep-alive",
}

session = requests.Session(impersonate="chrome120")
print("Priming main site...")
resp = session.get("https://www.nseindia.com", headers=headers)
print(f"Main site status: {resp.status_code}")
time.sleep(2)

print("Fetching archives...")
# Try the old nseindia url, it sometimes redirects properly or shares session
url = "https://nsearchives.nseindia.com/content/nsccl/Contract_Delta_28032025.csv"
session.headers.update({"Referer": "https://www.nseindia.com/"})
resp2 = session.get(url)
print(f"Archives status: {resp2.status_code}")
