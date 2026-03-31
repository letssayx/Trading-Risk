import urllib.request
import ssl

ctx = ssl.create_default_context()
ctx.set_ciphers('DEFAULT@SECLEVEL=1')
req = urllib.request.Request(
    'https://nsearchives.nseindia.com/content/nsccl/Contract_Delta_28032025.csv',
    headers={'User-Agent': 'curl/7.68.0'}
)
try:
    with urllib.request.urlopen(req, context=ctx) as response:
        print("urllib status:", response.status)
except Exception as e:
    print("urllib error:", e)
