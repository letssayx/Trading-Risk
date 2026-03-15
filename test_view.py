import requests
res = requests.get('http://127.0.0.1:8000/api/data/view/list?type=fii_dii_cash&limit=500')
print(res.status_code)
