import sys
import os
from fastapi.testclient import TestClient

# Add repo root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.main import app

client = TestClient(app)

def run_ui_wiring_tests():
    print("Starting Terminal UI Wiring Verification...")

    # 1. PnL Audit
    print("\n--- Testing PnL Audit API ---")
    res_pnl = client.post("/api/widgets/data", json={"tool_name": "pnl_audit"})
    print(f"PnL Response: {res_pnl.json()}")
    assert res_pnl.status_code == 200
    data = res_pnl.json()['data']
    assert "nav" in data
    assert "drawdown" in data

    # 2. Risk Scorecard
    print("\n--- Testing Risk Scorecard API ---")
    res_risk = client.post("/api/widgets/data", json={"tool_name": "risk_scorecard"})
    print(f"Risk Response: {res_risk.json()}")
    assert res_risk.status_code == 200
    r_data = res_risk.json()['data']
    assert "delta" in r_data
    assert "gamma" in r_data

    print("\n[SUCCESS] UI Wiring Verified.")

if __name__ == "__main__":
    run_ui_wiring_tests()
