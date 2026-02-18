import sys
import os
import time
from fastapi.testclient import TestClient

# Add project root to sys.path
sys.path.append(os.getcwd())

# Set DATABASE_URL to use SQLite for testing
os.environ["DATABASE_URL"] = "sqlite:///./test.db"

from backend.main import app
from backend.infrastructure.db import Base, engine, SessionLocal
from backend.domain.market.models import Bhavcopy
from datetime import datetime, date

# Initialize DB
Base.metadata.create_all(bind=engine)

def seed_db():
    db = SessionLocal()
    # Check if empty
    if db.query(Bhavcopy).count() == 0:
        print("Seeding DB with mock Bhavcopy data...")
        b1 = Bhavcopy(
            trade_date=date(2026, 2, 19),
            segment="CM",
            instrument_type="EQ",
            symbol="RELIANCE",
            series="EQ",
            open=2000.0,
            high=2050.0,
            low=1990.0,
            close=2040.0,
            total_traded_qty=100000
        )
        b2 = Bhavcopy(
            trade_date=date(2026, 2, 18),
            segment="CM",
            instrument_type="EQ",
            symbol="RELIANCE",
            series="EQ",
            open=1950.0,
            high=2010.0,
            low=1940.0,
            close=2000.0,
            total_traded_qty=90000
        )
        db.add(b1)
        db.add(b2)
        db.commit()
    db.close()

client = TestClient(app)

def test_endpoints():
    print("Testing Enhanced Endpoints...")

    # 1. Search
    res = client.get("/api/symbols/search?q=REL")
    print(f"Search 'REL': {res.status_code}")
    assert res.status_code == 200
    data = res.json()
    print(f"  Results: {data}")
    if "RELIANCE" in data:
        print("✅ Search OK")
    else:
        print("❌ Search Failed (RELIANCE not found)")

    # 2. Historical Data (DB backed)
    res = client.get("/api/historical/RELIANCE")
    print(f"History 'RELIANCE': {res.status_code}")
    assert res.status_code == 200
    data = res.json()
    print(f"  Rows: {len(data)}")
    if len(data) >= 2: # Seeded 2
        print("✅ History OK (Found DB data)")
        print(f"  Last Close: {data[-1]['close']}")
    else:
        print("⚠️ History Warning: Expected >= 2 rows")

    # 3. Strategy Start/Pause/Resume/Remove
    # Start
    res = client.post("/api/strategies/turtle/start", json={"symbol": "RELIANCE", "risk_per_trade": 0.01})
    print(f"Start Strategy: {res.status_code}")
    assert res.status_code == 200
    inst_id = res.json()["instanceId"]
    print(f"  ID: {inst_id}")

    # Pause
    res = client.post(f"/api/strategies/turtle/pause/{inst_id}")
    print(f"Pause: {res.status_code}, {res.json()}")
    assert res.status_code == 200

    # Resume
    res = client.post(f"/api/strategies/turtle/resume/{inst_id}")
    print(f"Resume: {res.status_code}, {res.json()}")
    assert res.status_code == 200

    # Remove
    res = client.post(f"/api/strategies/turtle/remove/{inst_id}")
    print(f"Remove: {res.status_code}, {res.json()}")
    assert res.status_code == 200

    # 4. Jules (Mock check)
    # Without API Key, it should return instruction
    res = client.post("/api/jules/chat", json={"message": "Hello"})
    print(f"Jules Chat: {res.status_code}")
    print(f"  Reply: {res.json()['reply']}")
    if "Please configure" in res.json()['reply'] or "error" in res.json()['reply']:
        print("✅ Jules OK (Handled missing key gracefully)")

if __name__ == "__main__":
    try:
        seed_db()
        test_endpoints()
    finally:
        if os.path.exists("test.db"):
            os.remove("test.db")
