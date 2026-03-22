import requests

try:
    resp = requests.get('http://127.0.0.1:8000/api/data/view/list?type=dividend&limit=5&symbol=PFC')
    print("STATUS:", resp.status_code)
    print("DATA:", resp.json())
except Exception as e:
    print("ERROR:", str(e))
