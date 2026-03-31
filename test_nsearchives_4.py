import subprocess
import time

def try_curl(url):
    cmd = [
        "curl", "-s",
        "-H", "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0",
        "-H", "Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "-H", "Accept-Language: en-US,en;q=0.5",
        "-H", "Connection: keep-alive",
        "-H", "Upgrade-Insecure-Requests: 1",
        "-H", "Sec-Fetch-Dest: document",
        "-H", "Sec-Fetch-Mode: navigate",
        "-H", "Sec-Fetch-Site: none",
        "-H", "Sec-Fetch-User: ?1",
        "-w", "%{http_code}",
        "-o", "/dev/null",
        url
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    return res.stdout

print("Firefox spoof:")
print("NSE India main:", try_curl("https://www.nseindia.com"))
time.sleep(1)
print("NSE Archives:", try_curl("https://nsearchives.nseindia.com/content/nsccl/Contract_Delta_28032025.csv"))
