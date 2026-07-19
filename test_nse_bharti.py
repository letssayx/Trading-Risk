import datetime
import urllib.request
import json
import ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

req = urllib.request.Request(
    'https://www.nseindia.com',
    headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36', 'Accept': '*/*'}
)
try:
    urllib.request.urlopen(req, context=ctx, timeout=5)
except:
    pass

url_ann = "https://www.nseindia.com/api/corporate-announcements?index=equities&symbol=BHARTIARTL&from_date=08-07-2026&to_date=12-07-2026"
print("Fetching announcements...")
try:
    req = urllib.request.Request(url_ann, headers={'User-Agent': 'Mozilla/5.0'})
    resp = urllib.request.urlopen(req, context=ctx, timeout=10)
    print("Status:", resp.status)
    print(resp.read().decode('utf-8'))
except Exception as e:
    print("Error:", e)
