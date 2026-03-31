# Let's see if we can get around the 403 block by simulating exactly what nse_lib.py was doing but with curl_cffi and fixing headers
from curl_cffi import requests
import time
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
}

session = requests.Session(impersonate="chrome120")
# Priming step
try:
    print("Priming...")
    r = session.get("https://www.nseindia.com", headers=headers, timeout=10)
    print("Prime main:", r.status_code)
except Exception as e:
    print("Prime error", e)

# The archive link
try:
    print("Fetching archive...")
    # we need referer
    headers["Referer"] = "https://www.nseindia.com/"
    r2 = session.get("https://nsearchives.nseindia.com/content/nsccl/Contract_Delta_28032025.csv", headers=headers, timeout=10)
    print("Fetch archive:", r2.status_code)
except Exception as e:
    print("Fetch error", e)
