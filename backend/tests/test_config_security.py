import os
from fastapi.testclient import TestClient
from fastapi import FastAPI
from backend.web.api.config_routes import router

app = FastAPI()
app.include_router(router)

client = TestClient(app)

def test_unauthorized_config_update():
    # Attempt update without X-Admin-Token
    response = client.post("/api/config", json={"google_api_key": "fake_key"})
    # It should be rejected (500 if no ADMIN_TOKEN set, or 422 for missing header)
    assert response.status_code in (403, 422, 500)

def test_authorized_config_update(monkeypatch):
    # Set the expected ADMIN_TOKEN in the environment
    monkeypatch.setenv("ADMIN_TOKEN", "test_admin_token_123")

    # Attempt update with the correct token
    response = client.post(
        "/api/config",
        headers={"X-Admin-Token": "test_admin_token_123"},
        json={"google_api_key": "new_fake_key"}
    )

    assert response.status_code == 200
    assert os.environ["GOOGLE_API_KEY"] == "new_fake_key"

def test_wrong_token_config_update(monkeypatch):
    monkeypatch.setenv("ADMIN_TOKEN", "test_admin_token_123")

    response = client.post(
        "/api/config",
        headers={"X-Admin-Token": "wrong_token"},
        json={"google_api_key": "hacker_key"}
    )

    assert response.status_code == 403
