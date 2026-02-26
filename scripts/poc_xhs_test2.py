"""快速测试：agent开发 关键词搜索"""
import asyncio, json, sys, time, re
from pathlib import Path
from urllib.parse import quote
from dataclasses import dataclass, field, asdict
from typing import List, Optional

COOKIE_FILE = Path("scripts/.xhs_cookies.json")

@dataclass
class Note:
    title: str = ""
    note_id: str = ""
    url: str = ""
    author: str = ""
    likes: int = 0
    collected: int = 0
    comments_count: int = 0
    content: str = ""
    top_comments: List[dict] = field(default_factory=list)
    xsec_token: str = ""

search_items = []
comment_map = {}

async def on_response(response):
    url = response.url
    try:
        if "/api/sns/web/v1/search/notes" in url and response.status == 200:
            data = await response.json()
            if data.get("success") or data.get("code") == 0:
                items = data.get("data", {}).get("items", [])
                search_items.extend(items)
                print(f"  [拦截] 搜索: {len(items)} 条 (累计 {len(search_items)})")
        elif "/api/sns/web/v2/comment/page" in url and response.status == 200:
            data = await response.json()
            if data.get("success") or data.get("code") == 0:
                comments = data.get("data", {}).get("comments", [])
                m = re.search(r'note_id=([a-f0-9]+)', url)
                if m:
                    comment_map[m.group(1)] = comments
                    print(f"  [拦截] 评论: {m.group(1)[:8]}... ({len(comments)}条)")
    except:
        pass


async def main():
    from playwright.async_api import async_playwright
    import random

    query = sys.argv[1] if len(sys.argv) > 1 else "agent开发"
    print(f"搜索: {query}")

    if not COOKIE_FILE.exists():
        print("Cookie 不存在，请先登录"); return

    cookies = json.loads(COOKIE_FILE.read_text(encoding="utf-8"))
    print(f"Cookie: {len(cookies)} 条")

    start = time.time()
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, args=["--disable-blink-features=AutomationControlled"])
        ctx = await browser.new_context(
            viewport={"width": 1280, "height": 900},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
            locale="zh-CN",
        )
        await ctx.add_init_script("Object.defineProperty(navigator,'webdriver',{get:()=>undefined})")
        await ctx.add_cookies(cookies)

        page = await ctx.new_page()
        page.set_default_timeout(20000)
        page.on("response", on_response)

        url = f"https://www.xiaohongshu.com/search_result?keyword={quote(query)}&source=web_search_result_note"
        print(f"[1] 打开搜索页...")
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=20000)
        except Exception as e:
            print(f"  页面加载异常: {e}")
        await asyncio.sleep(4)

        cur = page.url
        title = await page.title()
        print(f"  URL: {cur}")
        print(f"  Title: {title}")

        if "search_result" not in cur:
            print("  ⚠ Cookie 过期，需要重新登录")
            print("  请运行: venv\\Scripts\\python.exe scripts/poc_browser_search.py --login")
            await browser.close()
            return

        print(f"[2] 滚动加载...")
        for i in range(5):
            await page.evaluate("window.scrollBy(0, 800)")
            await asyncio.sleep(random.uniform(1.5, 2.5))

        print(f"  拦截到 {len(search_items)} 条搜索结果")

        # 解析
        notes = []
        seen = set()
        for item in search_items:
            nc = item.get("note_card", {})
            if not nc: continue
            nid = nc.get("note_id", item.get("id", ""))
            if nid in seen: continue
            seen.add(nid)
            interact = nc.get("interact_info", {})
            user = nc.get("user", {})
            xt = item.get("xsec_token", "")
            n = Note(
                title=nc.get("display_title", ""),
                note_id=nid,
                url=f"https://www.xiaohongshu.com/explore/{nid}?xsec_token={xt}&xsec_source=pc_search" if xt else f"https://www.xiaohongshu.com/explore/{nid}",
                author=user.get("nickname", ""),
                likes=int(interact.get("liked_count", 0) or 0),
                collected=int(interact.get("collected_count", 0) or 0),
                comments_count=int(interact.get("comment_count", 0) or 0),
                xsec_token=xt,
            )
            notes.append(n)

        # 排序
        notes.sort(key=lambda n: n.comments_count*3 + n.collected*2 + n.likes, reverse=True)
        print(f"  去重后 {len(notes)} 条")

        # 前10条详情
        detail_n = min(10, len(notes))
        print(f"\n[3] 获取前 {detail_n} 条详情...")
        for i, note in enumerate(notes[:detail_n]):
            print(f"\n  --- [{i+1}/{detail_n}] {note.title[:40]} ---")
            dp = await ctx.new_page()
            dp.on("response", on_response)
            dp.set_default_timeout(15000)
            try:
                await dp.goto(note.url, wait_until="domcontentloaded", timeout=15000)
                await asyncio.sleep(random.uniform(2, 3))
                for _ in range(3):
                    await dp.evaluate("window.scrollBy(0, 500)")
                    await asyncio.sleep(random.uniform(0.8, 1.2))
                await asyncio.sleep(1)

                # 正文: __INITIAL_STATE__ 或 DOM
                content = await dp.evaluate("""() => {
                    try {
                        const scripts = document.querySelectorAll('script');
                        for (const s of scripts) {
                            const t = s.textContent || '';
                            if (t.includes('__INITIAL_STATE__')) {
                                const m = t.match(/__INITIAL_STATE__\\s*=\\s*({.+?})\\s*<?\\/?\\/?\\/script/s)
                                    || t.match(/__INITIAL_STATE__\\s*=\\s*({.+})/s);
                                if (m) {
                                    const cleaned = m[1].replace(/undefined/g, 'null');
                                    const state = JSON.parse(cleaned);
                                    const nd = state?.note?.noteDetailMap;
                                    if (nd) {
                                        const k = Object.keys(nd)[0];
                                        const n = nd[k]?.note;
                                        if (n?.desc) return n.desc.substring(0, 800);
                                    }
                                }
                            }
                        }
                    } catch(e) {}
                    for (const sel of ['#detail-desc','.note-text','.note-content','div.desc','article']) {
                        const el = document.querySelector(sel);
                        if (el && el.innerText.trim().length > 20) return el.innerText.trim().substring(0, 800);
                    }
                    return '';
                }""")
                if content:
                    note.content = content
                    print(f"  ✓ 正文: {len(content)} 字")
                else:
                    print(f"  ✗ 无正文")

                # 评论
                if note.note_id in comment_map:
                    raw = comment_map[note.note_id]
                    parsed = []
                    for c in raw:
                        txt = c.get("content", "")
                        lk = int(c.get("like_count", 0) or 0)
                        au = c.get("user_info", {}).get("nickname", "")
                        if txt and len(txt) > 2:
                            parsed.append({"text": txt[:300], "likes": lk, "author": au})
                    parsed.sort(key=lambda x: x["likes"], reverse=True)
                    note.top_comments = parsed[:10]
                    print(f"  ✓ 评论: {len(note.top_comments)} 条")
                else:
                    print(f"  ✗ 无评论")
            except Exception as e:
                print(f"  失败: {e}")
            finally:
                await dp.close()
                await asyncio.sleep(random.uniform(0.5, 1))

        # 保存 cookie
        new_cookies = await ctx.cookies()
        COOKIE_FILE.write_text(json.dumps(new_cookies, ensure_ascii=False, indent=2), encoding="utf-8")
        await browser.close()

    elapsed = time.time() - start
    print(f"\n完成! {elapsed:.1f}s, {len(notes)} 条结果")

    # 保存 JSON
    out = [asdict(n) for n in notes]
    Path("scripts/xhs_agent_results.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print("已保存到 scripts/xhs_agent_results.json")

if __name__ == "__main__":
    asyncio.run(main())
