import requests

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'application/json',
    'Accept-Language': 'en-US,en;q=0.9',
}
session = requests.Session()
session.get('https://www.nseindia.com', headers=headers, timeout=10)

url = "https://www.nseindia.com/api/financial-results?index=equities&symbol=HDFCAMC&period=Quarterly"
response = session.get(url, headers=headers, timeout=10)
print(response.status_code)
