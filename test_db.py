from backend.main import app
from fastapi.testclient import TestClient

client = TestClient(app)
response = client.get("/api/data/view/list?type=dividend&limit=5")
print(f"Status: {response.status_code}")
print(f"Content: {response.text}")
