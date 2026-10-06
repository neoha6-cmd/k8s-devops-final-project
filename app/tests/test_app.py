import pytest

from app import Task, create_app, db


@pytest.fixture
def client():
    app = create_app(
        {"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:"}
    )
    with app.app_context():
        db.create_all()
        yield app.test_client()
        db.session.remove()
        db.drop_all()


def test_default_priority_is_medium(client):
    resp = client.post("/api/tasks", json={"title": "Write docs"})
    assert resp.status_code == 201
    assert resp.get_json()["priority"] == "medium"


def test_create_task_with_high_priority(client):
    resp = client.post("/api/tasks", json={"title": "Fix bug", "priority": "high"})
    assert resp.get_json()["priority"] == "high"
    assert Task.query.count() == 1


def test_invalid_priority_is_rejected(client):
    resp = client.post("/api/tasks", json={"title": "x", "priority": "urgent"})
    assert resp.status_code == 400
    assert Task.query.count() == 0


def test_list_returns_priority_field(client):
    client.post("/api/tasks", json={"title": "a", "priority": "low"})
    data = client.get("/api/tasks").get_json()
    assert data[0]["priority"] == "low"


def test_health_and_ready(client):
    assert client.get("/health").status_code == 200
    assert client.get("/ready").status_code == 200
