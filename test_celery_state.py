import requests
import json
import time
from backend.main import app
from fastapi.testclient import TestClient

client = TestClient(app)

print("Starting prepare data task...")
response = client.post("/api/morning-report/prepare", json={"target_date": "2024-02-28", "end_date": "2024-02-29"})
print("Prepare response:", response.status_code, response.json())

task_id = response.json().get("task_id")
if task_id:
    for i in range(5):
        time.sleep(1)
        res = client.get(f"/api/morning-report/status/{task_id}")
        print(f"Poll {i+1}:", res.json())
