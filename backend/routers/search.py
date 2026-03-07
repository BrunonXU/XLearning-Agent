"""
资源搜索端点

集成 ResourceSearcher + QualityScorer，按 quality_score 降序排列。
支持每平台独立进度推送（SSE）。
"""

import asyncio
import logging
import uuid
from typing import Any, Dict, List, Literal, Optional

from fastapi import APIRouter
from fastapi.requests import Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter(tags=["search"])

VALID_PLATFORMS = {"bilibili", "youtube", "google", "github", "xiaohongshu", "zhihu"}


class SearchRequest(BaseModel):
    query: str
    platforms: Optional[List[str]] = None
    planId: Optional[str] = None


class SearchResultItem(BaseModel):
    id: str
    title: str
    url: str
    platform: str
    description: str
    qualityScore: float
    recommendationReason: str
    contentSummary: str = ""
    commentSummary: str = ""
    engagementMetrics: Dict[str, Any] = {}
    imageUrls: List[str] = []
    topComments: List[str] = []
    contentText: str = ""
    keyPoints: List[str] = []
    keyFacts: List[str] = []
    methodology: List[str] = []
    credibility: Dict[str, Any] = {}


class SearchProgressEvent(BaseModel):
    stage: Literal["searching", "filtering", "extracting", "evaluating", "done", "error"]
    message: str = ""
    platform: Optional[str] = None
    total: Optional[int] = None
    completed: Optional[int] = None
    results: Optional[List[SearchResultItem]] = None
    error: Optional[str] = None


@router.post("/search", response_model=List[SearchResultItem])
async def search_resources(body: SearchRequest):
    """
    同步搜索端点，返回按 quality_score 降序排列的结果列表。
    """
    if not body.query.strip():
        return []

    platforms = [p for p in (body.platforms or [])] if body.platforms else None

    try:
        from src.specialists.resource_searcher import ResourceSearcher
        searcher = ResourceSearcher()

        loop = asyncio.get_event_loop()
        results = await loop.run_in_executor(
            None,
            lambda: searcher.search(
                query=body.query,
                platforms=platforms,
                user_selected=bool(platforms),
            )
        )

        items = [
            SearchResultItem(
                id=str(uuid.uuid4()),
                title=r.title,
                url=r.url,
                platform=r.platform,
                description=r.description[:120] if r.description else "",
                qualityScore=round(r.quality_score, 2),
                recommendationReason=r.recommendation_reason,
            )
            for r in results
        ]
        items.sort(key=lambda x: x.qualityScore, reverse=True)
        return items

    except Exception as e:
        logger.error(f"[search] failed: {e}")
        return []


@router.post("/search/stream")
async def search_stream(body: SearchRequest, request: Request):
    """
    SSE 流式搜索端点，通过 SearchOrchestrator 五阶段漏斗推送进度。
    """
    cancel_event = asyncio.Event()

    async def _generate():
        orchestrator = None
        try:
            if not body.query.strip():
                evt = SearchProgressEvent(stage="done", results=[])
                yield f"data: {evt.model_dump_json()}\n\n"
                return

            platforms = [p for p in (body.platforms or list(VALID_PLATFORMS)) if p in VALID_PLATFORMS]
            if not platforms:
                evt = SearchProgressEvent(stage="error", message="无有效搜索平台")
                yield f"data: {evt.model_dump_json()}\n\n"
                return

            from src.specialists.search_orchestrator import SearchOrchestrator
            from src.providers.factory import ProviderFactory
            try:
                llm = ProviderFactory.create_llm()
            except Exception as e:
                logger.warning(f"LLM provider 创建失败，关键词翻译将不可用: {e}")
                llm = None
            orchestrator = SearchOrchestrator(llm_provider=llm)

            try:
                async for event in orchestrator.search_all_platforms_stream(
                    query=body.query,
                    platforms=platforms,
                    cancel_event=cancel_event,
                ):
                    if await request.is_disconnected():
                        cancel_event.set()
                        break

                    if cancel_event.is_set():
                        break

                    stage = event.get("stage", "")

                    if stage == "done":
                        raw_results = event.get("results", [])
                        items = [
                            _to_search_result_item(r) for r in raw_results
                        ]
                        progress = SearchProgressEvent(stage="done", results=items)
                        yield f"data: {progress.model_dump_json()}\n\n"
                    else:
                        progress = SearchProgressEvent(
                            stage=stage,
                            message=event.get("message", ""),
                            platform=event.get("platform"),
                            total=event.get("total"),
                            completed=event.get("completed"),
                            error=event.get("message") if stage == "error" else None,
                        )
                        yield f"data: {progress.model_dump_json()}\n\n"
            except Exception as e:
                logger.error(f"[search/stream] error: {e}")
                try:
                    err_evt = SearchProgressEvent(stage="error", message=str(e))
                    yield f"data: {err_evt.model_dump_json()}\n\n"
                except Exception:
                    pass
        except (asyncio.CancelledError, ConnectionError, Exception) as e:
            # 客户端断开连接（abort）时，yield 会抛出异常，静默处理
            logger.info(f"[search/stream] client disconnected: {type(e).__name__}")
        finally:
            cancel_event.set()
            if orchestrator:
                try:
                    await orchestrator.close()
                except Exception as e:
                    # Windows 上关闭 Playwright 子进程可能触发 pipe 错误，静默处理
                    logger.debug(f"[search/stream] orchestrator close error (safe to ignore): {e}")

    return StreamingResponse(
        _generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


def _to_search_result_item(result_dict: dict) -> SearchResultItem:
    """Convert a SearchResult dict (from orchestrator) to a SearchResultItem for SSE."""
    return SearchResultItem(
        id=result_dict.get("id") or str(uuid.uuid4()),
        title=result_dict.get("title", ""),
        url=result_dict.get("url", ""),
        platform=result_dict.get("platform", ""),
        description=(result_dict.get("description", "") or "")[:120],
        qualityScore=round(result_dict.get("quality_score", 0.0), 2),
        recommendationReason=result_dict.get("recommendation_reason", ""),
        contentSummary=result_dict.get("content_summary", ""),
        commentSummary=result_dict.get("comment_summary", ""),
        engagementMetrics=result_dict.get("engagement_metrics", {}),
        imageUrls=result_dict.get("image_urls", []),
        topComments=result_dict.get("comments_preview", []),
        contentText=result_dict.get("content_text", ""),
        keyPoints=result_dict.get("key_points", []),
        keyFacts=result_dict.get("key_facts", []),
        methodology=result_dict.get("methodology", []),
        credibility=result_dict.get("credibility", {}),
    )
