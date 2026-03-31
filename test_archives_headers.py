# What if we need EXACTLY the headers a browser sends to static files?
from curl_cffi import requests
session = requests.Session(impersonate="chrome120")
url = "https://nsearchives.nseindia.com/content/nsccl/Contract_Delta_28032025.csv"

# Browser downloading a CSV file directly from URL bar sends:
headers = {
    "Host": "nsearchives.nseindia.com",
    "Connection": "keep-alive",
    "sec-ch-ua": "\"Not A(Brand\";v=\"99\", \"Google Chrome\";v=\"121\", \"Chromium\";v=\"121\"",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "\"Windows\"",
    "Upgrade-Insecure-Requests": "1",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-User": "?1",
    "Sec-Fetch-Dest": "document",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept-Language": "en-US,en;q=0.9",
}

resp = session.get(url, headers=headers)
print("Spoofed exact headers:", resp.status_code)
