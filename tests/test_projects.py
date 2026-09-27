from fastapi.testclient import TestClient

from tests.conftest import register_and_login


def test_create_and_list_projects(client: TestClient, auth_headers: dict[str, str]) -> None:
    for name in ("Website", "Mobile app", "Web API"):
        response = client.post("/api/v1/projects", json={"name": name}, headers=auth_headers)
        assert response.status_code == 201

    response = client.get("/api/v1/projects", params={"search": "web"}, headers=auth_headers)
    body = response.json()
    assert body["total"] == 2
    assert {p["name"] for p in body["items"]} == {"Website", "Web API"}


def test_pagination(client: TestClient, auth_headers: dict[str, str]) -> None:
    for i in range(5):
        client.post("/api/v1/projects", json={"name": f"P{i}"}, headers=auth_headers)
    body = client.get("/api/v1/projects?page=2&size=2", headers=auth_headers).json()
    assert body["total"] == 5
    assert body["pages"] == 3
    assert len(body["items"]) == 2


def test_update_and_delete_project(client: TestClient, auth_headers: dict[str, str]) -> None:
    project = client.post("/api/v1/projects", json={"name": "Old"}, headers=auth_headers).json()
    updated = client.patch(
        f"/api/v1/projects/{project['id']}", json={"name": "New"}, headers=auth_headers
    )
    assert updated.json()["name"] == "New"
    assert (
        client.delete(f"/api/v1/projects/{project['id']}", headers=auth_headers).status_code == 204
    )
    assert client.get(f"/api/v1/projects/{project['id']}", headers=auth_headers).status_code == 404


def test_users_cannot_access_other_users_projects(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    project = client.post("/api/v1/projects", json={"name": "Mine"}, headers=auth_headers).json()
    other = register_and_login(client, "other@example.com")
    assert client.get(f"/api/v1/projects/{project['id']}", headers=other).status_code == 404
    assert client.get("/api/v1/projects", headers=other).json()["total"] == 0
