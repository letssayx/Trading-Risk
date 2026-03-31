from curl_cffi import requests
import urllib3

# Suppress insecure request warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Just plain curl but with TLS fingerprinting bypassed or minimal
# curl_cffi impersonate handles the TLS fingerprinting, let's try different ones
impersonates = ["chrome100", "chrome101", "chrome104", "chrome110", "chrome116", "edge99", "edge101", "safari15_3", "safari15_5"]

for imp in impersonates:
    try:
        session = requests.Session(impersonate=imp)
        resp = session.get("https://nsearchives.nseindia.com/content/nsccl/Contract_Delta_28032025.csv", timeout=5)
        print(f"{imp}: {resp.status_code}")
    except Exception as e:
        print(f"{imp} failed: {e}")
