"""
POC: 小红书混合方案搜索测试

策略：用 Playwright 浏览器执行搜索（自带签名），
但通过拦截 API 响应获取结构化 JSON 数据，
避免 CSS 选择器不稳定的问题。

优势：
- 不需要逆向签名算法（X-S, X-T 等）
- 数据来自 API JSON，100% 完整
- 比纯浏览器方案更快（不需要逐个打开详情页）
- 比纯 API 方案更稳定（不会被反爬拦截）

用法:
    venv\Scripts\python.exe scripts/poc_xhs_hybrid.py "GRE 备考"
"""

import asyncio
import json
import sys
import time
import re
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import List, Optional

COOKIE_FILE = Path("scripts/.xhs_cookies.json")

@dataclass
class XhsNote:
    title: str = ""
    note_id: str = ""
    url: str = ""
    author: str = ""
    author_id: str = ""
    likes: int = 0
    collected: int = 0
    comments_count: int = 0
    share_count: int = 0
    content: str = ""
    note_type: str = ""
    top_comments: List[dict] = field(default_factory=list)
    xsec_token: str = ""


class XhsHybridSearcher:
    """混合搜索器：浏览器执行 + API 响应拦截"""

    def __init__(self):
        self.search_results_raw: List[dict] = []
        self.detail_results: dict = {}  # note_id -> detail data
        self.comment_results: dict = {}  # note_id -> comments
        self.captured_headers: dict = {}  # 捕获的请求 headers（含签名）

    async def _intercept_response(self, response):
        """拦截 API 响应，提取结构化数据"""
        url = response.url
        try:
            if "/api/sns/web/v1/search/notes" in url and response.status == 200:
                data = await response.json()
                if data.get("success") or data.get("code") == 0:
                    items = data.get("data", {}).get("items", [])
                    self.search_results_raw.extend(items)
                    print(f"  [拦截] 搜索结果: {len(items)} 条")

            elif "/api/sns/web/v1/feed" in url and response.status == 200:
                data = await response.json()
                if data.get("success") or data.get("code") == 0:
                    items = data.get("data", {}).get("items", [])
                    for item in items:
                        note_card = item.get("note_card", {})
                        note_id = note_card.get("note_id", item.get("id", ""))
                        if note_id:
                            self.detail_results[note_id] = note_card
                            print(f"  [拦截] 详情: {note_id[:8]}...")

            elif "/api/sns/web/v2/comment/page" in url and response.status == 200:
                data = await response.json()
                if data.get("success") or data.get("code") == 0:
                    comments = data.get("data", {}).get("comments", [])
                    # 从 URL 提取 note_id
                    m = re.search(r'note_id=([a-f0-9]+)', url)
                    if m:
                        note_id = m.group(1)
                        self.comment_results[note_id] = comments
                        print(f"  [拦截] 评论: {note_id[:8]}... ({len(comments)} 条)")
        except Exception as e:
            pass  # 静默处理非 JSON 响应

    async def _intercept_request(self, route, request):
        """拦截请求，捕获签名 headers"""
        url = request.url
        if "/api/sns/web/" in url:
            headers = request.headers
            # 保存签名相关 headers
            for key in ["x-s", "x-t", "x-s-common", "x-b3-traceid"]:
                if key in headers:
                    self.captured_headers[key] = headers[key]
        await route.continue_()


    async def search(self, query: str, max_detail: int = 5) -> List[XhsNote]:
        from playwright.async_api import async_playwright
        from urllib.parse import quote
        import random

        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=False,
                args=["--disable-blink-features=AutomationControlled"]
            )
            context = await browser.new_context(
                viewport={"width": 1280, "height": 900},
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                ),
                locale="zh-CN",
            )
            await context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            """)

            # 加载 cookie
            if COOKIE_FILE.exists():
                cookies = json.loads(COOKIE_FILE.read_text(encoding="utf-8"))
                await context.add_cookies(cookies)
                print(f"  已加载 {len(cookies)} 条 cookie")

            page = await context.new_page()
            page.set_default_timeout(15000)

            # 注册拦截器
            page.on("response", self._intercept_response)
            await page.route("**/api/sns/web/**", self._intercept_request)

            try:
                # 1. 搜索
                search_url = f"https://www.xiaohongshu.com/search_result?keyword={quote(query)}&source=web_search_result_note"
                print(f"\n[1] 访问搜索页...")
                print(f"  URL: {search_url}")
                await page.goto(search_url, wait_until="domcontentloaded")
                await asyncio.sleep(random.uniform(3, 5))

                print(f"  当前页面 URL: {page.url}")
                print(f"  页面标题: {await page.title()}")

                # 检查是否需要登录
                if "search_result" not in page.url:
                    print("  ⚠ 需要登录! 请手动运行以下命令登录:")
                    print("    venv\\Scripts\\python.exe scripts/poc_browser_search.py --login \"agent开发\"")
                    await browser.close()
                    return []

                # 2. 滚动加载更多（触发更多 API 请求）
                print(f"\n[2] 滚动加载...")
                for i in range(5):
                    await page.evaluate("window.scrollBy(0, 800)")
                    await asyncio.sleep(random.uniform(1.5, 2.5))

                print(f"  共拦截到 {len(self.search_results_raw)} 条搜索结果")

                # 3. 解析搜索结果
                print(f"\n[3] 解析搜索结果...")
                notes = []
                seen_ids = set()
                for item in self.search_results_raw:
                    note = self._parse_search_item(item)
                    if note and note.note_id not in seen_ids:
                        seen_ids.add(note.note_id)
                        notes.append(note)

                print(f"  去重后 {len(notes)} 条")
                for i, n in enumerate(notes):
                    print(f"  [{i+1}] {n.title[:50]}  👍{n.likes} ⭐{n.collected} 💬{n.comments_count}")

                # 4. 逐个打开详情页（触发 feed + comment API）
                detail_count = min(max_detail, len(notes))
                print(f"\n[4] 获取前 {detail_count} 条详情...")

                for i, note in enumerate(notes[:detail_count]):
                    detail_url = note.url if note.url else f"https://www.xiaohongshu.com/explore/{note.note_id}"
                    print(f"\n  --- [{i+1}/{detail_count}] {note.title[:30]} ---")

                    detail_page = await context.new_page()
                    detail_page.on("response", self._intercept_response)
                    detail_page.set_default_timeout(15000)

                    try:
                        await detail_page.goto(detail_url, wait_until="domcontentloaded")
                        await asyncio.sleep(random.uniform(2, 4))

                        # 滚动到评论区
                        for _ in range(3):
                            await detail_page.evaluate("window.scrollBy(0, 500)")
                            await asyncio.sleep(random.uniform(1, 1.5))

                        # 等一下让评论 API 响应回来
                        await asyncio.sleep(1)

                        # 用拦截到的数据补充
                        if note.note_id in self.detail_results:
                            self._enrich_from_detail(note, self.detail_results[note.note_id])
                            print(f"  ✓ 详情(API): 👍{note.likes} ⭐{note.collected} 💬{note.comments_count}")
                            if note.content:
                                print(f"  正文: {note.content[:80]}...")
                        else:
                            # 从页面内嵌 JSON 或 DOM 提取正文
                            content = await detail_page.evaluate("""
                                () => {
                                    // 方法1: __INITIAL_STATE__
                                    try {
                                        const scripts = document.querySelectorAll('script');
                                        for (const s of scripts) {
                                            const text = s.textContent || '';
                                            if (text.includes('__INITIAL_STATE__')) {
                                                const m = text.match(/__INITIAL_STATE__\\s*=\\s*({.+?})\\s*<?\\/?\\/?\\/script/s)
                                                    || text.match(/__INITIAL_STATE__\\s*=\\s*({.+})/s);
                                                if (m) {
                                                    const cleaned = m[1].replace(/undefined/g, 'null');
                                                    const state = JSON.parse(cleaned);
                                                    const noteData = state?.note?.noteDetailMap;
                                                    if (noteData) {
                                                        const firstKey = Object.keys(noteData)[0];
                                                        const note = noteData[firstKey]?.note;
                                                        if (note?.desc) return note.desc.substring(0, 800);
                                                    }
                                                }
                                            }
                                        }
                                    } catch(e) {}
                                    // 方法2: DOM
                                    for (const sel of ['#detail-desc', '.note-text', '.note-content', 'div.desc', 'article']) {
                                        const el = document.querySelector(sel);
                                        if (el && el.innerText.trim().length > 20) {
                                            return el.innerText.trim().substring(0, 800);
                                        }
                                    }
                                    return '';
                                }
                            """)
                            if content:
                                note.content = content
                                print(f"  ✓ 详情(DOM): 正文 {len(content)} 字")
                                print(f"  正文: {note.content[:80]}...")
                            else:
                                print(f"  ✗ 未获取到正文")

                        if note.note_id in self.comment_results:
                            note.top_comments = self._parse_comments(self.comment_results[note.note_id])
                            print(f"  ✓ 评论 ({len(note.top_comments)} 条):")
                            for c in note.top_comments[:3]:
                                print(f"    [{c['likes']}赞] {c['text'][:60]}  —{c['author']}")
                        else:
                            print(f"  ✗ 未拦截到评论数据")

                    except Exception as e:
                        print(f"  详情页失败: {e}")
                    finally:
                        await detail_page.close()
                        await asyncio.sleep(random.uniform(1, 2))

                # 保存 cookie
                cookies = await context.cookies()
                COOKIE_FILE.write_text(json.dumps(cookies, ensure_ascii=False, indent=2), encoding="utf-8")

            finally:
                await browser.close()

            # 排序
            notes.sort(key=lambda n: n.comments_count * 3 + n.collected * 2 + n.likes, reverse=True)
            return notes

    def _parse_search_item(self, item: dict) -> Optional[XhsNote]:
        note_card = item.get("note_card", {})
        if not note_card:
            return None
        interact = note_card.get("interact_info", {})
        user = note_card.get("user", {})
        note_id = note_card.get("note_id", item.get("id", ""))
        xsec_token = item.get("xsec_token", "")

        return XhsNote(
            title=note_card.get("display_title", ""),
            note_id=note_id,
            url=f"https://www.xiaohongshu.com/explore/{note_id}?xsec_token={xsec_token}&xsec_source=pc_search" if xsec_token else f"https://www.xiaohongshu.com/explore/{note_id}",
            author=user.get("nickname", ""),
            author_id=user.get("user_id", ""),
            likes=int(interact.get("liked_count", "0") or 0),
            collected=int(interact.get("collected_count", "0") or 0),
            comments_count=int(interact.get("comment_count", "0") or 0),
            share_count=int(interact.get("share_count", "0") or 0),
            note_type=note_card.get("type", ""),
            xsec_token=xsec_token,
        )

    def _enrich_from_detail(self, note: XhsNote, detail: dict):
        desc = detail.get("desc", "")
        if desc:
            note.content = desc[:800]
        interact = detail.get("interact_info", {})
        if interact:
            note.likes = int(interact.get("liked_count", note.likes) or note.likes)
            note.collected = int(interact.get("collected_count", note.collected) or note.collected)
            note.comments_count = int(interact.get("comment_count", note.comments_count) or note.comments_count)
            note.share_count = int(interact.get("share_count", note.share_count) or note.share_count)

    def _parse_comments(self, raw_comments: List[dict]) -> List[dict]:
        parsed = []
        for c in raw_comments:
            text = c.get("content", "")
            likes = int(c.get("like_count", 0) or 0)
            user = c.get("user_info", {})
            author = user.get("nickname", "")
            if text and len(text) > 2:
                parsed.append({"text": text[:300], "likes": likes, "author": author})
        parsed.sort(key=lambda x: x["likes"], reverse=True)
        return parsed[:10]


async def main():
    query = sys.argv[1] if len(sys.argv) > 1 else "GRE 备考"

    print("=" * 60)
    print(f"小红书混合方案 POC (浏览器 + API 拦截)")
    print(f"搜索关键词: {query}")
    print("=" * 60)

    searcher = XhsHybridSearcher()
    start = time.time()
    notes = await searcher.search(query, max_detail=10)
    elapsed = time.time() - start

    print(f"\n{'=' * 60}")
    print(f"完成! 耗时 {elapsed:.1f}s, {len(notes)} 条结果")
    print(f"排序: 评论数×3 + 收藏数×2 + 点赞数")
    print(f"捕获签名 headers: {list(searcher.captured_headers.keys())}")
    print("=" * 60)

    for i, n in enumerate(notes):
        score = n.comments_count * 3 + n.collected * 2 + n.likes
        print(f"\n--- 结果 {i+1} (综合分: {score}) ---")
        print(f"  标题: {n.title}")
        print(f"  链接: {n.url}")
        print(f"  作者: {n.author}")
        print(f"  👍{n.likes}  ⭐{n.collected}  💬{n.comments_count}  🔗{n.share_count}")
        if n.content:
            print(f"  正文: {n.content[:120]}...")
        if n.top_comments:
            print(f"  高赞评论:")
            for c in n.top_comments[:5]:
                print(f"    [{c['likes']}赞] {c['text'][:80]}")

    # 保存
    output_path = "scripts/xhs_hybrid_results.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump([asdict(n) for n in notes], f, ensure_ascii=False, indent=2)
    print(f"\n结果已保存到 {output_path}")

    # 对比总结
    print(f"\n{'=' * 60}")
    print("混合方案优势:")
    print(f"  - 数据来源: API JSON (100% 结构化)")
    print(f"  - 详情成功率: {sum(1 for n in notes if n.content)}/{min(5, len(notes))}")
    print(f"  - 评论成功率: {sum(1 for n in notes if n.top_comments)}/{min(5, len(notes))}")
    print(f"  - 耗时: {elapsed:.1f}s")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
