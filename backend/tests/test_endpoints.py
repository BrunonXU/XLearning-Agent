"""
FastAPI 端点单元测试
"""

import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_health():
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


class TestPlans:
    def test_list_empty(self):
        r = client.get("/api/plans")
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_create_plan(self):
        r = client.post("/api/plans", json={"title": "Test Plan"})
        assert r.status_code == 201
        data = r.json()
        assert data["title"] == "Test Plan"
        assert "id" in data
        return data["id"]

    def test_update_plan(self):
        create_r = client.post("/api/plans", json={"title": "Old Title"})
        plan_id = create_r.json()["id"]
        r = client.put(f"/api/plans/{plan_id}", json={"title": "New Title"})
        assert r.status_code == 200
        assert r.json()["title"] == "New Title"

    def test_delete_plan(self):
        create_r = client.post("/api/plans", json={"title": "To Delete"})
        plan_id = create_r.json()["id"]
        r = client.delete(f"/api/plans/{plan_id}")
        assert r.status_code == 204

    def test_update_nonexistent(self):
        r = client.put("/api/plans/nonexistent", json={"title": "x"})
        assert r.status_code == 404

    def test_delete_nonexistent(self):
        r = client.delete("/api/plans/nonexistent")
        assert r.status_code == 404


class TestSession:
    def test_get_session(self):
        r = client.get("/api/session/test-plan-123")
        assert r.status_code == 200
        data = r.json()
        assert data["planId"] == "test-plan-123"
        assert "messages" in data
        assert "materials" in data


class TestSearch:
    def test_search_returns_list(self):
        r = client.post("/api/search", json={"query": "Python tutorial"})
        assert r.status_code == 200
        assert isinstance(r.json(), list)


class TestStudio:
    def test_valid_type(self):
        r = client.get("/api/studio/study-guide?plan_id=test")
        assert r.status_code == 200
        data = r.json()
        assert data["type"] == "study-guide"

    def test_invalid_type(self):
        r = client.get("/api/studio/unknown-type")
        assert r.status_code == 400


class TestNotes:
    def test_create_note(self):
        r = client.post("/api/notes", json={
            "planId": "plan-1",
            "title": "My Note",
            "content": "# Hello"
        })
        assert r.status_code == 201
        data = r.json()
        assert data["title"] == "My Note"
        return data["id"]

    def test_update_note(self):
        create_r = client.post("/api/notes", json={
            "planId": "plan-1", "title": "Old", "content": "old"
        })
        note_id = create_r.json()["id"]
        r = client.put(f"/api/notes/{note_id}", json={"content": "new content"})
        assert r.status_code == 200
        assert r.json()["content"] == "new content"

    def test_delete_note(self):
        create_r = client.post("/api/notes", json={
            "planId": "plan-1", "title": "Del", "content": "x"
        })
        note_id = create_r.json()["id"]
        r = client.delete(f"/api/notes/{note_id}")
        assert r.status_code == 204
