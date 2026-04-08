import requests

try:
    print("Testing /api/data/analysis/oi/compute...")
    res = requests.post("http://localhost:8000/api/data/analysis/oi/compute")
    print(res.status_code, res.json())

    print("\nTesting /api/data/analysis/oi...")
    res2 = requests.get("http://localhost:8000/api/data/analysis/oi")
    print(res2.status_code)
    data = res2.json()
    if 'data' in data:
        print(f"Got {len(data['data'])} records.")
    else:
        print(data)
except Exception as e:
    print(f"Error: {e}")
