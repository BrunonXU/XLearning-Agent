"""
AI 对话端点

POST /api/chat      — SSE 流式输出（chunk / sources / questions / done / error）
POST /api/chat/sync — 普通 HTTP 降级端点（SSE 失败时使用）
"""

import asyncio
import json
import logging
from typing import List, Optional

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter(tags=["chat"])

MAX_HISTORY = 12  # 最多保留 12 条（6 轮）


class ChatRequest(BaseModel):
    planId: str
    message: str
    history: Optional[List[dict]] = None


def _truncate_history(history: List[dict]) -> List[dict]:
    """保留最近 MAX_HISTORY 条消息（6 轮）"""
    return history[-MAX_HISTORY:] if history else []


async def _generate_sse(plan_id: str, message: str, history: List[dict]):
    """SSE 生成器：逐 chunk 推送 TutorAgent 流式输出"""
    from backend.session_context import get_session

    logger.info(f"[chat] ▶ plan={plan_id!r} message={message[:80]!r} history_len={len(history)}")
    ctx = get_session(plan_id)
    truncated = _truncate_history(history)

    chunk_count = 0
    try:
        for chunk in ctx.tutor.stream_response(
            user_input=message,
            history=truncated,
        ):
            if chunk:
                chunk_count += 1
                data = json.dumps({"type": "chunk", "content": chunk}, ensure_ascii=False)
                yield f"data: {data}\n\n"
                await asyncio.sleep(0)  # 让出事件循环，保证 SSE 实时推送

        # 推送来源（TutorAgent 在 _current_sources 里记录）
        sources = ctx.tutor._current_sources
        if sources:
            src_payload = [
                {
                    "materialId": s.get("filename", s.get("source", "unknown")),
                    "materialName": s.get("filename", s.get("source", "来源")),
                    "snippet": s.get("section", s.get("query", "")),
                }
                for s in sources
            ]
            src_data = json.dumps({"type": "sources", "sources": src_payload}, ensure_ascii=False)
            yield f"data: {src_data}\n\n"

        # 异步生成建议问题（简单实现：基于最后一条 AI 回复）
        questions = _generate_suggested_questions(message)
        if questions:
            q_data = json.dumps({"type": "questions", "questions": questions}, ensure_ascii=False)
            yield f"data: {q_data}\n\n"

    except Exception as e:
        logger.error(f"[chat] ✗ plan={plan_id!r} error={e!r}")
        err_data = json.dumps({"type": "error", "message": str(e)}, ensure_ascii=False)
        yield f"data: {err_data}\n\n"

    finally:
        logger.info(f"[chat] ✓ plan={plan_id!r} chunks={chunk_count}")
        done_data = json.dumps({"type": "done", "chunkCount": chunk_count}, ensure_ascii=False)
        yield f"data: {done_data}\n\n"


def _generate_suggested_questions(user_message: str) -> List[str]:
    """
    简单的建议问题生成（Task 7.6 可接入 LLM 异步生成）。
    目前基于关键词启发式生成 3 个问题。
    """
    templates = [
        f"{user_message}的核心原理是什么？",
        f"能举一个{user_message}的实际应用例子吗？",
        f"{user_message}和相关概念有什么区别？",
    ]
    return templates[:3]


@router.post("/chat")
async def chat(body: ChatRequest):
    return StreamingResponse(
        _generate_sse(body.planId, body.message, body.history or []),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


@router.post("/chat/sync")
async def chat_sync(body: ChatRequest):
    """降级端点：普通 HTTP，返回完整回复"""
    from backend.session_context import get_session

    ctx = get_session(body.planId)
    truncated = _truncate_history(body.history or [])

    try:
        response = ctx.tutor.run(
            user_input=body.message,
            history=truncated,
        )
        return {"content": response, "type": "sync"}
    except Exception as e:
        logger.error(f"[chat sync] error: {e}")
        return {"content": "AI 暂时不可用，请稍后重试", "type": "error"}
