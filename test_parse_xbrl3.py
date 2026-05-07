import curl_cffi.requests as req_mod

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36",
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.5",
}

# The user explicitly said:
# "find a new solution to get it from NSE website its easy,
# use this https://www.nseindia.com/companies-listing/corporate-filings-announcements?symbol=TCS&tabIndex=equity
# there is a dropdown announcements, you need to read that xbrl file and parse the dividend amount and date"
# Let's check what the API response from corporate-announcements looks like again. Maybe I missed the field.

r = req_mod.get("https://www.nseindia.com/api/corporate-announcements?index=equities&symbol=TCS", headers=headers, impersonate="chrome110")
for item in r.json()[:10]:
    print(item.get("desc"), "hasXbrl:", item.get("hasXbrl"), "attchmntFile:", item.get("attchmntFile"))
