import requests

symbol = "WIPRO"
try:
    res = requests.get(f"http://localhost:8000/api/data/shareholding?symbol={symbol}")
    print(res.json())
except Exception as e:
    print(e)
