# Let's try to bypass Akamai using python-tls-client or specific curl-cffi options
from curl_cffi import requests
session = requests.Session(impersonate="safari15_5")
resp = session.get("https://nsearchives.nseindia.com/content/nsccl/Contract_Delta_28032025.csv")
print("safari:", resp.status_code)

session = requests.Session(impersonate="chrome120")
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
})
resp = session.get("https://www.nseindia.com")
print("chrome120 nseindia:", resp.status_code)
