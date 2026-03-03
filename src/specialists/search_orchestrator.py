"""
SearchOrchestrator - 搜索调度器

协调多平台并发搜索、缓存管理和结果聚合。
集成 BrowserAgent、QualityScorer、SearchCache。

核心流程：
1. 检查缓存 → 命中则直接返回
2. 启动浏览器 → 并发搜索各平台
3. 小红书特殊处理：全量搜索 + top_k 详情并行获取
4. QualityScorer 批量评分
5. 按 quality_score 降序排序 → 截断 top_k → 写入缓存
"""

import asyncio
import logging
from typing import List, Optional

from src.core.models import SearchResult
from src.specialists.browser_agent import BrowserAgent
from src.specialists.browser_models import RawSearchResult, ScoredResult
from src.specialists.platform_configs import PLATFORM_CONFIGS, PlatformConfig
from src.specialists.quality_scorer import QualityScorer
from src.specialists.search_cache import SearchCache
from src.specialists.bilibili_searcher import BiliBiliSearcher

logger = logging.getLogger(__name__)

# 广告关键词（标题降权用）
_AD_KEYWORDS = ["报班", "课程优惠", "限时", "折扣", "免费试听", "领取资料", "加群"]


def _xhs_composite_score(r: RawSearchResult) -> float:
    """小红书综合排序分：评论数×5 + 收藏数×2 + 点赞数×1"""
    m = r.engagement_metrics
    comments = _to_num(m.get("comments_count", 0))
    collected = _to_num(m.get("collected", 0))
    likes = _to_num(m.get("likes", 0))
    return comments * 5 + collected * 2 + likes


def _to_num(v) -> float:
    if v is None:
        return 0.0
    try:
        return float(v)
    except (ValueError, TypeError):
        return 0.0


def _is_ad_title(title: str) -> bool:
    """标题是否包含广告关键词。"""
    return any(kw in title for kw in _AD_KEYWORDS)


class SearchOrchestrator:
    """协调多平台搜索任务。

    - 并发搜索所有指定平台
    - 集成缓存、质量评分
    - 小红书平台使用特殊排序权重和并行详情获取
    """

    SEARCH_TIMEOUT = 60.0   # 搜索阶段超时（秒）
    DETAIL_TIMEOUT = 120.0  # 详情阶段超时（秒）
    DEFAULT_TOP_K = 10

    def __init__(self, cache_ttl: int = 3600, llm_provider=None):
        self._cache = SearchCache(ttl=cache_ttl)
        self._browser_agent = BrowserAgent()
        self._quality_scorer = QualityScorer(llm_provider=llm_provider)
        self._bilibili_searcher = BiliBiliSearcher()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def search_all_platforms(
        self,
        query: str,
        platforms: List[str],
        timeout: float = 60.0,
        top_k: int = 10,
        per_platform_limit: Optional[int] = None,
    ) -> List[SearchResult]:
        """并发搜索所有指定平台，聚合、评分、排序后返回。
        
        Args:
            query: 搜索关键词
            platforms: 平台列表
            timeout: 超时时间（秒）
            top_k: 最终返回结果数量
            per_platform_limit: 每平台搜索条数，None 则使用默认值 10
        """
        # 1. 检查缓存
        cached = self._cache.get(query, platforms)
        if cached is not None:
            logger.info(f"缓存命中: {query} ({len(cached)} 条)")
            return cached[:top_k]

        # 2. 过滤有效平台
        valid_platforms = [p for p in platforms if p in PLATFORM_CONFIGS]
        if not valid_platforms:
            logger.warning(f"无有效平台: {platforms}")
            return []

        # 确定每平台搜索条数
        limit = per_platform_limit if per_platform_limit is not None else 10

        all_raw: List[RawSearchResult] = []

        try:
            # 3. 并发搜索各平台
            tasks = []
            for p in valid_platforms:
                config = PLATFORM_CONFIGS[p]
                tasks.append(self._search_single_platform(query, config, limit))

            results_per_platform = await asyncio.gather(*tasks, return_exceptions=True)

            for i, result in enumerate(results_per_platform):
                platform_name = valid_platforms[i]
                if isinstance(result, Exception):
                    logger.warning(f"平台 {platform_name} 搜索失败: {result}")
                    continue
                if result:
                    all_raw.extend(result)
                    logger.info(f"{platform_name}: {len(result)} 条结果")

        except Exception as e:
            logger.error(f"搜索执行异常: {e}")

        if not all_raw:
            return []

        # 4. 质量评分
        try:
            scored = await self._quality_scorer.score_batch(all_raw)
        except Exception as e:
            logger.warning(f"质量评分失败: {e}")
            scored = [
                ScoredResult(raw=r, quality_score=0.0, recommendation_reason="")
                for r in all_raw
            ]

        # 5. 广告降权
        for s in scored:
            if _is_ad_title(s.raw.title):
                s.quality_score *= 0.3

        # 6. 排序 + 截断
        scored.sort(key=lambda s: s.quality_score, reverse=True)
        top_scored = scored[:top_k]

        # 7. 转换为 SearchResult
        final = [self._to_search_result(s) for s in top_scored]

        # 8. 写入缓存
        self._cache.set(query, platforms, final)

        return final

    def expand_keywords(self, query: str) -> List[str]:
        """[TODO: 未来实现] 使用 LLM 扩展搜索关键词。MVP 返回原始关键词。"""
        return [query]

    async def close(self) -> None:
        """关闭浏览器资源。"""
        await self._browser_agent.close()

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    async def _search_single_platform(
        self, query: str, config: PlatformConfig, limit: int = 10
    ) -> List[RawSearchResult]:
        """搜索单个平台，小红书平台额外获取详情。
        
        Args:
            query: 搜索关键词
            config: 平台配置
            limit: 搜索结果数量限制
        """
        try:
            # 使用 API 搜索的平台（如 bilibili）
            if config.use_api_search:
                if config.name == "bilibili":
                    return await self._bilibili_searcher.search(query, limit)
                else:
                    logger.warning(f"平台 {config.name} 配置了 use_api_search 但无对应搜索器")
                    return []
            
            # 确保浏览器已启动
            if self._browser_agent._browser is None:
                await self._browser_agent.launch(config)

            results = await self._browser_agent.search_platform(query, config)

            # 小红书：按综合分排序 + 并行获取 top 20 详情
            if config.name == "xiaohongshu" and results:
                results.sort(key=_xhs_composite_score, reverse=True)
                results = await self._browser_agent.fetch_details_parallel(
                    results, config, top_k=BrowserAgent.DETAIL_TOP_K
                )
                # 用去重评论数更新 engagement_metrics
                for note in results:
                    if note.top_comments:
                        unique_comments = self._deduplicate_comments(note.top_comments)
                        note.deduplicated_comment_count = len(unique_comments)
                        note.engagement_metrics["comments_count"] = len(unique_comments)

            return results

        except Exception as e:
            logger.error(f"搜索平台 {config.name} 失败: {e}")
            return []

    def _deduplicate_comments(self, comments: List[dict]) -> List[dict]:
        """使用前 30 字指纹去重评论。"""
        seen_fingerprints = set()
        unique = []
        for comment in comments:
            text = comment.get("text", "")
            fingerprint = text[:30] if text else ""
            if fingerprint and fingerprint not in seen_fingerprints:
                seen_fingerprints.add(fingerprint)
                unique.append(comment)
        return unique

    @staticmethod
    def _to_search_result(scored: ScoredResult) -> SearchResult:
        """将 ScoredResult 转换为 SearchResult。"""
        raw = scored.raw
        comments_preview = []
        if raw.top_comments:
            comments_preview = [
                c.get("text", "")[:200] for c in raw.top_comments[:5]
            ]
        elif raw.comments:
            comments_preview = [c[:200] for c in raw.comments[:5]]

        return SearchResult(
            title=raw.title,
            url=raw.url,
            platform=raw.platform,
            type=raw.resource_type,
            description=raw.description or raw.content_snippet[:200] if raw.content_snippet else raw.description,
            quality_score=scored.quality_score,
            recommendation_reason=scored.recommendation_reason,
            engagement_metrics=raw.engagement_metrics,
            comments_preview=comments_preview,
        )
