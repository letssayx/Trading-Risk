import requests

url = "https://nsearchives.nseindia.com/corporate/xbrl/HDFCAMC_16042026130308_BM.xml"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': '*/*',
}
session = requests.Session()
session.get('https://www.nseindia.com', headers=headers, timeout=10)

res = session.get(url, headers=headers)
print(res.status_code)
