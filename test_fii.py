import datetime
import requests

url = f"https://www.nseindia.com/api/fiidiiTradeReact"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "*/*",
    "Connection": "keep-alive"
}
try:
    s = requests.Session()
    s.get("https://www.nseindia.com", headers=headers, timeout=10)
    resp = s.get(url, headers=headers, timeout=10)
    print(resp.status_code)
    print(resp.text[:500])
except Exception as e:
    print(e)
