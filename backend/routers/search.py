"""
资源搜索端点

集成 ResourceSearcher + QualityScorer，按 quality_score 降序排列。
支持每平台独立进度推送（SSE）。
"""

import asyncio
import json
import logging
import uuid
from typing import List, Optional

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter(tags=["search"])

VALID_PLATFORMS = {"bilibili", "youtube", "google", "github", "xiaohongshu"}


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

        # ResourceSearcher.search 是同步的，在线程池中运行避免阻塞事件循环
        loop = asyncio.get_event_loop()
        results = await loop.run_in_executor(
            None,
            lambda: searcher.search(
                query=body.query,
                platforms=platforms,
                user_selected=bool(platforms),
            )
        )

        # 转换为前端格式，按 quality_score 降序
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
async def search_stream(body: SearchRequest):
    """
    SSE 流式搜索端点，逐平台推送进度和结果。
    事件格式：
      data: {"type": "platform_start", "platform": "bilibili"}
      data: {"type": "platform_done", "platform": "bilibili", "count": 3}
      data: {"type": "results", "items": [...]}
      data: {"type": "done"}
    """
    async def _generate():
        platforms = body.platforms or list(VALID_PLATFORMS)
        all_results: List[SearchResultItem] = []

        for platform in platforms:
            start_evt = json.dumps({"type": "platform_start", "platform": platform}, ensure_ascii=False)
            yield f"data: {start_evt}\n\n"
            await asyncio.sleep(0)

            try:
                from src.specialists.resource_searcher import ResourceSearcher
                searcher = ResourceSearcher()
                loop = asyncio.get_event_loop()
                results = await asyncio.wait_for(
                    loop.run_in_executor(
                        None,
                        lambda p=platform: searcher.search(
                            query=body.query,
                            platforms=[p],
                            user_selected=True,
                        )
                    ),
                    timeout=15.0,
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
                all_results.extend(items)
                done_evt = json.dumps(
                    {"type": "platform_done", "platform": platform, "count": len(items)},
                    ensure_ascii=False,
                )
                yield f"data: {done_evt}\n\n"

            except asyncio.TimeoutError:
                timeout_evt = json.dumps(
                    {"type": "platform_timeout", "platform": platform},
                    ensure_ascii=False,
                )
                yield f"data: {timeout_evt}\n\n"
            except Exception as e:
                err_evt = json.dumps(
                    {"type": "platform_error", "platform": platform, "message": str(e)},
                    ensure_ascii=False,
                )
                yield f"data: {err_evt}\n\n"

        # 最终结果按 quality_score 降序
        all_results.sort(key=lambda x: x.qualityScore, reverse=True)
        results_evt = json.dumps(
            {"type": "results", "items": [r.model_dump() for r in all_results]},
            ensure_ascii=False,
        )
        yield f"data: {results_evt}\n\n"
        yield f"data: {json.dumps({'type': 'done'})}\n\n"

    return StreamingResponse(
        _generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
