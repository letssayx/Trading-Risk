import curl_cffi.requests as req_mod

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36",
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.5",
}
r = req_mod.get("https://www.nseindia.com/api/corporate-announcements?index=equities&symbol=TCS", headers=headers, impersonate="chrome110")
print(r.status_code)
if r.status_code == 200:
    for item in r.json()[:5]:
        print(item.get("desc"), item.get("xbrl"))
