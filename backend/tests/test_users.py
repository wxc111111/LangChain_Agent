from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def _login():
    resp = client.post("/api/auth/login", json={"username": "admin", "password": "admin"})
    return resp.json()["access_token"]


def test_create_user():
    token = _login()
    resp = client.post(
        "/api/users",
        json={"username": "test_user_1", "password": "123456", "role": "user"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["username"] == "test_user_1"


def test_create_duplicate_user():
    token = _login()
    resp = client.post(
        "/api/users",
        json={"username": "test_user_1", "password": "123456", "role": "user"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 400


def test_list_users():
    token = _login()
    resp = client.get("/api/users", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert "total" in data
    assert "items" in data


def test_get_user_detail():
    token = _login()
    resp = client.get("/api/users/1", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["id"] == 1


def test_non_admin_cannot_create_user():
    token = _login()
    client.post(
        "/api/users",
        json={"username": "normal_user", "password": "123456", "role": "user"},
        headers={"Authorization": f"Bearer {token}"},
    )
    resp = client.post("/api/auth/login", json={"username": "normal_user", "password": "123456"})
    user_token = resp.json()["access_token"]
    resp = client.post(
        "/api/users",
        json={"username": "another", "password": "123456", "role": "user"},
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert resp.status_code == 403
