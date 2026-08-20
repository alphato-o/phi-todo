from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_stats():
    with client:
        r = client.get("/api/stats")
        assert r.status_code == 200


def test_create_task():
    with client:
        r = client.post("/api/tasks", json={"title": "test task"})
        assert r.status_code == 201
        assert r.json()["title"] == "test task"
