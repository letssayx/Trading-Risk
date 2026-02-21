import requests

url = "http://127.0.0.1:8000/api/data/upload/bhavcopy/preview"
files = {'file': open('test_data/fo.zip', 'rb')}
try:
    r = requests.post(url, files=files)
    print(r.status_code)
    print(r.json())
except Exception as e:
    print(e)
