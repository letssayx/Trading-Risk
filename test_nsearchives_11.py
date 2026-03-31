# The user's trace has: "Got 403, re-priming session..."
# Is it possible that the new website URL structure has changed, or we need an API endpoint to fetch the archive link?
# Let's check nseindia API for contract delta or see if we can get another URL format.
import requests

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Connection': 'keep-alive',
}
s = requests.Session()
# Don't try to access nsearchives, maybe just try nseindia.com/api/historical/fo/derivatives...
resp = s.get('https://www.nseindia.com/api/reports?archives=1', headers=headers)
print(f"API Reports status: {resp.status_code}")
