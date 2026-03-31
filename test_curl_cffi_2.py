from curl_cffi import requests

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Connection": "keep-alive",
}

# nsearchives url directly
session = requests.Session(impersonate="chrome120")
response = session.get("https://nsearchives.nseindia.com/content/nsccl/Contract_Delta_28032025.csv", headers=headers, timeout=10)
print(f"Status Code: {response.status_code}")
