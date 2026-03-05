"""
Studio 内容生成端点

POST /api/studio/{type}           — 生成 AI 内容（learning-plan / study-guide / flashcards / quiz / progress-report / mind-map / day-summary）
PUT  /api/plan/day/{day_id}/complete — 标记 Day 完成（幂等）
"""

from __future__ import annotations

import logging
import time
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend import database
from backend.prompt_builder import PromptBuilder
from backend.session_context import get_session

logger = logging.getLogger(__name__)
router = APIRouter(tags=["studio"])

VALID_TYPES = {"learning-plan", "study-guide", "flashcards", "quiz", "progress-report", "mind-map", "day-summary"}

# 各类型对应的生成提示词
_PROMPTS = {
    "learning-plan": (
        "请根据已上传的学习材料，生成一份结构化的学习计划。"
        "包含：总体目标、每日学习主题（3-7天）、每天的具体任务（视频/阅读/练习）。"
        "用 Markdown 格式输出，包含清晰的标题层级。"
    ),
    "study-guide": (
        "请根据已上传的学习材料，生成一份全面的学习指南。"
        "包含：核心概念总结、重要知识点、学习路径建议、常见问题解答。"
        "用 Markdown 格式输出。"
    ),
    "flashcards": (
        "请根据已上传的学习材料，生成 10-15 张闪卡（问答对）。"
        "格式：每张卡片用 '**Q:** 问题\\n**A:** 答案' 格式，用 '---' 分隔。"
        "覆盖核心概念、定义、原理等关键知识点。"
    ),
    "quiz": (
        "请根据已上传的学习材料，生成一份包含 5-8 道题的测验。"
        "包含：单选题、判断题、简答题各若干道。"
        "每题附上正确答案和解析。用 Markdown 格式输出。"
    ),
    "progress-report": (
        "请根据当前学习进度，生成一份学习进度报告。"
        "包含：已完成内容、掌握程度评估、薄弱环节分析、下一步建议。"
        "用 Markdown 格式输出。"
    ),
    "mind-map": (
        "请根据已上传的学习材料，生成一份思维导图结构。"
        "使用 Markdown 标题层级格式（#/##/###），适合渲染为思维导图。"
        "按学习天数组织知识结构。"
    ),
    "day-summary": (
        "请根据今日学习内容，生成一份知识总结。"
        "包含：知识回顾、与之前知识的关联分析、复习建议、明日预告。"
        "用 Markdown 格式输出。"
    ),
}

_TITLES = {
    "learning-plan": "学习计划",
    "study-guide": "学习指南",
    "flashcards": "闪卡",
    "quiz": "测验",
    "progress-report": "进度报告",
    "mind-map": "思维导图",
    "day-summary": "今日总结",
}


class LearnerProfileRequest(BaseModel):
    """学习者画像"""
    goal: str = ""
    duration: str = ""
    level: str = ""
    background: str = ""
    dailyHours: str = ""


class StudioRequest(BaseModel):
    """HTTP request body for Studio content generation.
    Also serves as the LearningContext for PromptBuilder."""
    planId: str = ""
    allDays: list[dict] = []
    currentDayNumber: Optional[int] = None
    learnerProfile: Optional[LearnerProfileRequest] = None


# Alias for clarity when used as internal context by PromptBuilder
LearningContext = StudioRequest


class StudioResponse(BaseModel):
    type: str
    title: str
    content: str
    createdAt: str


class DayCompleteResponse(BaseModel):
    success: bool
    dayNumber: int


@router.post("/studio/{content_type}", response_model=StudioResponse)
async def generate_studio_content(content_type: str, body: StudioRequest):
    if content_type not in VALID_TYPES:
        raise HTTPException(status_code=400, detail=f"Unknown type: {content_type}")

    title = _TITLES[content_type]
    t_start = time.perf_counter()
    status = "ok"

    try:
        ctx = get_session(body.planId)
        # Load learner profile: prefer request body, fallback to DB
        learner_profile = body.learnerProfile
        if not learner_profile and body.planId:
            profile_data = database.get_learner_profile(body.planId)
            if profile_data:
                learner_profile = LearnerProfileRequest(
                    goal=profile_data.get("goal", ""),
                    duration=profile_data.get("duration", ""),
                    level=profile_data.get("level", ""),
                    background=profile_data.get("background", ""),
                    dailyHours=profile_data.get("dailyHours", ""),
                )
        learning_context = LearningContext(
            planId=body.planId,
            allDays=body.allDays,
            currentDayNumber=body.currentDayNumber,
            learnerProfile=learner_profile,
        )
        builder = PromptBuilder(rag_engine=ctx.tutor.rag_engine)
        user_prompt, system_prompt = builder.build(content_type, learning_context)
        content = ctx.tutor.generate(user_prompt, system_prompt=system_prompt)
    except Exception as e:
        logger.warning(f"[studio] Generation failed for {content_type}: {e}")
        content = _fallback_content(content_type)
        user_prompt = ""
        status = "error"

    duration_ms = round((time.perf_counter() - t_start) * 1000, 1)
    now = datetime.now(timezone.utc).isoformat()

    # Record trace for DEV panel
    try:
        from backend.routers.dev import record_trace
        record_trace({
            "id": str(uuid.uuid4()),
            "type": "tool",
            "name": f"Studio.{content_type}",
            "startTime": now,
            "duration": duration_ms,
            "status": status,
            "input": (user_prompt[:200] if user_prompt else ""),
            "output": content[:200],
            "tokens": {"prompt": 0, "completion": 0, "total": 0},
            "metadata": {"planId": body.planId, "contentType": content_type},
        })
    except Exception:
        pass

    # Persist generated content to database
    if body.planId:
        content_id = str(uuid.uuid4())
        try:
            database.insert_generated_content({
                "id": content_id,
                "planId": body.planId,
                "type": content_type,
                "title": title,
                "content": content,
                "createdAt": now,
            })
        except Exception as e:
            logger.warning(f"[studio] Failed to persist generated content: {e}")

    return StudioResponse(type=content_type, title=title, content=content, createdAt=now)


@router.put("/plan/day/{day_id}/complete", response_model=DayCompleteResponse)
async def complete_day(day_id: int, plan_id: str = ""):
    """标记 Day 完成（幂等）"""
    try:
        from backend.session_context import get_session
        ctx = get_session(plan_id)
        ctx.progress.mark_day_completed(day_id)
    except Exception as e:
        logger.warning(f"[studio] ProgressTracker.mark_day_completed failed: {e}")
        # 幂等：即使后端失败，前端状态已更新，返回成功
    return DayCompleteResponse(success=True, dayNumber=day_id)


async def generate_studio_content_internal(content_type: str, plan_id: str) -> dict:
    """Internal function for chat-triggered Studio content generation.

    Reuses PromptBuilder logic without HTTP request/response overhead.
    Called from chat.py when IntentDetector detects a Studio trigger.

    Returns:
        dict with type, title, content, createdAt (empty dict if invalid type)
    """
    if content_type not in VALID_TYPES:
        return {}

    ctx = get_session(plan_id)
    # Load learner profile from DB for internal calls
    profile_data = database.get_learner_profile(plan_id)
    learner_profile = None
    if profile_data:
        learner_profile = LearnerProfileRequest(
            goal=profile_data.get("goal", ""),
            duration=profile_data.get("duration", ""),
            level=profile_data.get("level", ""),
            background=profile_data.get("background", ""),
            dailyHours=profile_data.get("dailyHours", ""),
        )
    learning_context = LearningContext(planId=plan_id, learnerProfile=learner_profile)
    builder = PromptBuilder(rag_engine=ctx.tutor.rag_engine)
    title = _TITLES.get(content_type, content_type)

    try:
        user_prompt, system_prompt = builder.build(content_type, learning_context)
        content = ctx.tutor.generate(user_prompt, system_prompt=system_prompt)
    except Exception as e:
        logger.warning(f"[studio] Internal generation failed for {content_type}: {e}")
        content = _fallback_content(content_type)

    now = datetime.now(timezone.utc).isoformat()

    # Persist
    if plan_id:
        try:
            database.insert_generated_content({
                "id": str(uuid.uuid4()),
                "planId": plan_id,
                "type": content_type,
                "title": title,
                "content": content,
                "createdAt": now,
            })
        except Exception:
            pass

    return {"type": content_type, "title": title, "content": content, "createdAt": now}


# ---------------------------------------------------------------------------
# Learner Profile endpoints
# ---------------------------------------------------------------------------

class LearnerProfileResponse(BaseModel):
    planId: str
    goal: str = ""
    duration: str = ""
    level: str = ""
    background: str = ""
    dailyHours: str = ""


@router.get("/learner-profile/{plan_id}", response_model=LearnerProfileResponse)
async def get_learner_profile(plan_id: str):
    """获取学习者画像"""
    profile = database.get_learner_profile(plan_id)
    if not profile:
        return LearnerProfileResponse(planId=plan_id)
    return LearnerProfileResponse(
        planId=plan_id,
        goal=profile.get("goal", ""),
        duration=profile.get("duration", ""),
        level=profile.get("level", ""),
        background=profile.get("background", ""),
        dailyHours=profile.get("dailyHours", ""),
    )


@router.put("/learner-profile/{plan_id}", response_model=LearnerProfileResponse)
async def save_learner_profile(plan_id: str, body: LearnerProfileRequest):
    """保存/更新学习者画像"""
    profile_id = str(uuid.uuid4())
    database.upsert_learner_profile({
        "id": profile_id,
        "planId": plan_id,
        "goal": body.goal,
        "duration": body.duration,
        "level": body.level,
        "background": body.background,
        "dailyHours": body.dailyHours,
    })
    return LearnerProfileResponse(
        planId=plan_id,
        goal=body.goal,
        duration=body.duration,
        level=body.level,
        background=body.background,
        dailyHours=body.dailyHours,
    )


def _fallback_content(content_type: str) -> str:
    """TutorAgent 不可用时的降级内容"""
    fallbacks = {
        "learning-plan": "# 学习计划\n\n请先上传学习材料，AI 将根据材料内容生成个性化学习计划。",
        "study-guide": "# 学习指南\n\n请先上传学习材料，AI 将根据材料内容生成学习指南。",
        "flashcards": "**Q:** 请先上传学习材料\n**A:** AI 将根据材料内容生成闪卡",
        "quiz": "# 测验\n\n请先上传学习材料，AI 将根据材料内容生成测验题目。",
        "progress-report": "# 进度报告\n\n暂无学习数据，开始学习后将自动生成进度报告。",
        "mind-map": "# 思维导图\n\n请先上传学习材料，AI 将根据材料内容生成思维导图。",
        "day-summary": "# 今日总结\n\n暂无今日学习数据，完成学习任务后将自动生成总结。",
    }
    return fallbacks.get(content_type, "内容生成失败，请稍后重试。")
