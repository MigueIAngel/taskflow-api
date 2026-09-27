from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def project_id(client: TestClient, auth_headers: dict[str, str]) -> int:
    return client.post("/api/v1/projects", json={"name": "Demo"}, headers=auth_headers).json()["id"]


def test_task_crud(client: TestClient, auth_headers: dict[str, str], project_id: int) -> None:
    url = f"/api/v1/projects/{project_id}/tasks"
    created = client.post(url, json={"title": "Write docs"}, headers=auth_headers)
    assert created.status_code == 201
    task = created.json()
    assert task["status"] == "todo"
    assert task["priority"] == "medium"

    patched = client.patch(f"{url}/{task['id']}", json={"status": "done"}, headers=auth_headers)
    assert patched.json()["status"] == "done"

    assert client.delete(f"{url}/{task['id']}", headers=auth_headers).status_code == 204
    assert client.get(f"{url}/{task['id']}", headers=auth_headers).status_code == 404


def test_filter_and_sort_tasks(
    client: TestClient, auth_headers: dict[str, str], project_id: int
) -> None:
    url = f"/api/v1/projects/{project_id}/tasks"
    client.post(url, json={"title": "B task", "priority": "high"}, headers=auth_headers)
    client.post(url, json={"title": "A task", "priority": "low"}, headers=auth_headers)
    client.post(
        url, json={"title": "C task", "priority": "high", "status": "done"}, headers=auth_headers
    )

    high = client.get(url, params={"priority": "high"}, headers=auth_headers).json()
    assert high["total"] == 2

    done = client.get(url, params={"status": "done"}, headers=auth_headers).json()
    assert [t["title"] for t in done["items"]] == ["C task"]

    by_title = client.get(url, params={"sort": "title", "order": "asc"}, headers=auth_headers)
    assert [t["title"] for t in by_title.json()["items"]] == ["A task", "B task", "C task"]


def test_project_stats(client: TestClient, auth_headers: dict[str, str], project_id: int) -> None:
    url = f"/api/v1/projects/{project_id}/tasks"
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    client.post(url, json={"title": "Late", "due_date": yesterday}, headers=auth_headers)
    client.post(url, json={"title": "Doing", "status": "in_progress"}, headers=auth_headers)
    client.post(url, json={"title": "Done", "status": "done"}, headers=auth_headers)
    client.post(url, json={"title": "Done 2", "status": "done"}, headers=auth_headers)

    stats = client.get(f"/api/v1/projects/{project_id}/stats", headers=auth_headers).json()
    assert stats == {
        "total": 4,
        "todo": 1,
        "in_progress": 1,
        "done": 2,
        "overdue": 1,
        "completion_rate": 0.5,
    }
