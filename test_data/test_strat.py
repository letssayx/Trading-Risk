import requests

url = "http://127.0.0.1:8000/api/strategies/turtle/start"
try:
    r = requests.post(url, json={"symbol": "RELIANCE", "risk_per_trade": 0.01})
    print(r.status_code)
    print(r.text)
except Exception as e:
    print(e)
