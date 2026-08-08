import urllib.request
import json
import ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': '*/*',
    'Referer': 'https://www.nseindia.com/',
    'Accept-Language': 'en-US,en;q=0.9',
}
print("--- COALINDIA ---")
url = "https://www.nseindia.com/api/corporate-announcements?index=equities&symbol=COALINDIA"
req = urllib.request.Request(url, headers=headers)
try:
    with urllib.request.urlopen(req, context=ctx) as response:
        data = json.loads(response.read().decode('utf-8'))
        for item in data:
            if '2026' in item.get('an_dt', ''):
                print(item.get('desc'), "|||", item.get('attchmntText'))
except Exception as e:
    pass

print("--- DLF ---")
url = "https://www.nseindia.com/api/corporate-announcements?index=equities&symbol=DLF"
req = urllib.request.Request(url, headers=headers)
try:
    with urllib.request.urlopen(req, context=ctx) as response:
        data = json.loads(response.read().decode('utf-8'))
        for item in data:
            if '2026' in item.get('an_dt', ''):
                print(item.get('desc'), "|||", item.get('attchmntText'))
except Exception as e:
    pass
