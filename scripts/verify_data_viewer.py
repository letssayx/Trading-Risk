import sys
import os

# Set DATABASE_URL to use SQLite for testing
os.environ["DATABASE_URL"] = "sqlite:///./test.db"

# Add project root to sys.path
sys.path.append(os.getcwd())

from fastapi.testclient import TestClient
from backend.main import app

def test_view_data():
    print("Testing /api/data/view endpoint...")

    # Use context manager to trigger startup events (table creation)
    with TestClient(app) as client:
        # Valid date format
        response = client.get("/api/data/view?segment=CM&date=2026-02-19")

        if response.status_code == 200:
            print("✅ Request successful (200 OK)")
            data = response.json()
            print(f"   Received: {data}")
        elif response.status_code == 500:
            print("❌ FAILED: Internal Server Error (500)")
            print(f"   Response: {response.text}")
            sys.exit(1)
        else:
            print(f"⚠️ Unexpected status code: {response.status_code}")
            print(f"   Response: {response.text}")

        # Invalid date format should be handled gracefully (400)
        response_invalid = client.get("/api/data/view?segment=CM&date=invalid-date")
        if response_invalid.status_code == 500:
             print("❌ FAILED: Internal Server Error on invalid date")
             sys.exit(1)
        else:
             print(f"✅ Invalid date handled correctly (Status: {response_invalid.status_code})")

if __name__ == "__main__":
    try:
        test_view_data()
    finally:
        # Clean up test.db
        if os.path.exists("./test.db"):
            os.remove("./test.db")
