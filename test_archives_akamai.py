from curl_cffi import requests
# Try hitting nseindia with curl_cffi on a completely different impersonate
print("Try safari15_3")
print(requests.get("https://nsearchives.nseindia.com/content/nsccl/Contract_Delta_28032025.csv", impersonate="safari15_3").status_code)

print("Try chrome110")
print(requests.get("https://nsearchives.nseindia.com/content/nsccl/Contract_Delta_28032025.csv", impersonate="chrome110").status_code)
