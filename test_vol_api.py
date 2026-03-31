import requests

try:
    r = requests.get('http://127.0.0.1:8000/api/data/derivatives/pre_expiry_action/NIFTY')
    print("Pre-Expiry:", r.status_code)
    print(str(r.json())[:500])
except Exception as e:
    print("Error:", e)
