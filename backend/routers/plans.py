"""规划 CRUD 端点"""

import uuid
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(tags=["plans"])

# 内存存储（后续可替换为数据库）
_plans: dict = {}


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


@router.get("/plans", response_model=List[PlanResponse])
async def list_plans():
    return list(_plans.values())


@router.post("/plans", response_model=PlanResponse, status_code=201)
async def create_plan(body: PlanCreate):
    plan_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat() + "Z"
    plan = PlanResponse(
        id=plan_id,
        title=body.title,
        description=body.description,
        sourceCount=0,
        lastAccessedAt=now,
        coverColor="from-blue-400 to-indigo-600",
        totalDays=0,
        completedDays=0,
        createdAt=now,
    )
    _plans[plan_id] = plan.model_dump()
    return plan


@router.put("/plans/{plan_id}", response_model=PlanResponse)
async def update_plan(plan_id: str, body: PlanUpdate):
    if plan_id not in _plans:
        raise HTTPException(status_code=404, detail="Plan not found")
    plan = _plans[plan_id]
    if body.title is not None:
        plan["title"] = body.title
    if body.description is not None:
        plan["description"] = body.description
    plan["lastAccessedAt"] = datetime.utcnow().isoformat() + "Z"
    return plan


@router.delete("/plans/{plan_id}", status_code=204)
async def delete_plan(plan_id: str):
    if plan_id not in _plans:
        raise HTTPException(status_code=404, detail="Plan not found")
    del _plans[plan_id]
    from backend.session_context import clear_session
    clear_session(plan_id)
