"""
多源资源搜索专家模块

职责：
1. 封装 Bilibili、YouTube、Google、GitHub、小红书、微信公众号 六平台搜索能力
2. 统一返回 SearchResult 列表
3. 单个平台失败不影响其他平台（故障容错）
4. 总超时 10 秒

设计决策：
- 使用 httpx 做 HTTP 请求，与 RepoAnalyzer 保持一致
- 使用 concurrent.futures 并发搜索所有平台
- 每个平台搜索方法独立，单个平台失败返回空列表
"""

import logging
from typing import List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

import httpx

from src.core.models import SearchResult

logger = logging.getLogger(__name__)


class ResourceSearcher:
    """
    多源资源搜索专家（6平台）

    通过并发搜索 6 个平台获取学习资源。
    降级策略：单个平台失败 → 跳过该平台，返回其余平台结果。
    """

    PLATFORMS = ["bilibili", "youtube", "google", "github", "xiaohongshu", "wechat"]
    TIMEOUT = 10  # 秒，总超时

    def __init__(self):
        self._platform_methods = {
            "bilibili": self._search_bilibili,
            "youtube": self._search_youtube,
            "google": self._search_google,
            "github": self._search_github,
            "xiaohongshu": self._search_xiaohongshu,
            "wechat": self._search_wechat,
        }

    def _search_bilibili(self, query: str) -> List[SearchResult]:
        """
        搜索 Bilibili 视频资源

        使用 Bilibili 搜索 API 获取视频结果。
        """
        try:
            resp = httpx.get(
                "https://api.bilibili.com/x/web-interface/search/type",
                params={"keyword": query, "search_type": "video", "page": 1, "pagesize": 5},
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "Referer": "https://www.bilibili.com",
                },
                timeout=self.TIMEOUT / len(self.PLATFORMS),
            )
            resp.raise_for_status()
            data = resp.json()

            results = []
            items = data.get("data", {}).get("result", []) or []
            for item in items[:5]:
                title = item.get("title", "").replace("<em class=\"keyword\">", "").replace("</em>", "")
                bvid = item.get("bvid", "")
                results.append(SearchResult(
                    title=title,
                    url=f"https://www.bilibili.com/video/{bvid}" if bvid else item.get("arcurl", ""),
                    platform="bilibili",
                    type="video",
                    description=item.get("description", "")[:200],
                ))
            return results
        except Exception as e:
            logger.warning(f"[ResourceSearcher] Bilibili search failed: {e}")
            return []

    def _search_youtube(self, query: str) -> List[SearchResult]:
        """
        搜索 YouTube 视频资源

        使用 YouTube Data API v3（需要 API Key）。
        降级：无 API Key 时通过网页搜索 URL 构造结果。
        """
        try:
            import os
            api_key = os.getenv("YOUTUBE_API_KEY")
            if api_key:
                resp = httpx.get(
                    "https://www.googleapis.com/youtube/v3/search",
                    params={
                        "part": "snippet",
                        "q": query,
                        "type": "video",
                        "maxResults": 5,
                        "key": api_key,
                    },
                    timeout=self.TIMEOUT / len(self.PLATFORMS),
                )
                resp.raise_for_status()
                data = resp.json()

                results = []
                for item in data.get("items", []):
                    video_id = item.get("id", {}).get("videoId", "")
                    snippet = item.get("snippet", {})
                    results.append(SearchResult(
                        title=snippet.get("title", ""),
                        url=f"https://www.youtube.com/watch?v={video_id}",
                        platform="youtube",
                        type="video",
                        description=snippet.get("description", "")[:200],
                    ))
                return results

            # 降级：构造 YouTube 搜索链接
            from urllib.parse import quote_plus
            return [SearchResult(
                title=f"YouTube: {query}",
                url=f"https://www.youtube.com/results?search_query={quote_plus(query)}",
                platform="youtube",
                type="video",
                description=f"在 YouTube 上搜索「{query}」的相关视频",
            )]
        except Exception as e:
            logger.warning(f"[ResourceSearcher] YouTube search failed: {e}")
            return []

    def _search_google(self, query: str) -> List[SearchResult]:
        """
        搜索 Google 学习资源

        使用 Google Custom Search API（需要 API Key + CX）。
        降级：无 API Key 时构造 Google 搜索链接。
        """
        try:
            import os
            api_key = os.getenv("GOOGLE_API_KEY")
            cx = os.getenv("GOOGLE_CX")
            if api_key and cx:
                resp = httpx.get(
                    "https://www.googleapis.com/customsearch/v1",
                    params={
                        "key": api_key,
                        "cx": cx,
                        "q": f"{query} tutorial",
                        "num": 5,
                    },
                    timeout=self.TIMEOUT / len(self.PLATFORMS),
                )
                resp.raise_for_status()
                data = resp.json()

                results = []
                for item in data.get("items", []):
                    results.append(SearchResult(
                        title=item.get("title", ""),
                        url=item.get("link", ""),
                        platform="google",
                        type="article",
                        description=item.get("snippet", "")[:200],
                    ))
                return results

            # 降级：构造 Google 搜索链接
            from urllib.parse import quote_plus
            return [SearchResult(
                title=f"Google: {query} tutorial",
                url=f"https://www.google.com/search?q={quote_plus(query + ' tutorial')}",
                platform="google",
                type="article",
                description=f"在 Google 上搜索「{query}」的学习教程",
            )]
        except Exception as e:
            logger.warning(f"[ResourceSearcher] Google search failed: {e}")
            return []

    def _search_github(self, query: str) -> List[SearchResult]:
        """
        搜索 GitHub 仓库资源

        使用 GitHub Search API 搜索相关仓库。
        """
        try:
            import os
            headers = {"Accept": "application/vnd.github.v3+json"}
            token = os.getenv("GITHUB_TOKEN")
            if token:
                headers["Authorization"] = f"token {token}"

            resp = httpx.get(
                "https://api.github.com/search/repositories",
                params={"q": f"{query} tutorial", "sort": "stars", "per_page": 5},
                headers=headers,
                timeout=self.TIMEOUT / len(self.PLATFORMS),
            )
            resp.raise_for_status()
            data = resp.json()

            results = []
            for item in data.get("items", []):
                results.append(SearchResult(
                    title=item.get("full_name", ""),
                    url=item.get("html_url", ""),
                    platform="github",
                    type="repo",
                    description=item.get("description", "")[:200] if item.get("description") else "",
                ))
            return results
        except Exception as e:
            logger.warning(f"[ResourceSearcher] GitHub search failed: {e}")
            return []

    def _search_xiaohongshu(self, query: str) -> List[SearchResult]:
        """
        搜索小红书笔记资源

        通过小红书 Web 搜索接口获取笔记。
        降级：构造小红书搜索链接。
        返回 type 为 "note"。
        """
        try:
            from urllib.parse import quote_plus
            resp = httpx.get(
                "https://edith.xiaohongshu.com/api/sns/web/v1/search/notes",
                params={"keyword": query, "page": 1, "page_size": 5},
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "Origin": "https://www.xiaohongshu.com",
                    "Referer": "https://www.xiaohongshu.com/",
                },
                timeout=self.TIMEOUT / len(self.PLATFORMS),
            )
            resp.raise_for_status()
            data = resp.json()

            results = []
            items = data.get("data", {}).get("items", []) or []
            for item in items[:5]:
                note_card = item.get("note_card", {})
                note_id = item.get("id", "")
                results.append(SearchResult(
                    title=note_card.get("display_title", f"小红书笔记: {query}"),
                    url=f"https://www.xiaohongshu.com/explore/{note_id}" if note_id else "https://www.xiaohongshu.com",
                    platform="xiaohongshu",
                    type="note",
                    description=note_card.get("desc", "")[:200],
                ))
            if results:
                return results

            # API 未返回结果时，构造搜索链接
            return [SearchResult(
                title=f"小红书: {query}",
                url=f"https://www.xiaohongshu.com/search_result?keyword={quote_plus(query)}",
                platform="xiaohongshu",
                type="note",
                description=f"在小红书上搜索「{query}」的相关笔记",
            )]
        except Exception as e:
            logger.warning(f"[ResourceSearcher] Xiaohongshu search failed: {e}")
            # 降级：构造搜索链接
            try:
                from urllib.parse import quote_plus
                return [SearchResult(
                    title=f"小红书: {query}",
                    url=f"https://www.xiaohongshu.com/search_result?keyword={quote_plus(query)}",
                    platform="xiaohongshu",
                    type="note",
                    description=f"在小红书上搜索「{query}」的相关笔记",
                )]
            except Exception:
                return []

    def _search_wechat(self, query: str) -> List[SearchResult]:
        """
        搜索微信公众号文章

        通过搜狗微信搜索接口获取公众号文章。
        降级：构造搜狗微信搜索链接。
        返回 type 为 "article"。
        """
        try:
            from urllib.parse import quote_plus
            resp = httpx.get(
                "https://weixin.sogou.com/weixin",
                params={"type": 2, "query": query, "ie": "utf8"},
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "Referer": "https://weixin.sogou.com/",
                },
                timeout=self.TIMEOUT / len(self.PLATFORMS),
                follow_redirects=True,
            )
            resp.raise_for_status()
            html = resp.text

            # 简单解析搜狗微信搜索结果页面
            results = []
            import re
            # 匹配文章标题和链接
            articles = re.findall(
                r'<h3>.*?<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>',
                html,
                re.DOTALL,
            )
            for url, title_html in articles[:5]:
                # 清理 HTML 标签
                title = re.sub(r'<[^>]+>', '', title_html).strip()
                if title:
                    results.append(SearchResult(
                        title=title,
                        url=url if url.startswith("http") else f"https://weixin.sogou.com{url}",
                        platform="wechat",
                        type="article",
                        description=f"微信公众号文章：{title[:100]}",
                    ))
            if results:
                return results

            # 未解析到结果时，构造搜索链接
            return [SearchResult(
                title=f"微信公众号: {query}",
                url=f"https://weixin.sogou.com/weixin?type=2&query={quote_plus(query)}",
                platform="wechat",
                type="article",
                description=f"在搜狗微信搜索「{query}」的公众号文章",
            )]
        except Exception as e:
            logger.warning(f"[ResourceSearcher] WeChat search failed: {e}")
            # 降级：构造搜索链接
            try:
                from urllib.parse import quote_plus
                return [SearchResult(
                    title=f"微信公众号: {query}",
                    url=f"https://weixin.sogou.com/weixin?type=2&query={quote_plus(query)}",
                    platform="wechat",
                    type="article",
                    description=f"在搜狗微信搜索「{query}」的公众号文章",
                )]
            except Exception:
                return []

    def search(self, query: str, platforms: Optional[List[str]] = None) -> List[SearchResult]:
        """
        搜索学习资源（并发搜索，跳过失败平台）

        Args:
            query: 搜索关键词
            platforms: 指定平台列表，默认搜索全部 6 个平台

        Returns:
            SearchResult 列表（跳过失败平台，不抛异常）
        """
        if not query or not query.strip():
            return []

        target_platforms = platforms if platforms else self.PLATFORMS
        # 过滤无效平台名
        target_platforms = [p for p in target_platforms if p in self._platform_methods]

        if not target_platforms:
            return []

        all_results: List[SearchResult] = []

        try:
            with ThreadPoolExecutor(max_workers=len(target_platforms)) as executor:
                future_to_platform = {
                    executor.submit(self._platform_methods[platform], query): platform
                    for platform in target_platforms
                }

                for future in as_completed(future_to_platform, timeout=self.TIMEOUT):
                    platform = future_to_platform[future]
                    try:
                        results = future.result(timeout=0)
                        all_results.extend(results)
                        logger.info(f"[ResourceSearcher] {platform}: found {len(results)} results")
                    except Exception as e:
                        logger.warning(f"[ResourceSearcher] {platform} failed: {e}")
                        # 跳过失败平台，继续处理其他平台
        except TimeoutError:
            logger.warning("[ResourceSearcher] Overall search timed out, returning partial results")
        except Exception as e:
            logger.warning(f"[ResourceSearcher] Search execution error: {e}")

        return all_results
