import subprocess
import time

def scrape_curl(url):
    cmd = [
        "curl", "-s",
        "-H", "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "-H", "Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "-H", "Accept-Language: en-US,en;q=0.9",
        "-H", "Cache-Control: max-age=0",
        "-H", "Sec-Fetch-Dest: document",
        "-H", "Sec-Fetch-Mode: navigate",
        "-H", "Sec-Fetch-Site: none",
        "-H", "Sec-Fetch-User: ?1",
        "-H", "Upgrade-Insecure-Requests: 1",
        "--compressed",
        "-o", "/dev/null",
        "-w", "%{http_code}",
        url
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    return res.stdout

print(scrape_curl("https://www.nseindia.com"))
print(scrape_curl("https://nsearchives.nseindia.com/content/nsccl/Contract_Delta_28032025.csv"))
