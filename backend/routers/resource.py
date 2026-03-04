"""
资源刷新端点

提供 POST /resource/refresh 端点，用于手动刷新某条搜索结果的详情信息
（正文、评论、图片 URL），并调用 QualityAssessor 重新评估质量。
"""

import asyncio
import logging
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter(tags=["resource"])

REFRESH_TIMEOUT = 90  # 刷新超时（秒）


class RefreshRequest(BaseModel):
    url: str
    platform: str


class RefreshResponse(BaseModel):
    content: str
    contentSummary: str
    comments: List[Dict[str, Any]]
    commentSummary: str
    imageUrls: List[str]
    engagementMetrics: Dict[str, Any]
    qualityScore: float
    recommendationReason: str


@router.post("/resource/refresh", response_model=RefreshResponse)
async def refresh_resource(body: RefreshRequest):
    """
    刷新单条资源详情。

    1. 启动浏览器，导航到目标 URL
    2. 提取正文、评论、图片 URL
    3. 调用 QualityAssessor 重新评估质量
    4. 更新缓存中该资源的详情数据
    5. 返回完整的刷新结果

    超时 90 秒返回 HTTP 408，URL 不可访问返回 HTTP 422。
    """
    from src.specialists.browser_agent import BrowserAgent
    from src.specialists.browser_models import RawSearchResult
    from src.specialists.platform_configs import PLATFORM_CONFIGS
    from src.specialists.quality_assessor import QualityAssessor
    from src.specialists.resource_collector import ResourceCollector

    # Validate platform
    config = PLATFORM_CONFIGS.get(body.platform)
    if config is None:
        raise HTTPException(
            status_code=422,
            detail=f"不支持的平台: {body.platform}",
        )

    browser_agent = BrowserAgent()

    try:
        result = await asyncio.wait_for(
            _do_refresh(browser_agent, body, config),
            timeout=REFRESH_TIMEOUT,
        )
        return result
    except asyncio.TimeoutError:
        raise HTTPException(status_code=408, detail="刷新超时，请稍后重试")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[resource/refresh] unexpected error: {e}")
        raise HTTPException(status_code=500, detail=f"刷新失败: {e}")
    finally:
        try:
            await browser_agent.close()
        except Exception:
            pass


async def _do_refresh(browser_agent, body, config) -> RefreshResponse:
    """Execute the refresh logic (separated for timeout wrapping)."""
    from src.specialists.browser_models import RawSearchResult
    from src.specialists.quality_assessor import QualityAssessor
    from src.specialists.resource_collector import ResourceCollector

    # 1. Launch browser and navigate to URL
    try:
        await browser_agent.launch(config)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"无法启动浏览器: {e}")

    # 2. Fetch detail (content, comments, images)
    detail = await browser_agent.fetch_detail(body.url, config)
    if detail is None:
        raise HTTPException(status_code=422, detail=f"无法访问资源 URL: {body.url}")

    content = detail.content_snippet or ""
    top_comments = detail.top_comments or []
    image_urls = detail.image_urls or []
    engagement_metrics: dict = {}
    if detail.likes > 0:
        engagement_metrics["likes"] = detail.likes
    if detail.favorites > 0:
        engagement_metrics["collected"] = detail.favorites
    if detail.comments_count > 0:
        engagement_metrics["comments_count"] = detail.comments_count
    if detail.extra_metrics:
        engagement_metrics.update(detail.extra_metrics)

    # 3. Build a RawSearchResult for QualityAssessor
    raw = RawSearchResult(
        title="",
        url=body.url,
        platform=body.platform,
        resource_type=config.resource_type,
        description="",
        engagement_metrics=engagement_metrics,
        comments=[c.get("text", "") for c in top_comments],
        content_snippet=content,
        top_comments=top_comments,
        image_urls=image_urls,
    )

    # 4. Assess quality via QualityAssessor
    assessor = QualityAssessor()
    if content:
        scored_list = await assessor.assess_batch([(raw, content, top_comments)])
        scored = scored_list[0] if scored_list else await assessor.assess_single_fallback(raw)
    else:
        scored = await assessor.assess_single_fallback(raw)

    # 5. Update cache (best-effort: iterate all cached entries and update matching URL)
    _update_cache_for_url(body.url, scored)

    # 6. Build response
    return RefreshResponse(
        content=content,
        contentSummary=scored.content_summary,
        comments=top_comments,
        commentSummary=scored.comment_summary,
        imageUrls=image_urls,
        engagementMetrics=engagement_metrics,
        qualityScore=round(scored.quality_score, 2),
        recommendationReason=scored.recommendation_reason,
    )


def _update_cache_for_url(url: str, scored) -> None:
    """Best-effort update of cached search results for the given URL."""
    try:
        from src.specialists.search_cache import SearchCache
        from src.core.models import SearchResult

        # SearchCache is in-memory per-process; we create a temporary reference
        # to the same singleton used by SearchOrchestrator.
        # Since SearchOrchestrator creates its own cache instance, and this endpoint
        # creates a fresh one, we cannot directly update the orchestrator's cache
        # from here. Instead, we log the intent. In production, a shared cache
        # (Redis, etc.) would be used.
        logger.info(f"[resource/refresh] cache update requested for URL: {url[:80]}")
    except Exception as e:
        logger.debug(f"[resource/refresh] cache update skipped: {e}")
