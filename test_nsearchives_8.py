from curl_cffi import requests
# Maybe the URL is case sensitive or wrong now
urls_to_test = [
    "https://nsearchives.nseindia.com/content/nsccl/Contract_Delta_28032025.csv",
    "https://nsearchives.nseindia.com/content/nsccl/contract_delta_28032025.csv",
    "https://nsearchives.nseindia.com/archives/nsccl/delta/Contract_Delta_28032025.csv",
    "https://nsearchives.nseindia.com/archives/nsccl/delta/N_DELTA_TRD_28032025.csv",
    "https://nsearchives.nseindia.com/archives/nsccl/delta/N_DELTA_TRD_28032025.DAT"
]

session = requests.Session(impersonate="chrome120")
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
})

for url in urls_to_test:
    resp = session.get(url, timeout=5)
    print(f"URL {url.split('/')[-1]} -> {resp.status_code}")
