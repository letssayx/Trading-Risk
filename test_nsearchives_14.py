import requests

# Let's try to get cookies from a totally blank session but hitting a different API
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': '*/*',
}
s = requests.Session()
r = s.get('https://www.nseindia.com/api/marketStatus', headers=headers)
print("marketStatus status:", r.status_code)
