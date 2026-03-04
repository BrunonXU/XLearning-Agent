"""
资源刷新端点

提供 POST /resource/refresh 端点，用于手动刷新某条搜索结果的详情信息
（正文、评论、图片 URL），并调用 QualityAssessor 重新评估质量。

使用全局 BrowserAgent 单例，避免每次刷新都重新启动浏览器和登录。
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend import database

logger = logging.getLogger(__name__)
router = APIRouter(tags=["resource"])

REFRESH_TIMEOUT = 90  # 刷新超时（秒）

# 全局 BrowserAgent 单例，刷新时复用
_global_browser_agent: Optional[Any] = None
_browser_lock: Optional[asyncio.Lock] = None


def _get_lock() -> asyncio.Lock:
    global _browser_lock
    if _browser_lock is None:
        _browser_lock = asyncio.Lock()
    return _browser_lock


class RefreshRequest(BaseModel):
    url: str
    platform: str
    materialId: Optional[str] = None


class RefreshResponse(BaseModel):
    content: str
    contentSummary: str
    comments: List[Dict[str, Any]]
    commentSummary: str
    imageUrls: List[str]
    engagementMetrics: Dict[str, Any]
    qualityScore: float
    recommendationReason: str
    topComments: List[str] = []


async def _get_browser_agent(config):
    """获取或创建全局 BrowserAgent 单例。"""
    global _global_browser_agent

    async with _get_lock():
        if _global_browser_agent is not None and _global_browser_agent._context is not None:
            return _global_browser_agent

        # 需要新建或重建
        from src.specialists.browser_agent import BrowserAgent
        if _global_browser_agent is not None:
            try:
                await _global_browser_agent.close()
            except Exception:
                pass

        agent = BrowserAgent()
        await agent.launch(config)
        _global_browser_agent = agent
        return agent


@router.post("/resource/refresh", response_model=RefreshResponse)
async def refresh_resource(body: RefreshRequest):
    """
    刷新单条资源详情。

    1. 复用全局浏览器实例（无需重新登录）
    2. 导航到目标 URL，提取正文、评论、图片
    3. 调用 QualityAssessor 重新评估质量
    4. 返回完整的刷新结果

    超时 90 秒返回 HTTP 408，URL 不可访问返回 HTTP 422。
    """
    from src.specialists.platform_configs import PLATFORM_CONFIGS

    config = PLATFORM_CONFIGS.get(body.platform)
    if config is None:
        raise HTTPException(status_code=422, detail=f"不支持的平台: {body.platform}")

    try:
        result = await asyncio.wait_for(
            _do_refresh(body, config),
            timeout=REFRESH_TIMEOUT,
        )
        # Persist extra_data to materials table if materialId is provided
        if body.materialId:
            try:
                database.update_material_extra_data(body.materialId, {
                    "contentSummary": result.contentSummary,
                    "commentSummary": result.commentSummary,
                    "imageUrls": result.imageUrls,
                    "topComments": result.topComments,
                    "engagementMetrics": result.engagementMetrics,
                    "qualityScore": result.qualityScore,
                    "recommendationReason": result.recommendationReason,
                })
            except Exception as e:
                logger.warning(f"[resource/refresh] Failed to persist extra_data: {e}")
        return result
    except asyncio.TimeoutError:
        raise HTTPException(status_code=408, detail="刷新超时，请稍后重试")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[resource/refresh] unexpected error: {e}")
        raise HTTPException(status_code=500, detail=f"刷新失败: {e}")


async def _do_refresh(body, config) -> RefreshResponse:
    """Execute the refresh logic."""
    from src.specialists.browser_models import RawSearchResult
    from src.specialists.quality_assessor import QualityAssessor

    # 1. 获取全局浏览器实例（复用已有的，不会重新登录）
    try:
        browser_agent = await _get_browser_agent(config)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"无法启动浏览器: {e}")

    # 2. Fetch detail
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

    # 3. Build RawSearchResult for QualityAssessor
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

    # 4. Assess quality (使用 LLM 生成信息整理)
    from src.providers.factory import ProviderFactory
    try:
        llm = ProviderFactory.create_llm()
    except Exception:
        llm = None
    assessor = QualityAssessor(llm_provider=llm)
    if content:
        scored_list = await assessor.assess_batch([(raw, content, top_comments)])
        scored = scored_list[0] if scored_list else await assessor.assess_single_fallback(raw)
    else:
        scored = await assessor.assess_single_fallback(raw)

    # 5. Build response
    # topComments: 纯文本评论列表，供前端 PreviewPopup 展示
    comments_text = [c.get("text", "")[:200] for c in top_comments[:5]]

    return RefreshResponse(
        content=content,
        contentSummary=scored.content_summary,
        comments=top_comments,
        commentSummary=scored.comment_summary,
        imageUrls=image_urls,
        engagementMetrics=engagement_metrics,
        qualityScore=round(scored.quality_score, 2),
        recommendationReason=scored.recommendation_reason,
        topComments=comments_text,
    )
