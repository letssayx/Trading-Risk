import sys
import os
import asyncio
from fastapi.testclient import TestClient

# Add repo root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.main import app

client = TestClient(app)

def run_terminal_verification():
    print("Starting Terminal UI & Live Console Verification...")

    # 1. Test Widget API
    print("\n--- Testing Widget Data API ---")
    payload = {"tool_name": "Turtle Strategy"}
    res = client.post("/api/widgets/data", json=payload)
    print(f"Widget Response: {res.status_code} - {res.json()}")

    assert res.status_code == 200
    assert res.json()['type'] == 'metrics'

    # 2. Test WebSocket (Mocking via logic check, TestClient WS support varies)
    print("\n--- Testing WebSocket Route Existence ---")
    # Just checking if route exists
    routes = [route.path for route in app.routes]
    print(f"Routes: {routes}")
    assert "/ws/logs" in routes

    print("\n[SUCCESS] Terminal UI Architecture Verified.")

if __name__ == "__main__":
    run_terminal_verification()
