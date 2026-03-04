"""规划 CRUD 端点及子资源端点"""

import uuid
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend import database
from backend.session_context import clear_session

router = APIRouter(tags=["plans"])


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------

class PlanCreate(BaseModel):
    title: str
    description: Optional[str] = None


class PlanUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None


class PlanResponse(BaseModel):
    id: str
    title: str
    description: Optional[str]
    sourceCount: int
    lastAccessedAt: str
    coverColor: str
    totalDays: int
    completedDays: int
    createdAt: str


class ProgressCompleted(BaseModel):
    completed: bool


class ProgressTasks(BaseModel):
    tasks: list


# ---------------------------------------------------------------------------
# Plans CRUD
# ---------------------------------------------------------------------------

@router.get("/plans", response_model=List[PlanResponse])
async def list_plans():
    return database.get_all_plans()


@router.post("/plans", response_model=PlanResponse, status_code=201)
async def create_plan(body: PlanCreate):
    plan_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    plan = {
        "id": plan_id,
        "title": body.title,
        "description": body.description or "",
        "sourceCount": 0,
        "lastAccessedAt": now,
        "coverColor": "from-blue-400 to-indigo-600",
        "totalDays": 0,
        "completedDays": 0,
        "createdAt": now,
    }
    return database.create_plan(plan)


@router.put("/plans/{plan_id}", response_model=PlanResponse)
async def update_plan(plan_id: str, body: PlanUpdate):
    updates = {}
    if body.title is not None:
        updates["title"] = body.title
    if body.description is not None:
        updates["description"] = body.description
    updates["lastAccessedAt"] = datetime.now(timezone.utc).isoformat()
    result = database.update_plan(plan_id, updates)
    if result is None:
        raise HTTPException(status_code=404, detail="Plan not found")
    return result


@router.delete("/plans/{plan_id}", status_code=204)
async def delete_plan(plan_id: str):
    deleted = database.delete_plan(plan_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Plan not found")
    clear_session(plan_id)


# ---------------------------------------------------------------------------
# Messages sub-resource
# ---------------------------------------------------------------------------

@router.get("/plans/{plan_id}/messages")
async def get_plan_messages(plan_id: str):
    return database.get_messages(plan_id)


# ---------------------------------------------------------------------------
# Materials sub-resource
# ---------------------------------------------------------------------------

@router.get("/plans/{plan_id}/materials")
async def get_plan_materials(plan_id: str):
    return database.get_materials(plan_id)


# ---------------------------------------------------------------------------
# Progress sub-resource
# ---------------------------------------------------------------------------

@router.post("/plans/{plan_id}/progress")
async def save_progress(plan_id: str, body: List[dict]):
    database.upsert_progress(plan_id, body)
    return {"ok": True}


@router.get("/plans/{plan_id}/progress")
async def get_plan_progress(plan_id: str):
    return database.get_progress(plan_id)


@router.put("/plans/{plan_id}/progress/{day_number}")
async def update_day_completed(plan_id: str, day_number: int, body: ProgressCompleted):
    ok = database.update_progress_completed(plan_id, day_number, body.completed)
    if not ok:
        raise HTTPException(status_code=404, detail="Progress not found")
    return {"ok": True}


@router.put("/plans/{plan_id}/progress/{day_number}/tasks")
async def update_day_tasks(plan_id: str, day_number: int, body: ProgressTasks):
    ok = database.update_progress_tasks(plan_id, day_number, body.tasks)
    if not ok:
        raise HTTPException(status_code=404, detail="Progress not found")
    return {"ok": True}


# ---------------------------------------------------------------------------
# Notes sub-resource
# ---------------------------------------------------------------------------

@router.get("/plans/{plan_id}/notes")
async def get_plan_notes(plan_id: str):
    return database.get_notes(plan_id)


# ---------------------------------------------------------------------------
# Generated Contents sub-resource
# ---------------------------------------------------------------------------

@router.get("/plans/{plan_id}/generated-contents")
async def get_plan_generated_contents(plan_id: str):
    return database.get_generated_contents(plan_id)


@router.post("/plans/{plan_id}/generated-contents")
async def save_generated_content(plan_id: str, body: dict):
    body["planId"] = plan_id
    return database.insert_generated_content(body)


# ---------------------------------------------------------------------------
# Search History sub-resource
# ---------------------------------------------------------------------------

@router.get("/plans/{plan_id}/search-history")
async def get_plan_search_history(plan_id: str):
    return database.get_search_history(plan_id)


@router.post("/plans/{plan_id}/search-history")
async def save_search_history(plan_id: str, body: dict):
    body["planId"] = plan_id
    return database.insert_search_history(body)


@router.delete("/plans/{plan_id}/search-history", status_code=204)
async def clear_search_history(plan_id: str):
    database.delete_search_history(plan_id)
