"""
BrowserAgent - 基于 Playwright 的浏览器代理

管理 Playwright 浏览器实例，执行页面操作，支持 API 响应拦截。
基于 POC (scripts/poc_xhs_parallel.py) 的验证结果实现。

核心功能：
- 启动带反检测配置的 Chromium 浏览器
- 混合模式搜索（浏览器 + API 响应拦截）
- 并行详情页获取（asyncio.Semaphore 控制并发）
- Cookie 持久化与登录状态管理
- 三级回退正文提取（API JSON → __INITIAL_STATE__ → DOM）
"""

import asyncio
import json
import logging
import random
import re
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import quote

from src.specialists.browser_models import RawSearchResult, ResourceDetail
from src.specialists.platform_configs import PlatformConfig
from src.specialists.resource_collector import ResourceCollector

logger = logging.getLogger(__name__)

# User-Agent 池
_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 Safari/17.2",
]


def _random_delay() -> float:
    """生成 [1.0, 3.0] 秒的随机延迟值。"""
    return random.uniform(BrowserAgent.MIN_DELAY, BrowserAgent.MAX_DELAY)



class BrowserAgent:
    """基于 Playwright 的浏览器代理，支持混合模式（浏览器 + API 拦截）。

    混合模式用 Playwright 浏览器执行搜索（浏览器自带签名），
    通过 page.on("response") 拦截 API 响应获取结构化 JSON 数据。
    """

    PAGE_TIMEOUT = 15_000  # 页面加载超时（毫秒）
    MIN_DELAY = 1.0  # 最小操作间隔（秒）
    MAX_DELAY = 3.0  # 最大操作间隔（秒）
    MIN_PLATFORM_INTERVAL = 2.0  # 同平台最小请求间隔（秒）
    DETAIL_MAX_RETRIES = 2  # 详情页最大重试次数
    DETAIL_CONCURRENCY = 3  # 详情页并行获取的最大 tab 数
    SEARCH_FULL_COUNT = 60  # 搜索全量获取数（滚动加载）
    DETAIL_TOP_K = 20  # 获取详情的 top K 条结果
    SCROLL_COUNT = 6  # 搜索页滚动次数
    SCROLL_PX = 800  # 每次滚动像素
    DETAIL_SCROLL_COUNT = 3  # 详情页滚动次数（触发评论加载）
    DETAIL_SCROLL_PX = 500  # 详情页每次滚动像素

    def __init__(self) -> None:
        self._playwright: Any = None
        self._browser: Any = None
        self._context: Any = None
        # 拦截到的搜索 API 响应
        self._intercepted_search: List[dict] = []
        # note_id → 评论列表
        self._intercepted_comments: Dict[str, List[dict]] = {}
        # note_id → 详情数据
        self._intercepted_details: Dict[str, dict] = {}
        # 捕获的签名 headers
        self._captured_headers: Dict[str, str] = {}
        # 同平台上次请求时间戳
        self._last_platform_request: Dict[str, float] = {}
        # 评论锁（懒加载，避免在无事件循环的线程中初始化失败）
        self._comment_lock: Optional[asyncio.Lock] = None

    def _get_comment_lock(self) -> asyncio.Lock:
        """懒加载评论锁，确保在有事件循环的上下文中创建。"""
        if self._comment_lock is None:
            self._comment_lock = asyncio.Lock()
        return self._comment_lock

    # ------------------------------------------------------------------
    # launch / close
    # ------------------------------------------------------------------

    async def launch(self, config: PlatformConfig) -> None:
        """启动浏览器实例（带反检测配置），如需登录则加载 Cookie。"""
        try:
            from playwright.async_api import async_playwright

            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(
                headless=False,
                args=["--disable-blink-features=AutomationControlled"],
            )

            user_agent = random.choice(_USER_AGENTS)
            self._context = await self._browser.new_context(
                viewport={"width": 1280, "height": 900},
                user_agent=user_agent,
                locale="zh-CN",
            )

            # 反检测：覆盖 webdriver 属性
            await self._context.add_init_script(
                "Object.defineProperty(navigator,'webdriver',{get:()=>undefined})"
            )

            # 加载 Cookie
            if config.requires_login and config.cookie_file:
                cookie_path = Path(config.cookie_file)
                if cookie_path.exists():
                    cookies = json.loads(cookie_path.read_text(encoding="utf-8"))
                    await self._context.add_cookies(cookies)
                    logger.info(f"已加载 {len(cookies)} 条 Cookie ({config.name})")
                else:
                    logger.warning(f"Cookie 文件不存在: {config.cookie_file}")

            logger.info(f"浏览器已启动 (UA: {user_agent[:50]}...)")
        except Exception as e:
            logger.error(f"浏览器启动失败: {e}")
            self._browser = None
            self._context = None

    async def close(self) -> None:
        """关闭浏览器实例，保存 Cookie，释放资源。"""
        try:
            if self._context:
                # 保存 Cookie（遍历所有已知的 cookie_file 配置）
                try:
                    cookies = await self._context.cookies()
                    if cookies:
                        # 保存到默认位置（小红书）
                        cookie_path = Path("scripts/.xhs_cookies.json")
                        cookie_path.write_text(
                            json.dumps(cookies, ensure_ascii=False, indent=2),
                            encoding="utf-8",
                        )
                        logger.info(f"已保存 {len(cookies)} 条 Cookie")
                except Exception as e:
                    logger.debug(f"保存 Cookie 失败: {e}")

            if self._browser:
                await self._browser.close()
            if self._playwright:
                await self._playwright.stop()
        except Exception as e:
            logger.error(f"关闭浏览器失败: {e}")
        finally:
            self._browser = None
            self._context = None
            self._playwright = None

    # ------------------------------------------------------------------
    # API interception callbacks
    # ------------------------------------------------------------------

    async def _intercept_response(self, response: Any) -> None:
        """API 响应拦截回调，提取搜索结果、详情和评论的 JSON 数据。"""
        url = response.url
        try:
            if "/api/sns/web/v1/search/notes" in url and response.status == 200:
                data = await response.json()
                if data.get("success") or data.get("code") == 0:
                    items = data.get("data", {}).get("items", [])
                    self._intercepted_search.extend(items)
                    logger.debug(f"[拦截] 搜索: +{len(items)} 条 (累计 {len(self._intercepted_search)})")

            elif "/api/sns/web/v2/comment/page" in url and response.status == 200:
                data = await response.json()
                if data.get("success") or data.get("code") == 0:
                    comments = data.get("data", {}).get("comments", [])
                    m = re.search(r"note_id=([a-f0-9]+)", url)
                    if m:
                        nid = m.group(1)
                        async with self._get_comment_lock():
                            self._intercepted_comments[nid] = comments
                        logger.debug(f"[拦截] 评论 {nid}: {len(comments)} 条")

            elif "/api/sns/web/v1/feed" in url and response.status == 200:
                data = await response.json()
                if data.get("success") or data.get("code") == 0:
                    feed_items = data.get("data", {}).get("items", [])
                    for fi in feed_items:
                        nid = fi.get("id", "")
                        if nid:
                            self._intercepted_details[nid] = fi
                            logger.debug(f"[拦截] 详情 {nid}")
        except Exception:
            pass

    async def _intercept_request(self, route: Any, request: Any) -> None:
        """请求拦截回调，捕获签名 headers（x-s, x-t, x-s-common）。"""
        try:
            headers = request.headers
            for key in ("x-s", "x-t", "x-s-common"):
                if key in headers:
                    self._captured_headers[key] = headers[key]
        except Exception:
            pass
        await route.continue_()

    # ------------------------------------------------------------------
    # Platform interval enforcement
    # ------------------------------------------------------------------

    async def _enforce_platform_interval(self, platform: str) -> None:
        """确保同平台连续请求间隔不少于 MIN_PLATFORM_INTERVAL 秒。"""
        now = time.time()
        last = self._last_platform_request.get(platform, 0.0)
        wait = self.MIN_PLATFORM_INTERVAL - (now - last)
        if wait > 0:
            await asyncio.sleep(wait)
        self._last_platform_request[platform] = time.time()

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    async def search_platform(
        self, query: str, config: PlatformConfig
    ) -> List[RawSearchResult]:
        """在指定平台执行搜索，返回原始结果。

        对于 use_hybrid_mode=True 的平台，注册 API 响应拦截器，
        从拦截到的 JSON 中提取结构化数据。
        搜索阶段全量获取（~60 条），通过多次滚动触发分页 API。
        """
        if not self._context:
            logger.error("浏览器未启动，无法搜索")
            return []

        await self._enforce_platform_interval(config.name)

        # 清空上次搜索的拦截数据
        self._intercepted_search.clear()

        page = await self._context.new_page()
        page.set_default_timeout(self.PAGE_TIMEOUT)

        try:
            # 注册 API 响应拦截器（混合模式）
            if config.use_hybrid_mode:
                page.on("response", self._intercept_response)

            # 打开搜索页
            search_url = config.search_url_template.format(query=quote(query))
            logger.info(f"搜索 {config.name}: {query}")
            try:
                await page.goto(search_url, wait_until="domcontentloaded", timeout=self.PAGE_TIMEOUT)
            except Exception as e:
                logger.warning(f"搜索页加载异常 ({config.name}): {e}")

            await asyncio.sleep(_random_delay())

            # 检查登录状态
            if config.requires_login:
                logged_in = await self.ensure_logged_in(page, config)
                if not logged_in:
                    logger.warning(f"登录失效 ({config.name})，跳过搜索")
                    return []

            # 检查验证码/反爬页面
            if await self._detect_captcha(page):
                logger.warning(f"检测到验证码/反爬页面 ({config.name})，跳过")
                return []

            # 滚动加载更多结果
            for i in range(self.SCROLL_COUNT):
                await page.evaluate(f"window.scrollBy(0, {self.SCROLL_PX})")
                await asyncio.sleep(random.uniform(1.5, 2.5))

            # 提取结果
            if config.use_hybrid_mode and self._intercepted_search:
                results = ResourceCollector.extract_from_intercepted_json(
                    self._intercepted_search, config
                )
                logger.info(f"混合模式提取 {len(results)} 条结果 ({config.name})")
            elif config.use_js_extraction:
                results = await ResourceCollector.extract_search_results_js(page, config)
                logger.info(f"JS 提取 {len(results)} 条结果 ({config.name})")
            else:
                results = await ResourceCollector.extract_search_results(page, config)
                logger.info(f"CSS 提取 {len(results)} 条结果 ({config.name})")

            return results

        except Exception as e:
            logger.error(f"搜索失败 ({config.name}): {e}")
            return []
        finally:
            try:
                await page.close()
            except Exception:
                pass

    # ------------------------------------------------------------------
    # Detail fetching
    # ------------------------------------------------------------------

    async def fetch_details_parallel(
        self, notes: List[RawSearchResult], config: PlatformConfig, top_k: int = 20
    ) -> List[RawSearchResult]:
        """并行获取 top_k 条结果的详情页（正文 + 评论）。

        使用 asyncio.Semaphore 控制最多 DETAIL_CONCURRENCY 个 tab 并发。
        每个 tab 独立注册 API 响应拦截器。
        """
        if not self._context:
            logger.error("浏览器未启动，无法获取详情")
            return notes

        to_fetch = notes[:top_k]
        sem = asyncio.Semaphore(self.DETAIL_CONCURRENCY)

        async def _fetch_one(note: RawSearchResult, idx: int) -> None:
            async with sem:
                await self._enforce_platform_interval(config.name)
                detail = await self.fetch_detail(note.url, config)
                if detail:
                    # 合并详情数据到 note
                    if detail.content_snippet:
                        note.content_snippet = detail.content_snippet
                    if detail.top_comments:
                        note.top_comments = detail.top_comments
                        note.comments = [c.get("text", "") for c in detail.top_comments]
                    if detail.image_urls:
                        note.image_urls = detail.image_urls
                    # 更新互动指标（如果详情页有更精确的数据）
                    if detail.likes > 0:
                        note.engagement_metrics["likes"] = detail.likes
                    if detail.favorites > 0:
                        note.engagement_metrics["collected"] = detail.favorites
                    if detail.comments_count > 0:
                        note.engagement_metrics["comments_count"] = detail.comments_count

        tasks = [
            _fetch_one(note, i)
            for i, note in enumerate(to_fetch)
        ]
        await asyncio.gather(*tasks, return_exceptions=True)

        return notes

    async def fetch_detail(
        self, url: str, config: PlatformConfig, retry: int = 0
    ) -> Optional[ResourceDetail]:
        """进入详情页提取内容和评论，支持最多 DETAIL_MAX_RETRIES 次重试。

        优先使用拦截到的 API 数据，回退到 __INITIAL_STATE__ 或 DOM 提取。
        """
        if not self._context:
            return None

        page = await self._context.new_page()
        page.set_default_timeout(self.PAGE_TIMEOUT)

        # 提取 note_id 用于匹配拦截数据
        note_id = ""
        m = re.search(r"/explore/([a-f0-9]+)", url)
        if m:
            note_id = m.group(1)

        # 为此 tab 注册独立的响应拦截器
        detail_handler = self._make_detail_response_handler(note_id)
        if config.use_hybrid_mode:
            page.on("response", detail_handler)

        try:
            logger.debug(f"获取详情: {url[:80]}...")
            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=self.PAGE_TIMEOUT)
            except Exception as e:
                logger.warning(f"详情页加载异常: {e}")
                if retry < self.DETAIL_MAX_RETRIES:
                    await page.close()
                    await asyncio.sleep(_random_delay())
                    return await self.fetch_detail(url, config, retry + 1)
                return None

            await asyncio.sleep(_random_delay())

            # 关闭可能的登录弹窗
            await self._dismiss_login_popup(page)

            # 滚动触发评论加载
            for _ in range(self.DETAIL_SCROLL_COUNT):
                await page.evaluate(f"window.scrollBy(0, {self.DETAIL_SCROLL_PX})")
                await asyncio.sleep(0.8)
            await asyncio.sleep(1)

            # 提取正文（三级回退）
            content = await self._extract_content_from_page(page)

            # 提取图片 URL
            image_urls = await ResourceCollector.extract_image_urls(page)

            # 提取评论（优先拦截数据）
            top_comments: List[Dict[str, str]] = []
            async with self._get_comment_lock():
                raw_comments = self._intercepted_comments.get(note_id, [])
            if raw_comments:
                top_comments = ResourceCollector.parse_intercepted_comments(raw_comments)
            else:
                # 回退到 DOM 提取
                top_comments = await ResourceCollector.extract_top_comments(page, config)

            detail = ResourceDetail(
                content_snippet=content,
                top_comments=top_comments,
                comments=[c.get("text", "") for c in top_comments],
                image_urls=image_urls,
            )

            status_parts = []
            if content:
                status_parts.append(f"正文{len(content)}字")
            if top_comments:
                status_parts.append(f"评论{len(top_comments)}条")
            if image_urls:
                status_parts.append(f"图片{len(image_urls)}张")
            logger.info(f"详情完成: {' '.join(status_parts) or '无数据'}")

            return detail

        except Exception as e:
            logger.error(f"详情获取失败: {e}")
            if retry < self.DETAIL_MAX_RETRIES:
                await asyncio.sleep(_random_delay())
                try:
                    await page.close()
                except Exception:
                    pass
                return await self.fetch_detail(url, config, retry + 1)
            return None
        finally:
            try:
                await page.close()
            except Exception:
                pass

    def _make_detail_response_handler(self, note_id: str):
        """为每个详情页 tab 创建独立的响应拦截器。"""
        async def handler(response: Any) -> None:
            url = response.url
            try:
                if "/api/sns/web/v2/comment/page" in url and response.status == 200:
                    data = await response.json()
                    if data.get("success") or data.get("code") == 0:
                        comments = data.get("data", {}).get("comments", [])
                        m = re.search(r"note_id=([a-f0-9]+)", url)
                        if m:
                            nid = m.group(1)
                            async with self._get_comment_lock():
                                self._intercepted_comments[nid] = comments
                elif "/api/sns/web/v1/feed" in url and response.status == 200:
                    data = await response.json()
                    if data.get("success") or data.get("code") == 0:
                        feed_items = data.get("data", {}).get("items", [])
                        for fi in feed_items:
                            nid = fi.get("id", "")
                            if nid:
                                self._intercepted_details[nid] = fi
            except Exception:
                pass
        return handler

    # ------------------------------------------------------------------
    # Content extraction (three-level fallback)
    # ------------------------------------------------------------------

    async def _extract_content_from_page(self, page: Any) -> str:
        """从详情页提取正文：三级回退策略。

        1. 优先：API 拦截数据（feed API）
        2. 回退：__INITIAL_STATE__ 内嵌 JSON
        3. 兜底：DOM 选择器
        """
        # Level 1: 检查拦截到的 feed API 数据
        m = re.search(r"/explore/([a-f0-9]+)", page.url)
        if m:
            nid = m.group(1)
            detail_data = self._intercepted_details.get(nid)
            if detail_data:
                try:
                    note = detail_data.get("note_card", detail_data.get("note", {}))
                    desc = note.get("desc", "")
                    if desc:
                        return desc[:800]
                except Exception:
                    pass

        # Level 2: __INITIAL_STATE__
        content = await ResourceCollector.extract_detail_from_initial_state(page)
        if content:
            return content

        # Level 3: DOM 选择器回退
        try:
            result = await page.evaluate("""() => {
                const selectors = ['#detail-desc', '.note-text', '.note-content', 'div.desc', 'article'];
                for (const sel of selectors) {
                    const el = document.querySelector(sel);
                    if (el && el.innerText.trim().length > 20) {
                        return el.innerText.trim().substring(0, 800);
                    }
                }
                return '';
            }""")
            return result or ""
        except Exception:
            return ""

    # ------------------------------------------------------------------
    # Image content extraction (TODO stub)
    # ------------------------------------------------------------------

    async def extract_image_content(
        self, image_urls: List[str], max_images: int = 3
    ) -> List[str]:
        """[TODO: 未来实现] 下载前 max_images 张图片，调用多模态 LLM 提取图片内容。

        MVP 阶段返回空列表。
        """
        return []

    # ------------------------------------------------------------------
    # Login & anti-detection helpers
    # ------------------------------------------------------------------

    async def ensure_logged_in(self, page: Any, config: PlatformConfig) -> bool:
        """检查登录状态，失效时记录警告。

        通过检查 URL 是否被重定向（不再包含搜索关键词）来判断登录状态。
        """
        try:
            current_url = page.url
            # 小红书：如果被重定向到首页或登录页，说明 Cookie 失效
            if config.name == "xiaohongshu":
                if "search_result" not in current_url and "explore" not in current_url:
                    logger.warning(f"Cookie 过期 ({config.name})，需要重新登录")
                    return False
            return True
        except Exception:
            return False

    async def _dismiss_login_popup(self, page: Any) -> None:
        """自动检测并关闭登录弹窗。"""
        try:
            # 常见的关闭按钮选择器
            close_selectors = [
                ".close-button",
                ".login-close",
                "[class*='close']",
                "button.close",
            ]
            for sel in close_selectors:
                try:
                    el = await page.query_selector(sel)
                    if el and await el.is_visible():
                        await el.click()
                        await asyncio.sleep(0.5)
                        return
                except Exception:
                    continue
        except Exception:
            pass

    async def _detect_captcha(self, page: Any) -> bool:
        """检测验证码/反爬页面。"""
        try:
            content = await page.content()
            captcha_indicators = [
                "captcha",
                "验证码",
                "人机验证",
                "请完成安全验证",
                "滑动验证",
            ]
            content_lower = content.lower()
            for indicator in captcha_indicators:
                if indicator in content_lower:
                    return True
            return False
        except Exception:
            return False

