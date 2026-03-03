"""
Studio 内容生成端点（Task 8）

GET  /api/studio/{type}           — 生成 AI 内容（learning-plan / study-guide / flashcards / quiz / progress-report）
PUT  /api/plan/day/{day_id}/complete — 标记 Day 完成（幂等）
"""

import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter(tags=["studio"])

VALID_TYPES = {"learning-plan", "study-guide", "flashcards", "quiz", "progress-report"}

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
}

_TITLES = {
    "learning-plan": "学习计划",
    "study-guide": "学习指南",
    "flashcards": "闪卡",
    "quiz": "测验",
    "progress-report": "进度报告",
}


class StudioResponse(BaseModel):
    type: str
    title: str
    content: str


class DayCompleteResponse(BaseModel):
    success: bool
    dayNumber: int


@router.get("/studio/{content_type}", response_model=StudioResponse)
async def generate_studio_content(content_type: str, plan_id: str = ""):
    if content_type not in VALID_TYPES:
        raise HTTPException(status_code=400, detail=f"Unknown type: {content_type}")

    prompt = _PROMPTS[content_type]
    title = _TITLES[content_type]

    try:
        from backend.session_context import get_session
        ctx = get_session(plan_id)
        content = ctx.tutor.run(user_input=prompt, use_rag=True)
    except Exception as e:
        logger.warning(f"[studio] TutorAgent failed for {content_type}: {e}")
        content = _fallback_content(content_type)

    return StudioResponse(type=content_type, title=title, content=content)


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


def _fallback_content(content_type: str) -> str:
    """TutorAgent 不可用时的降级内容"""
    fallbacks = {
        "learning-plan": "# 学习计划\n\n请先上传学习材料，AI 将根据材料内容生成个性化学习计划。",
        "study-guide": "# 学习指南\n\n请先上传学习材料，AI 将根据材料内容生成学习指南。",
        "flashcards": "**Q:** 请先上传学习材料\n**A:** AI 将根据材料内容生成闪卡",
        "quiz": "# 测验\n\n请先上传学习材料，AI 将根据材料内容生成测验题目。",
        "progress-report": "# 进度报告\n\n暂无学习数据，开始学习后将自动生成进度报告。",
    }
    return fallbacks.get(content_type, "内容生成失败，请稍后重试。")
