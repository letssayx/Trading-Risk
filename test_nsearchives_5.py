from curl_cffi import requests
session = requests.Session(impersonate="chrome124")
# We need to try some more realistic browser fingerprints, or maybe try the new domains
resp = session.get("https://nsearchives.nseindia.com/content/nsccl/Contract_Delta_28032025.csv")
print(resp.status_code)

print("Try getting the index file:")
resp = session.get("https://nsearchives.nseindia.com/")
print(resp.status_code)
