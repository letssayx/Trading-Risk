from curl_cffi import requests

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Connection": "keep-alive",
}

session = requests.Session(impersonate="chrome110")
response = session.get("https://nsearchives.nseindia.com", headers=headers, timeout=10)
print(f"Archives Status Code: {response.status_code}")

# Let's see if we can get around it with curl
import subprocess
try:
    res = subprocess.run(["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", "-A", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36", "https://nsearchives.nseindia.com/content/nsccl/Contract_Delta_28032025.csv"], capture_output=True, text=True)
    print(f"Curl status code: {res.stdout}")
except Exception as e:
    print(f"Curl failed: {e}")
