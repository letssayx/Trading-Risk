import urllib.request

req = urllib.request.Request(
    'https://nsearchives.nseindia.com/content/nsccl/Contract_Delta_28032025.csv',
    headers={'User-Agent': 'Mozilla/5.0'}
)
try:
    with urllib.request.urlopen(req) as response:
        print("urllib status:", response.status)
except Exception as e:
    print("urllib error:", e)
