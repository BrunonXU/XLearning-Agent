"""会话恢复端点"""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter(tags=["session"])

# 内存存储（与 chat 路由共享）
from backend.store import get_session_store


class SessionResponse(BaseModel):
    planId: str
    messages: List[dict]
    materials: List[dict]


@router.get("/session/{plan_id}", response_model=SessionResponse)
async def get_session(plan_id: str):
    store = get_session_store(plan_id)
    return SessionResponse(
        planId=plan_id,
        messages=store.get("messages", []),
        materials=store.get("materials", []),
    )
