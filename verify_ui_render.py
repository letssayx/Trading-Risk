from fastapi.testclient import TestClient
from web.main import app

def verify_ui_render():
    print("Verifying UI Template Rendering...")

    client = TestClient(app)

    # 1. Test Dashboard Render
    print("1. Rendering Dashboard...")
    response = client.get("/dashboard")
    assert response.status_code == 200
    content = response.text

    # Verify Layout Elements
    assert "Jules Analysis Workbench" in content
    assert "id=\"main-pane\"" in content
    assert "id=\"sidebar\"" in content

    # Verify Risk Section
    assert "RISK ANALYSIS" in content
    assert "worst-case-box" in content
    assert "Greeks Table" in content or "greeks-table" in content

    # Verify Chat & Audit
    assert "Ask Jules" in content
    assert "toggleAudit" in content

    print("   Dashboard rendered successfully with all key components.")

    # 2. Test Ingestion Render
    print("2. Rendering Ingestion Hub...")
    response = client.get("/ingest")
    assert response.status_code == 200
    content = response.text

    assert "DATA_INGESTION_MODULE_V1" in content
    assert "drop-zone" in content

    print("   Ingestion Hub rendered successfully.")

    print("\nUI Verification Complete.")

if __name__ == "__main__":
    verify_ui_render()
