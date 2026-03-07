from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)
def test_endpoints():
    # Because backend.main includes it as: `app.include_router(analysis_routes.router)` (Wait, how is it included?)
    # Let's check how it's included...
    # Just try directly "/morning-report/prepare"
    print("Testing /api/morning-report/prepare...")
    response = client.post("/api/morning-report/prepare", json={"target_date": "2024-02-28"})
    print("Response status:", response.status_code)

    print("\nTesting /api/morning-report/generate...")
    response = client.post("/api/morning-report/generate", json={"target_date": "2024-02-28", "author": "Jules"})
    print("Response status:", response.status_code)

if __name__ == "__main__":
    test_endpoints()
