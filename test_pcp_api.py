import requests

url = "http://localhost:8000/api/data/derivatives/put_call_parity?symbol=NIFTY"
response = requests.get(url)
print(response.status_code)
if response.status_code == 200:
    data = response.json()
    print("Data count:", len(data.get("data", [])))
    if len(data.get("data", [])) > 0:
        print("First row:", data["data"][0])
        print("Futures keys:", list(data.get("futures", {}).keys()))
else:
    print(response.text)
