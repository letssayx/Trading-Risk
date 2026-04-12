import requests

try:
    response = requests.get('http://127.0.0.1:8000/api/data/derivatives/option_chain?symbol=NIFTY')
    print(response.status_code)
    print(response.json())
except Exception as e:
    print(f"Error: {e}")
