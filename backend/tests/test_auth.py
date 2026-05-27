from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_login_success():
    resp = client.post("/api/auth/login", json={"username": "admin", "password": "admin"})
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["user"]["username"] == "admin"


def test_login_wrong_password():
    resp = client.post("/api/auth/login", json={"username": "admin", "password": "wrong"})
    assert resp.status_code == 401


def test_me_without_token():
    resp = client.get("/api/auth/me")
    assert resp.status_code == 403


def test_me_with_token():
    login_resp = client.post("/api/auth/login", json={"username": "admin", "password": "admin"})
    token = login_resp.json()["access_token"]
    resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["username"] == "admin"
