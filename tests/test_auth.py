from fastapi.testclient import TestClient


def test_register_creates_user(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/register",
        json={"email": "new@example.com", "full_name": "New User", "password": "password123"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "new@example.com"
    assert "hashed_password" not in body


def test_register_rejects_duplicate_email(client: TestClient) -> None:
    payload = {"email": "dup@example.com", "full_name": "Dup", "password": "password123"}
    client.post("/api/v1/auth/register", json=payload)
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 409


def test_register_validates_password_length(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/register",
        json={"email": "short@example.com", "full_name": "Short", "password": "123"},
    )
    assert response.status_code == 422


def test_login_with_wrong_password_fails(client: TestClient) -> None:
    client.post(
        "/api/v1/auth/register",
        json={"email": "a@example.com", "full_name": "A User", "password": "password123"},
    )
    response = client.post(
        "/api/v1/auth/login", data={"username": "a@example.com", "password": "wrong-pass"}
    )
    assert response.status_code == 401


def test_me_returns_current_user(client: TestClient, auth_headers: dict[str, str]) -> None:
    response = client.get("/api/v1/auth/me", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["email"] == "ana@example.com"


def test_me_requires_token(client: TestClient) -> None:
    assert client.get("/api/v1/auth/me").status_code == 401
    bad = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer invalid"})
    assert bad.status_code == 401
