import curl_cffi.requests as req_mod

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36",
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.5",
}

# The user explicitly asked to "read that xbrl file and parse the dividend amount and date".
# The endpoint is https://www.nseindia.com/api/corporate-announcements-xbrl?index=equities&symbol=TCS maybe? Or something else?
# Let's try the xbrl endpoint for announcements.

r = req_mod.get("https://www.nseindia.com/api/corporate-announcements-xbrl?index=equities&symbol=TCS", headers=headers, impersonate="chrome110")
print("XBRL Endpoint status:", r.status_code)
try:
    for item in r.json()[:10]:
        print(item.get("desc"), item.get("seqId"), item.get("attachment"))
except:
    print("Failed to parse json or missing keys")
