from curl_cffi import requests
# Maybe try without impersonate, just a normal curl request
import subprocess
try:
    res = subprocess.run(["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", "https://nsearchives.nseindia.com/content/nsccl/Contract_Delta_28032025.csv"], capture_output=True, text=True)
    print(f"Basic Curl status code: {res.stdout}")
except Exception as e:
    print(f"Curl failed: {e}")

# What about the python requests module?
import requests as r
resp = r.get("https://nsearchives.nseindia.com/content/nsccl/Contract_Delta_28032025.csv")
print(f"Requests module status code: {resp.status_code}")
