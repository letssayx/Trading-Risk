import requests
import time
import os

res = requests.get('http://localhost:8000/api/special-sit/dividends')
if res.status_code == 200:
    data = res.json()
    print("Success. Total items:", len(data.get('data', [])))
else:
    print("Failed.", res.status_code)
    print(res.text)
