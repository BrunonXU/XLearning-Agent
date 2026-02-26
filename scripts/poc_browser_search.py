"""
POC: 小红书浏览器 Agent 搜索测试

用 Playwright 模拟真实浏览器访问小红书搜索页面，
提取搜索结果（标题、URL、互动指标），
点击进入详情页读取正文、收藏数、评论数、高赞评论。

首次运行需要手动登录（cookie 会保存到本地，后续自动复用）。
建议用小号登录，避免影响主号推荐。

用法:
    venv\Scripts\python.exe scripts/poc_browser_search.py "GRE 备考"
    venv\Scripts\python.exe scripts/poc_browser_search.py --login "GRE 备考"  # 强制重新登录
"""

import asyncio
import json
import random
import re
import sys
import time
from dataclasses import dataclass, field, asdict
from typing import List
from pathlib import Path

COOKIE_FILE = Path("scripts/.xhs_cookies.json")
SCREENSHOT_DIR = Path("scripts/debug_screenshots")


@dataclass
class SearchResultPOC:
    title: str = ""
    url: str = ""           # 带 token 的原始搜索结果链接
    note_id: str = ""
    author: str = ""
    likes: str = ""
    detail_likes: str = ""
    favorites: str = ""
    comments_count: str = ""
    content_snippet: str = ""
    top_comments: List[dict] = field(default_factory=list)


async def random_delay(min_s: float = 1.0, max_s: float = 3.0):
    await asyncio.sleep(random.uniform(min_s, max_s))


async def save_screenshot(page, name: str):
    SCREENSHOT_DIR.mkdir(exist_ok=True)
    path = SCREENSHOT_DIR / f"{name}.png"
    await page.screenshot(path=str(path), full_page=False)
    print(f"  [截图] {path}")


def extract_note_id(url: str) -> str:
    m = re.search(r'/(explore|discovery/item|search_result)/([a-f0-9]{24})', url)
    return m.group(2) if m else ""


async def create_browser_context(playwright, force_login=False):
    browser = await playwright.chromium.launch(
        headless=False,
        args=["--disable-blink-features=AutomationControlled", "--no-sandbox"]
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
        Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3] });
    """)

    # 加载已保存的 cookie
    if not force_login and COOKIE_FILE.exists():
        try:
            cookies = json.loads(COOKIE_FILE.read_text(encoding="utf-8"))
            await context.add_cookies(cookies)
            print(f"  已加载 {len(cookies)} 条 cookie")
        except Exception as e:
            print(f"  加载 cookie 失败: {e}")

    return browser, context


async def do_login(context):
    page = await context.new_page()
    await page.goto("https://www.xiaohongshu.com", wait_until="domcontentloaded")
    print("\n" + "=" * 60)
    print("请在浏览器中手动登录小红书（建议用小号）")
    print("登录完成后，在终端按 Enter 继续...")
    print("=" * 60)
    await asyncio.get_event_loop().run_in_executor(None, input)
    cookies = await context.cookies()
    COOKIE_FILE.write_text(json.dumps(cookies, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  已保存 {len(cookies)} 条 cookie")
    await page.close()


async def ensure_logged_in(page, context):
    """检查是否需要登录，如果需要则执行登录流程"""
    # 检查是否被重定向到首页或出现登录弹窗
    current_url = page.url
    if "search_result" not in current_url:
        print("  被重定向了，可能需要登录...")
        await do_login(context)
        return True

    try:
        login_modal = await page.query_selector('[class*="login-container"], [class*="LoginModal"]')
        if login_modal and await login_modal.is_visible():
            print("  检测到登录弹窗，需要登录...")
            await do_login(context)
            return True
    except Exception:
        pass

    return False


async def search_xiaohongshu(query: str, max_results: int = 15, force_login: bool = False) -> List[SearchResultPOC]:
    from playwright.async_api import async_playwright

    results: List[SearchResultPOC] = []

    async with async_playwright() as p:
        browser, context = await create_browser_context(p, force_login)

        if force_login or not COOKIE_FILE.exists():
            await do_login(context)

        page = await context.new_page()
        page.set_default_timeout(15000)

        try:
            # 1. 访问搜索页
            search_url = f"https://www.xiaohongshu.com/search_result?keyword={query}&source=web_search_result_note"
            print(f"\n[1] 访问搜索页...")
            await page.goto(search_url, wait_until="domcontentloaded")
            await random_delay(3, 5)

            # 检查登录状态
            need_relogin = await ensure_logged_in(page, context)
            if need_relogin:
                await page.goto(search_url, wait_until="domcontentloaded")
                await random_delay(3, 5)

            await save_screenshot(page, "01_search_page")

            # 2. 多次滚动加载更多
            print("[2] 滚动加载更多结果...")
            for _ in range(5):
                await page.evaluate("window.scrollBy(0, 800)")
                await random_delay(1.5, 2.5)
            await save_screenshot(page, "02_after_scroll")

            # 3. 提取搜索结果（按笔记 ID 去重，保留带 token 的链接）
            print("[3] 提取搜索结果...")
            raw_results = await page.evaluate("""
                () => {
                    const results = [];
                    const seenIds = new Set();

                    const links = document.querySelectorAll(
                        'a[href*="/explore/"], a[href*="/discovery/item/"], a[href*="/search_result/"]'
                    );

                    for (const link of links) {
                        const href = link.getAttribute('href') || '';
                        const m = href.match(/\\/(explore|discovery\\/item|search_result)\\/([a-f0-9]{24})/);
                        if (!m) continue;
                        const noteId = m[2];
                        if (seenIds.has(noteId)) continue;
                        seenIds.add(noteId);

                        // 优先保留带 xsec_token 的链接（详情页需要）
                        let bestUrl = href;
                        // 如果当前链接没有 token，看看同 noteId 的其他链接
                        if (!href.includes('xsec_token')) {
                            const altLink = document.querySelector(
                                'a[href*="' + noteId + '"][href*="xsec_token"]'
                            );
                            if (altLink) bestUrl = altLink.getAttribute('href') || href;
                        }

                        // 补全 URL
                        if (bestUrl.startsWith('/')) {
                            bestUrl = 'https://www.xiaohongshu.com' + bestUrl;
                        }

                        // 向上找卡片容器
                        let card = link;
                        for (let i = 0; i < 5; i++) {
                            if (card.parentElement) card = card.parentElement;
                            if (card.tagName === 'SECTION' ||
                                (card.className && /note|card/i.test(card.className))) break;
                        }

                        const fullText = card.innerText || '';
                        const lines = fullText.split('\\n').map(l => l.trim()).filter(l => l.length > 0);

                        let title = '';
                        const titleEl = card.querySelector('a.title span, a.title, .title span, .title');
                        if (titleEl) title = titleEl.innerText.trim();
                        if (!title) {
                            const candidates = lines.filter(l => l.length > 4 && !/^\\d+$/.test(l));
                            if (candidates.length > 0) title = candidates[0];
                        }

                        let author = '';
                        const authorEl = card.querySelector(
                            '.author-wrapper .name, .author .name, span.name, .name'
                        );
                        if (authorEl) author = authorEl.innerText.trim();

                        let likes = '';
                        const likeEl = card.querySelector(
                            '.like-wrapper .count, span.count, .count'
                        );
                        if (likeEl) likes = likeEl.innerText.trim();

                        results.push({
                            title: title.substring(0, 120),
                            url: bestUrl,
                            noteId,
                            author,
                            likes
                        });
                    }
                    return results;
                }
            """)

            print(f"  去重后 {len(raw_results)} 条结果")
            for i, raw in enumerate(raw_results[:max_results]):
                r = SearchResultPOC(
                    title=raw.get("title", ""),
                    url=raw.get("url", ""),
                    note_id=raw.get("noteId", ""),
                    author=raw.get("author", ""),
                    likes=raw.get("likes", ""),
                )
                results.append(r)
                print(f"  [{i+1}] {r.title[:50]}  👍{r.likes}  by {r.author}")

            # 4. 进入详情页提取深度数据
            detail_count = min(5, len(results))
            print(f"\n[4] 进入前 {detail_count} 条详情页...")

            for i, result in enumerate(results[:detail_count]):
                if not result.url:
                    continue

                try:
                    title_preview = result.title[:30] if result.title else "..."
                    print(f"\n  --- [{i+1}/{detail_count}] {title_preview} ---")
                    detail_page = await context.new_page()
                    detail_page.set_default_timeout(15000)

                    await detail_page.goto(result.url, wait_until="domcontentloaded")
                    await random_delay(3, 5)

                    # 检查是否 404 或被重定向
                    detail_url = detail_page.url
                    if "404" in (await detail_page.title()) or "search_result" not in detail_url and "explore" not in detail_url:
                        print(f"  ⚠ 页面无法访问: {detail_url}")
                        await detail_page.close()
                        continue

                    # 关闭可能的登录弹窗
                    try:
                        close_btn = await detail_page.query_selector(
                            '[class*="close-button"], [class*="login"] [class*="close"], .close-icon'
                        )
                        if close_btn and await close_btn.is_visible():
                            await close_btn.click()
                            await random_delay(0.5, 1)
                    except Exception:
                        pass

                    # 滚动到评论区
                    for _ in range(4):
                        await detail_page.evaluate("window.scrollBy(0, 500)")
                        await random_delay(1, 1.5)

                    await save_screenshot(detail_page, f"03_detail_{i+1}")

                    # JS 提取详情数据
                    detail_data = await detail_page.evaluate("""
                        () => {
                            // 正文
                            let content = '';
                            for (const sel of ['#detail-desc', '.note-text', '.note-content', 'div.desc', 'article']) {
                                const el = document.querySelector(sel);
                                if (el && el.innerText.trim().length > 20) {
                                    content = el.innerText.trim();
                                    break;
                                }
                            }

                            // 互动指标
                            let detailLikes = '', favorites = '', commentsCount = '';

                            // 方法1: 从互动栏提取
                            const bar = document.querySelector(
                                '.interact-container, [class*="interact"], [class*="engage"]'
                            );
                            if (bar) {
                                const spans = bar.querySelectorAll('span, .count');
                                const nums = [];
                                for (const s of spans) {
                                    const t = s.innerText.trim();
                                    if (/^[\\d.]+[万kK]?$/.test(t)) nums.push(t);
                                }
                                if (nums.length >= 1) detailLikes = nums[0];
                                if (nums.length >= 2) favorites = nums[1];
                                if (nums.length >= 3) commentsCount = nums[2];
                            }

                            // 方法2: 按 class 名找
                            if (!detailLikes) {
                                const el = document.querySelector('[class*="like"] .count, [class*="like"] span.count');
                                if (el) detailLikes = el.innerText.trim();
                            }
                            if (!favorites) {
                                const el = document.querySelector('[class*="collect"] .count, [class*="collect"] span.count');
                                if (el) favorites = el.innerText.trim();
                            }
                            if (!commentsCount) {
                                const el = document.querySelector('[class*="chat"] .count, [class*="comment-count"]');
                                if (el) commentsCount = el.innerText.trim();
                            }

                            // 评论（含点赞数）
                            const topComments = [];
                            const commentItems = document.querySelectorAll(
                                '[class*="comment-item"], [class*="commentItem"], .comment-item'
                            );
                            for (const item of Array.from(commentItems).slice(0, 20)) {
                                let text = '';
                                const textEl = item.querySelector(
                                    '[class*="content"], .note-text, .text, p'
                                );
                                if (textEl) text = textEl.innerText.trim();

                                let commentLikes = '0';
                                const likeEl = item.querySelector(
                                    '[class*="like"] .count, [class*="like"] span, .count'
                                );
                                if (likeEl) {
                                    const lt = likeEl.innerText.trim();
                                    if (/^[\\d.]+[万kK]?$/.test(lt)) commentLikes = lt;
                                }

                                if (text && text.length > 2) {
                                    topComments.push({ text: text.substring(0, 300), likes: commentLikes });
                                }
                            }

                            // 按赞数排序
                            topComments.sort((a, b) => {
                                const p = (s) => {
                                    if (!s) return 0;
                                    if (s.includes('万')) return parseFloat(s) * 10000;
                                    if (s.toLowerCase().includes('k')) return parseFloat(s) * 1000;
                                    return parseInt(s) || 0;
                                };
                                return p(b.likes) - p(a.likes);
                            });

                            return {
                                content: content.substring(0, 800),
                                detailLikes, favorites, commentsCount,
                                topComments: topComments.slice(0, 10)
                            };
                        }
                    """)

                    result.content_snippet = detail_data.get("content", "")
                    result.detail_likes = detail_data.get("detailLikes", "")
                    result.favorites = detail_data.get("favorites", "")
                    result.comments_count = detail_data.get("commentsCount", "")
                    result.top_comments = detail_data.get("topComments", [])

                    print(f"  👍 {result.detail_likes}  ⭐ {result.favorites}  💬 {result.comments_count}")
                    if result.content_snippet:
                        print(f"  正文: {result.content_snippet[:80]}...")
                    if result.top_comments:
                        print(f"  高赞评论 ({len(result.top_comments)} 条):")
                        for c in result.top_comments[:3]:
                            print(f"    [{c.get('likes','0')}赞] {c.get('text','')[:60]}")

                    await detail_page.close()
                    await random_delay(2, 3)

                except Exception as e:
                    print(f"  详情页失败: {e}")

            # 5. 按价值排序
            def parse_metric(s: str) -> int:
                if not s: return 0
                s = s.strip()
                if '万' in s: return int(float(s.replace('万', '')) * 10000)
                if s.lower().endswith('k'): return int(float(s[:-1]) * 1000)
                try: return int(s)
                except ValueError: return 0

            results.sort(key=lambda r: (
                parse_metric(r.comments_count) * 3 +
                parse_metric(r.favorites) * 2 +
                parse_metric(r.detail_likes or r.likes)
            ), reverse=True)

        except Exception as e:
            print(f"\n[ERROR] {e}")
            try:
                await save_screenshot(page, "error")
            except Exception:
                pass
        finally:
            # 每次运行后更新 cookie
            try:
                cookies = await context.cookies()
                COOKIE_FILE.write_text(
                    json.dumps(cookies, ensure_ascii=False, indent=2), encoding="utf-8"
                )
            except Exception:
                pass
            await browser.close()

    return results


async def main():
    force_login = "--login" in sys.argv
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    query = args[0] if args else "GRE 备考"

    print("=" * 60)
    print(f"小红书搜索 POC")
    print(f"搜索关键词: {query}")
    if force_login:
        print("模式: 强制重新登录")
    print("=" * 60)

    start = time.time()
    results = await search_xiaohongshu(query, force_login=force_login)
    elapsed = time.time() - start

    print(f"\n{'=' * 60}")
    print(f"完成! 耗时 {elapsed:.1f}s, {len(results)} 条结果")
    print(f"排序: 评论数×3 + 收藏数×2 + 点赞数")
    print("=" * 60)

    for i, r in enumerate(results):
        print(f"\n--- 结果 {i+1} ---")
        print(f"  标题: {r.title}")
        print(f"  链接: {r.url}")
        print(f"  作者: {r.author}")
        print(f"  👍 {r.detail_likes or r.likes}  ⭐ {r.favorites}  💬 {r.comments_count}")
        if r.content_snippet:
            print(f"  正文: {r.content_snippet[:120]}...")
        if r.top_comments:
            print(f"  高赞评论:")
            for c in r.top_comments[:5]:
                print(f"    [{c.get('likes','0')}赞] {c.get('text','')[:80]}")

    output_path = "scripts/xhs_results.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump([asdict(r) for r in results], f, ensure_ascii=False, indent=2)
    print(f"\n结果已保存到 {output_path}")


if __name__ == "__main__":
    asyncio.run(main())
