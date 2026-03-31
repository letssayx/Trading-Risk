from curl_cffi import requests
session = requests.Session(impersonate="chrome120")
url = "https://nsearchives.nseindia.com/content/nsccl/Contract_Delta_28032025.csv"
resp = session.get(url, headers={
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
})
print("No cookie archives:", resp.status_code)
