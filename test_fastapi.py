from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)
response = client.get("/api/data/view/list?type=dividend&limit=2")
print("Status:", response.status_code)
print("Data:", response.json())
