import curl_cffi.requests as req_mod

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36",
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.5",
}

# The user showed an image where they are on: https://www.nseindia.com/companies-listing/corporate-filings-announcements?symbol=TCS&tabIndex=equity
# It loads from the /api/corporate-announcements?index=equities&symbol=TCS endpoint.
# But in my script `test_nse_api_cffi_xb_all.py` the `xbrl` field is None or missing for everything!

# Wait, the URL the user shared is the exact same one but let's see if xbrl shows up for some other recent ones.
r = req_mod.get("https://www.nseindia.com/api/corporate-announcements?index=equities&symbol=TCS", headers=headers, impersonate="chrome110")
print("TCS status:", r.status_code)
for item in r.json()[:20]:
    if item.get("xbrl") or "http" in str(item.get("xbrl")):
        print(item.get("desc"), item.get("xbrl"))
