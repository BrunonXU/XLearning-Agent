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




class TestSearch:
    def test_search_returns_list(self):
        r = client.post("/api/search", json={"query": "Python tutorial"})
        assert r.status_code == 200
        assert isinstance(r.json(), list)


class TestStudio:
    def test_valid_type(self):
        r = client.post("/api/studio/study-guide", json={
            "planId": "test",
            "allDays": [],
            "currentDayNumber": None
        })
        assert r.status_code == 200
        data = r.json()
        assert data["type"] == "study-guide"

    def test_invalid_type(self):
        r = client.post("/api/studio/unknown-type", json={})
        assert r.status_code == 400


class TestNotes:
    def _create_plan(self):
        r = client.post("/api/plans", json={"title": "Notes Test Plan"})
        assert r.status_code == 201
        return r.json()["id"]

    def test_create_note(self):
        plan_id = self._create_plan()
        r = client.post("/api/notes", json={
            "planId": plan_id,
            "title": "My Note",
            "content": "# Hello"
        })
        assert r.status_code == 201
        data = r.json()
        assert data["title"] == "My Note"
        assert "createdAt" in data
        assert "updatedAt" in data
        return data["id"]

    def test_update_note(self):
        plan_id = self._create_plan()
        create_r = client.post("/api/notes", json={
            "planId": plan_id, "title": "Old", "content": "old"
        })
        note_id = create_r.json()["id"]
        r = client.put(f"/api/notes/{note_id}", json={"content": "new content"})
        assert r.status_code == 200
        assert r.json()["content"] == "new content"

    def test_update_nonexistent_note(self):
        r = client.put("/api/notes/nonexistent", json={"title": "x"})
        assert r.status_code == 404

    def test_delete_note(self):
        plan_id = self._create_plan()
        create_r = client.post("/api/notes", json={
            "planId": plan_id, "title": "Del", "content": "x"
        })
        note_id = create_r.json()["id"]
        r = client.delete(f"/api/notes/{note_id}")
        assert r.status_code == 204

    def test_delete_nonexistent_note(self):
        r = client.delete("/api/notes/nonexistent")
        assert r.status_code == 404


class TestPlanSubResources:
    """Tests for the new sub-resource endpoints under /api/plans/{plan_id}/..."""

    def _create_plan(self):
        r = client.post("/api/plans", json={"title": "Sub-resource Test Plan"})
        assert r.status_code == 201
        return r.json()["id"]

    def test_get_messages_empty(self):
        plan_id = self._create_plan()
        r = client.get(f"/api/plans/{plan_id}/messages")
        assert r.status_code == 200
        assert r.json() == []

    def test_get_materials_empty(self):
        plan_id = self._create_plan()
        r = client.get(f"/api/plans/{plan_id}/materials")
        assert r.status_code == 200
        assert r.json() == []

    def test_progress_crud(self):
        plan_id = self._create_plan()
        # POST progress
        days = [
            {"dayNumber": 1, "title": "Day 1", "completed": False, "tasks": []},
            {"dayNumber": 2, "title": "Day 2", "completed": False, "tasks": [{"id": "t1", "title": "Task 1", "completed": False}]},
        ]
        r = client.post(f"/api/plans/{plan_id}/progress", json=days)
        assert r.status_code == 200
        assert r.json()["ok"] is True

        # GET progress
        r = client.get(f"/api/plans/{plan_id}/progress")
        assert r.status_code == 200
        data = r.json()
        assert len(data) == 2
        assert data[0]["dayNumber"] == 1
        assert data[1]["dayNumber"] == 2

        # PUT completed
        r = client.put(f"/api/plans/{plan_id}/progress/1", json={"completed": True})
        assert r.status_code == 200
        assert r.json()["ok"] is True

        # PUT tasks
        new_tasks = [{"id": "t1", "title": "Task 1", "completed": True}]
        r = client.put(f"/api/plans/{plan_id}/progress/2/tasks", json={"tasks": new_tasks})
        assert r.status_code == 200
        assert r.json()["ok"] is True

    def test_progress_completed_not_found(self):
        plan_id = self._create_plan()
        r = client.put(f"/api/plans/{plan_id}/progress/999", json={"completed": True})
        assert r.status_code == 404

    def test_progress_tasks_not_found(self):
        plan_id = self._create_plan()
        r = client.put(f"/api/plans/{plan_id}/progress/999/tasks", json={"tasks": []})
        assert r.status_code == 404

    def test_get_notes_empty(self):
        plan_id = self._create_plan()
        r = client.get(f"/api/plans/{plan_id}/notes")
        assert r.status_code == 200
        assert r.json() == []

    def test_generated_contents_crud(self):
        plan_id = self._create_plan()
        # GET empty
        r = client.get(f"/api/plans/{plan_id}/generated-contents")
        assert r.status_code == 200
        assert r.json() == []

        # POST
        content = {
            "id": "gc-1",
            "type": "study-guide",
            "title": "Test Guide",
            "content": "# Guide content",
            "createdAt": "2024-01-01T00:00:00Z",
        }
        r = client.post(f"/api/plans/{plan_id}/generated-contents", json=content)
        assert r.status_code == 200
        assert r.json()["planId"] == plan_id

        # GET after insert
        r = client.get(f"/api/plans/{plan_id}/generated-contents")
        assert r.status_code == 200
        assert len(r.json()) == 1

    def test_search_history_crud(self):
        plan_id = self._create_plan()
        # GET empty
        r = client.get(f"/api/plans/{plan_id}/search-history")
        assert r.status_code == 200
        assert r.json() == []

        # POST
        entry = {
            "id": "sh-1",
            "query": "Python tutorial",
            "platforms": ["youtube"],
            "results": [{"id": "r1", "title": "Result 1", "url": "https://example.com"}],
            "resultCount": 1,
            "searchedAt": "2024-01-01T00:00:00Z",
        }
        r = client.post(f"/api/plans/{plan_id}/search-history", json=entry)
        assert r.status_code == 200
        data = r.json()
        assert data["planId"] == plan_id
        assert data["query"] == "Python tutorial"

        # GET after insert
        r = client.get(f"/api/plans/{plan_id}/search-history")
        assert r.status_code == 200
        assert len(r.json()) == 1

        # DELETE
        r = client.delete(f"/api/plans/{plan_id}/search-history")
        assert r.status_code == 204

        # GET after delete
        r = client.get(f"/api/plans/{plan_id}/search-history")
        assert r.status_code == 200
        assert r.json() == []
