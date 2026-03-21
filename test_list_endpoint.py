from fastapi.testclient import TestClient
from backend.main import app
import sys
import logging

logging.basicConfig(level=logging.ERROR, stream=sys.stdout)

client = TestClient(app)

response = client.get("/api/data/view/list?type=dividend&limit=5")
print(f"Status: {response.status_code}")
print(f"Content: {response.text}")
