import requests
import time

try:
    resp = requests.get("http://localhost:8000/api/data/view/list?type=mwpl&limit=5000&latest=true")
    print(resp.status_code)
    print(resp.text)
except Exception as e:
    print(e)
