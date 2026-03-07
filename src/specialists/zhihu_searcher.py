"""
知乎搜索器

基于 MediaCrawler 签名算法，使用 Playwright 获取匿名 cookie + execjs 签名 + httpx 请求知乎 API。
不需要登录，通过访问知乎页面获取匿名 d_c0 cookie 即可搜索。
签名核心代码从 MediaCrawler 提取（libs/zhihu.js）。
"""

import asyncio
import json
import logging
import re
from pathlib import Path
from typing import Dict, List, Optional
from urllib.parse import urlencode

import httpx
from playwright.async_api import BrowserContext, Page, async_playwright

from src.specialists.browser_models import RawSearchResult

logger = logging.getLogger(__name__)

# 路径常量
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
STEALTH_JS = _PROJECT_ROOT / "scripts" / "MediaCrawler" / "libs" / "stealth.min.js"
ZHIHU_SIGN_JS = _PROJECT_ROOT / "scripts" / "MediaCrawler" / "libs" / "zhihu.js"
ZHIHU_URL = "https://www.zhihu.com"
ZHIHU_ZHUANLAN_URL = "https://zhuanlan.zhihu.com"
REQUEST_INTERVAL = 1.0  # 请求间隔（秒）

# 签名 JS 编译缓存
_SIGN_JS_COMPILED = None


def _get_sign_js():
    """懒加载并编译知乎签名 JS。"""
    global _SIGN_JS_COMPILED
    if _SIGN_JS_COMPILED is None:
        import execjs
        with open(ZHIHU_SIGN_JS, mode="r", encoding="utf-8-sig") as f:
            _SIGN_JS_COMPILED = execjs.compile(f.read())
    return _SIGN_JS_COMPILED


def _sign(url: str, cookies: str) -> Dict:
    """调用 zhihu.js 生成签名头。"""
    js = _get_sign_js()
    return js.call("get_sign", url, cookies)


def _extract_text_from_html(html: str) -> str:
    """简单的 HTML 标签清理，提取纯文本。"""
    if not html:
        return ""
    return re.sub(r"<[^>]+>", "", html).strip()


class ZhihuSearcher:
    """知乎搜索器（匿名模式，不需要登录）"""

    TIMEOUT = 15  # httpx 超时（秒）

    def __init__(self):
        self._browser_context: Optional[BrowserContext] = None
        self._page: Optional[Page] = None
        self._playwright = None
        self._pw_cm = None
        self._cookie_dict: Dict[str, str] = {}
        self._cookie_str: str = ""
        self._headers: Dict[str, str] = {}
        self._initialized = False

    async def search(self, query: str, limit: int = 10) -> List[RawSearchResult]:
        """搜索知乎内容，返回 RawSearchResult 列表。"""
        try:
            if not self._initialized:
                await self._init_browser()

            search_results = await self._search_api(query, limit)
            if not search_results:
                logger.warning("知乎搜索无结果")
                return self._fallback_result(query)

            # 串行获取评论（签名依赖 cookie，不能太快）
            results: List[RawSearchResult] = []
            for item in search_results[:limit]:
                try:
                    comments = await self._get_top_comments(
                        item["content_id"], item["content_type"], max_count=10
                    )
                    await asyncio.sleep(REQUEST_INTERVAL)
                    r = self._build_result(item, comments)
                    if r:
                        results.append(r)
                except Exception as e:
                    logger.warning(f"处理知乎内容失败 [{item.get('content_id', '')}]: {e}")

            logger.info(f"知乎搜索完成: {len(results)} 条结果")
            return results if results else self._fallback_result(query)
        except Exception as e:
            logger.error(f"知乎搜索异常: {e}")
            return self._fallback_result(query)

    # ---- 浏览器初始化（获取匿名 cookie）----

    async def _init_browser(self):
        """启动 Playwright，访问知乎获取匿名 d_c0 cookie。"""
        logger.info("初始化知乎签名环境（匿名模式）...")
        self._pw_cm = async_playwright()
        self._playwright = await self._pw_cm.start()

        self._browser_context = await self._playwright.chromium.launch_persistent_context(
            user_data_dir=str(_PROJECT_ROOT / "browser_data" / "zhihu"),
            headless=True,
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                       "(KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
        )
        if STEALTH_JS.exists():
            await self._browser_context.add_init_script(path=str(STEALTH_JS))

        self._page = await self._browser_context.new_page()
        # 先访问首页获取基础 cookie
        await self._page.goto(ZHIHU_URL, wait_until="domcontentloaded", timeout=30000)
        await self._page.wait_for_timeout(3000)

        # 知乎搜索 API 需要先访问搜索页才能拿到正确的 cookie（MediaCrawler 的经验）
        await self._page.goto(
            f"{ZHIHU_URL}/search?q=python&type=content",
            wait_until="domcontentloaded",
            timeout=30000,
        )
        await self._page.wait_for_timeout(3000)

        await self._refresh_cookies()

        d_c0 = self._cookie_dict.get("d_c0")
        logger.info(f"知乎 cookie 状态: d_c0={'有' if d_c0 else '无'}, 总 cookie 数={len(self._cookie_dict)}")
        if not d_c0:
            logger.warning("未获取到 d_c0 cookie，知乎搜索可能受限")

        self._build_base_headers()
        self._initialized = True
        logger.info("知乎签名环境就绪（匿名模式）")

    async def _refresh_cookies(self):
        """从浏览器上下文刷新 cookie。"""
        cookies = await self._browser_context.cookies()
        self._cookie_dict = {c["name"]: c["value"] for c in cookies}
        self._cookie_str = "; ".join(f"{c['name']}={c['value']}" for c in cookies)

    def _build_base_headers(self):
        """构建基础请求头。"""
        self._headers = {
            "accept": "*/*",
            "accept-language": "zh-CN,zh;q=0.9",
            "cookie": self._cookie_str,
            "referer": f"{ZHIHU_URL}/search?q=python&type=content",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                          "(KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
            "x-api-version": "3.0.91",
            "x-app-za": "OS=Web",
            "x-requested-with": "fetch",
            "x-zse-93": "101_3_3.0",
        }

    # ---- API 请求 ----

    async def _signed_get(self, uri: str, params: Optional[Dict] = None) -> Dict:
        """带签名的 GET 请求。"""
        final_uri = uri
        if params:
            final_uri += "?" + urlencode(params)

        # 生成签名
        sign_res = _sign(final_uri, self._cookie_str)
        headers = {**self._headers}
        headers["x-zst-81"] = sign_res.get("x-zst-81", "")
        headers["x-zse-96"] = sign_res.get("x-zse-96", "")

        logger.debug(f"知乎请求签名: d_c0={self._cookie_dict.get('d_c0', 'MISSING')[:20]}..., "
                     f"x-zse-96={headers.get('x-zse-96', '')[:30]}...")

        url = ZHIHU_URL + final_uri
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, headers=headers, timeout=self.TIMEOUT)

        if resp.status_code == 401:
            logger.warning(f"知乎 API 401，尝试刷新 cookie 重试...")
            await self._refresh_cookies()
            self._build_base_headers()
            # 重新签名
            sign_res = _sign(final_uri, self._cookie_str)
            headers = {**self._headers}
            headers["x-zst-81"] = sign_res.get("x-zst-81", "")
            headers["x-zse-96"] = sign_res.get("x-zse-96", "")
            async with httpx.AsyncClient() as client:
                resp = await client.get(url, headers=headers, timeout=self.TIMEOUT)

        if resp.status_code == 403:
            raise RuntimeError(f"知乎 API 403 Forbidden: {resp.text[:200]}")
        if resp.status_code == 404:
            return {}
        resp.raise_for_status()

        data = resp.json()
        if data.get("error"):
            raise RuntimeError(f"知乎 API 错误: {data['error'].get('message', '')}")
        return data

    async def _search_api(self, keyword: str, limit: int = 20) -> List[Dict]:
        """调用知乎搜索 API，返回解析后的内容列表。"""
        params = {
            "gk_version": "gz-gaokao",
            "t": "general",
            "q": keyword,
            "correction": 1,
            "offset": 0,
            "limit": min(limit, 20),
            "filter_fields": "",
            "lc_idx": 0,
            "show_all_topics": 0,
            "search_source": "Filter",
        }
        data = await self._signed_get("/api/v4/search_v3", params)
        if not data:
            return []

        search_items = data.get("data", [])
        # 只保留回答、文章、视频类型
        valid_types = {"search_result", "zvideo"}
        results = []
        for item in search_items:
            if item.get("type") not in valid_types:
                continue
            obj = item.get("object")
            if not obj:
                continue
            parsed = self._parse_content(obj)
            if parsed:
                results.append(parsed)

        return results

    def _parse_content(self, obj: Dict) -> Optional[Dict]:
        """解析搜索结果中的单个内容对象。"""
        content_type = obj.get("type", "")
        content_id = obj.get("id")
        if not content_id:
            return None

        title = _extract_text_from_html(obj.get("title", ""))
        if not title:
            title = _extract_text_from_html(obj.get("name", ""))
        if not title:
            return None

        # 构造 URL
        if content_type == "answer":
            question_id = obj.get("question", {}).get("id", "")
            url = f"{ZHIHU_URL}/question/{question_id}/answer/{content_id}"
        elif content_type == "article":
            url = f"{ZHIHU_ZHUANLAN_URL}/p/{content_id}"
        elif content_type == "zvideo":
            url = obj.get("video_url") or f"{ZHIHU_URL}/zvideo/{content_id}"
        else:
            url = f"{ZHIHU_URL}/question/{content_id}"

        # 提取描述/正文摘要
        desc = _extract_text_from_html(
            obj.get("description", "") or obj.get("excerpt", "") or obj.get("content", "")
        )

        voteup = self._safe_int(obj.get("voteup_count", 0))
        comment_count = self._safe_int(obj.get("comment_count", 0))

        return {
            "content_id": str(content_id),
            "content_type": content_type,
            "title": title,
            "url": url,
            "description": desc[:500] if desc else "",
            "content_snippet": desc[:1000] if desc else "",
            "voteup_count": voteup,
            "comment_count": comment_count,
            "author": obj.get("author", {}).get("name", ""),
        }

    async def _get_top_comments(
        self, content_id: str, content_type: str, max_count: int = 10
    ) -> List[Dict]:
        """获取内容的高赞评论。"""
        if content_type not in ("answer", "article", "zvideo"):
            return []
        try:
            uri = f"/api/v4/comment_v5/{content_type}s/{content_id}/root_comment"
            params = {"order": "score", "offset": "", "limit": max_count}
            data = await self._signed_get(uri, params)
            if not data:
                return []

            comments = []
            for c in data.get("data", []):
                if c.get("type") != "comment":
                    continue
                text = _extract_text_from_html(c.get("content", ""))
                if text:
                    comments.append({
                        "text": text,
                        "likes": self._safe_int(c.get("like_count", 0)),
                        "author": c.get("author", {}).get("member", {}).get("name", "")
                                  if isinstance(c.get("author"), dict) else "",
                    })
            return comments[:max_count]
        except Exception as e:
            logger.warning(f"获取知乎评论失败 [{content_id}]: {e}")
            return []

    # ---- 数据转换 ----

    def _build_result(self, item: Dict, comments: List[Dict]) -> Optional[RawSearchResult]:
        """将解析后的内容 + 评论转换为 RawSearchResult。"""
        try:
            comment_texts = [c["text"] for c in comments if c.get("text")]
            return RawSearchResult(
                title=item["title"],
                url=item["url"],
                platform="zhihu",
                resource_type="article",  # 知乎内容统一归为 article
                description=item.get("description", ""),
                content_snippet=item.get("content_snippet", ""),
                engagement_metrics={
                    "likes": item.get("voteup_count", 0),
                    "comments": item.get("comment_count", 0),
                },
                comments=comment_texts[:10],
                top_comments=comments[:10],
            )
        except Exception as e:
            logger.warning(f"构建知乎结果失败: {e}")
            return None

    @staticmethod
    def _safe_int(value) -> int:
        if value is None:
            return 0
        try:
            if isinstance(value, str):
                value = value.replace("万", "0000").replace("亿", "00000000").replace("+", "")
            return int(float(value))
        except (ValueError, TypeError):
            return 0

    def _fallback_result(self, query: str) -> List[RawSearchResult]:
        """降级结果：返回知乎搜索链接。"""
        from urllib.parse import quote
        search_url = f"{ZHIHU_URL}/search?type=content&q={quote(query)}"
        return [
            RawSearchResult(
                title=f"在知乎搜索「{query}」",
                url=search_url,
                platform="zhihu",
                resource_type="article",
                description="点击链接在知乎查看更多搜索结果",
                engagement_metrics={},
            )
        ]

    # ---- 资源清理 ----

    async def close(self):
        """关闭浏览器，释放资源。"""
        self._initialized = False
        try:
            if self._browser_context:
                await self._browser_context.close()
                self._browser_context = None
                self._page = None
        except Exception:
            pass
        try:
            if self._pw_cm:
                await self._pw_cm.__aexit__(None, None, None)
                self._playwright = None
                self._pw_cm = None
        except Exception:
            pass
