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
from typing import AsyncGenerator, List, Optional

from src.core.models import SearchResult
from src.specialists.browser_agent import BrowserAgent
from src.specialists.browser_models import RawSearchResult, ScoredResult
from src.specialists.engagement_ranker import EngagementRanker
from src.specialists.pipeline_executor import PipelineExecutor
from src.specialists.platform_configs import PLATFORM_CONFIGS, PlatformConfig
from src.specialists.quality_assessor import QualityAssessor
from src.specialists.quality_scorer import QualityScorer
from src.specialists.resource_collector import ResourceCollector
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
        # 搜索体验重设计：两阶段漏斗筛选 + 流水线执行
        self._engagement_ranker = EngagementRanker()
        self._quality_assessor = QualityAssessor(llm_provider=llm_provider)
        self._resource_collector = ResourceCollector()

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
            await self.close()
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

        # 9. 关闭浏览器释放资源
        await self.close()

        return final

    async def search_all_platforms_stream(
        self,
        query: str,
        platforms: List[str],
        top_k: int = 10,
        per_platform_limit: Optional[int] = None,
        cancel_event: Optional[asyncio.Event] = None,
    ) -> AsyncGenerator[dict, None]:
        """
        流式搜索：通过 yield 推送各阶段进度事件。

        Events:
        - {"stage": "searching", "message": "正在搜索小红书...", "platform": "xiaohongshu"}
        - {"stage": "filtering", "message": "已获取 N 条，正在初筛...", "total": N}
        - {"stage": "extracting", "message": "正在提取详情（3/15）...", "completed": 3, "total": 15}
        - {"stage": "evaluating", "message": "AI 正在评估内容质量..."}
        - {"stage": "done", "results": [...]}
        - {"stage": "error", "message": "..."}

        Flow:
        1. Check cache → hit: yield done directly
        2. Concurrent search all platforms → yield searching progress
        3. EngagementRanker filter → yield filtering
        4. PipelineExecutor extract+assess → yield extracting/evaluating
        5. Sort top_k → write cache → yield done

        Args:
            query: 搜索关键词
            platforms: 平台列表
            top_k: 最终返回结果数量
            per_platform_limit: 每平台搜索条数，None 则使用默认值 10
            cancel_event: 取消信号，设置后中断所有进行中的任务
        """
        PLATFORM_TIMEOUT = 45.0  # 单平台超时（秒）

        _cancel = cancel_event or asyncio.Event()

        # ---- 1. 检查缓存 ----
        cached = self._cache.get(query, platforms)
        if cached is not None:
            logger.info(f"缓存命中: {query} ({len(cached)} 条)")
            yield {
                "stage": "done",
                "results": [r.to_dict() for r in cached[:top_k]],
            }
            return

        # ---- 2. 过滤有效平台 ----
        valid_platforms = [p for p in platforms if p in PLATFORM_CONFIGS]
        if not valid_platforms:
            logger.warning(f"无有效平台: {platforms}")
            yield {"stage": "error", "message": "无有效搜索平台"}
            return

        limit = per_platform_limit if per_platform_limit is not None else 10

        # ---- 3. 并发搜索各平台 ----
        all_raw: List[RawSearchResult] = []
        errors: List[str] = []

        for p in valid_platforms:
            if _cancel.is_set():
                await self.close()
                return
            yield {
                "stage": "searching",
                "message": f"正在搜索{PLATFORM_CONFIGS[p].name}...",
                "platform": p,
            }

        async def _search_with_timeout(platform_name: str) -> List[RawSearchResult]:
            config = PLATFORM_CONFIGS[platform_name]
            return await asyncio.wait_for(
                self._search_single_platform(query, config, limit),
                timeout=PLATFORM_TIMEOUT,
            )

        tasks = [_search_with_timeout(p) for p in valid_platforms]
        results_per_platform = await asyncio.gather(*tasks, return_exceptions=True)

        for i, result in enumerate(results_per_platform):
            platform_name = valid_platforms[i]
            if isinstance(result, Exception):
                err_msg = f"平台 {platform_name} 搜索失败: {result}"
                logger.warning(err_msg)
                errors.append(err_msg)
                continue
            if result:
                all_raw.extend(result)
                logger.info(f"{platform_name}: {len(result)} 条结果")

        if not all_raw:
            await self.close()
            error_detail = "；".join(errors) if errors else "所有平台均无结果"
            yield {"stage": "error", "message": f"搜索失败: {error_detail}"}
            return

        if _cancel.is_set():
            await self.close()
            return

        # ---- 4. EngagementRanker 初筛 ----
        yield {
            "stage": "filtering",
            "message": f"已获取 {len(all_raw)} 条，正在初筛...",
            "total": len(all_raw),
        }

        candidates = self._engagement_ranker.rank(all_raw)
        total_candidates = len(candidates)

        if _cancel.is_set():
            await self.close()
            return

        # ---- 5. PipelineExecutor 提取 + 评估 ----
        pipeline = PipelineExecutor(
            browser_agent=self._browser_agent,
            resource_collector=self._resource_collector,
            quality_assessor=self._quality_assessor,
            cancel_event=_cancel,
        )

        # We need to yield extracting events during pipeline execution.
        # Use a shared list to collect progress events, then yield after pipeline.
        extract_events: List[dict] = []

        async def _progress_callback(completed: int, total: int) -> None:
            extract_events.append({
                "stage": "extracting",
                "message": f"正在提取详情（{completed}/{total}）...",
                "completed": completed,
                "total": total,
            })

        yield {
            "stage": "extracting",
            "message": f"正在提取详情（0/{total_candidates}）...",
            "completed": 0,
            "total": total_candidates,
        }

        scored_results: List[ScoredResult] = []
        try:
            scored_results = await pipeline.execute(
                candidates, progress_callback=_progress_callback
            )
        except Exception as e:
            logger.error(f"流水线执行异常: {e}")

        # Yield accumulated extracting progress events
        for evt in extract_events:
            if _cancel.is_set():
                await self.close()
                return
            yield evt

        # ---- 6. 关闭浏览器（提取完成后，LLM 评估前）----
        await self.close()

        if _cancel.is_set():
            return

        # ---- 7. 处理评估结果 ----
        if not scored_results:
            # LLM 整体失败降级：使用互动数据排序结果（需求 5.9）
            logger.warning("流水线无结果，使用互动数据排序降级")
            scored_results = [
                ScoredResult(raw=r, quality_score=0.0, recommendation_reason="")
                for r in candidates
            ]

        yield {
            "stage": "evaluating",
            "message": "AI 正在评估内容质量...",
        }

        # ---- 8. 排序取 top_k ----
        scored_results.sort(key=lambda s: s.quality_score, reverse=True)
        top_scored = scored_results[:top_k]

        # ---- 9. 转换为 SearchResult ----
        final = [self._to_search_result_extended(s) for s in top_scored]

        # ---- 10. 写入缓存 ----
        self._cache.set(query, platforms, final)

        # ---- 11. yield done ----
        yield {
            "stage": "done",
            "results": [r.to_dict() for r in final],
        }

    @staticmethod
    def _to_search_result_extended(scored: ScoredResult) -> SearchResult:
        """将 ScoredResult（含摘要字段）转换为 SearchResult。"""
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
            description=(
                raw.description
                or (raw.content_snippet[:200] if raw.content_snippet else "")
            ),
            quality_score=scored.quality_score,
            recommendation_reason=scored.recommendation_reason,
            engagement_metrics=raw.engagement_metrics,
            comments_preview=comments_preview,
            content_summary=scored.content_summary,
            comment_summary=scored.comment_summary,
            image_urls=list(raw.image_urls) if raw.image_urls else [],
        )

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
                # launch 失败时 _browser 仍为 None
                if self._browser_agent._browser is None:
                    logger.error(f"浏览器启动失败，无法搜索 {config.name}")
                    return []

            results = await self._browser_agent.search_platform(query, config)

            # 小红书：按综合分排序（跳过详情页获取，加快搜索速度）
            if config.name == "xiaohongshu" and results:
                results.sort(key=_xhs_composite_score, reverse=True)
                results = results[:limit]  # 只保留 top N

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
