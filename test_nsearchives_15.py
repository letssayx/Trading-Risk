# In memory: "Historical FII/DII gross trading data is scraped via a fallback mechanism in nse_lib.py using pure HTTP requests via curl_cffi"
# Let's inspect the exact nse_lib.py implementation of curl_cffi initialization
from curl_cffi import requests
from curl_cffi.requests.models import Response
s = requests.Session(impersonate="chrome110")
# The previous tests all gave 403. Let's see if the server itself is rejecting all requests from this sandbox IP entirely.
r = s.get('https://google.com')
print("Google:", r.status_code)
r = s.get('https://www.nseindia.com', headers={
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36',
    'Accept': '*/*'
})
print("NSE:", r.status_code)
