import requests

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "*/*",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive"
}

url = "https://nsearchives.nseindia.com/content/nsccl/Contract_Delta_28032025.csv"

# Don't prime via nseindia.com first, just go directly to archives
resp = requests.get(url, headers=headers)
print(f"requests Status: {resp.status_code}")

from curl_cffi import requests as cffi_req
cffi_session = cffi_req.Session(impersonate="chrome120")
cffi_resp = cffi_session.get(url, headers=headers)
print(f"curl_cffi Status: {cffi_resp.status_code}")
