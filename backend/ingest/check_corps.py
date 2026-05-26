from nse_lib import NSELib
import json

lib = NSELib()
ca_url = 'https://www.nseindia.com/api/corporates-corporateActions?index=equities&symbol=MPHASIS'
r = lib.get(ca_url)
print(r.status_code)
if r and r.status_code == 200:
    for a in r.json():
        if '2026' in str(a.get('exDate', '')):
            print("CA:", a.get('exDate'), a.get('purpose'), a.get('recordDate'))
