"""
POC: 小红书并行详情获取测试

搜索 60 条 + 并行 3 tab 获取 top 20 详情 + 输出 MD 报告
验证并行方案的速度提升和稳定性

用法:
    venv\Scripts\python.exe scripts/poc_xhs_parallel.py "agent开发"
"""
import asyncio
import json
import sys
import time
import re
from pathlib import Path
from urllib.parse import quote
from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict

COOKIE_FILE = Path("scripts/.xhs_cookies.json")
CONCURRENCY = 3  # 并行 tab 数
DETAIL_TOP_K = 20  # 获取详情的 top K


@dataclass
class Note:
    title: str = ""
    note_id: str = ""
    url: str = ""
    author: str = ""
    likes: int = 0
    collected: int = 0
    comments_count: int = 0
    share_count: int = 0
    content: str = ""
    top_comments: List[dict] = field(default_factory=list)
    image_urls: List[str] = field(default_factory=list)
    xsec_token: str = ""


# 全局拦截数据（搜索阶段）
search_items: List[dict] = []
# 每个 note_id 的评论（详情阶段，需要线程安全）
comment_map: Dict[str, list] = {}
comment_lock = asyncio.Lock()


async def on_search_response(response):
    """搜索页的响应拦截"""
    url = response.url
    try:
        if "/api/sns/web/v1/search/notes" in url and response.status == 200:
            data = await response.json()
            if data.get("success") or data.get("code") == 0:
                items = data.get("data", {}).get("items", [])
                search_items.extend(items)
                print(f"  [拦截] 搜索: +{len(items)} 条 (累计 {len(search_items)})")
    except:
        pass


def make_detail_response_handler(note_id: str):
    """为每个详情页 tab 创建独立的响应拦截器"""
    async def handler(response):
        url = response.url
        try:
            if "/api/sns/web/v2/comment/page" in url and response.status == 200:
                data = await response.json()
                if data.get("success") or data.get("code") == 0:
                    comments = data.get("data", {}).get("comments", [])
                    m = re.search(r'note_id=([a-f0-9]+)', url)
                    if m:
                        nid = m.group(1)
                        async with comment_lock:
                            comment_map[nid] = comments
        except:
            pass
    return handler



async def fetch_single_detail(ctx, note: Note, idx: int, total: int, sem: asyncio.Semaphore):
    """获取单条详情（受信号量控制并发）"""
    async with sem:
        print(f"  [{idx+1}/{total}] {note.title[:35]}...")
        dp = await ctx.new_page()
        handler = make_detail_response_handler(note.note_id)
        dp.on("response", handler)
        dp.set_default_timeout(15000)
        try:
            await dp.goto(note.url, wait_until="domcontentloaded", timeout=15000)
            await asyncio.sleep(2)
            # 滚动触发评论
            for _ in range(3):
                await dp.evaluate("window.scrollBy(0, 500)")
                await asyncio.sleep(0.8)
            await asyncio.sleep(1)

            # 正文: __INITIAL_STATE__
            result = await dp.evaluate("""() => {
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
                                    let content = '';
                                    let images = [];
                                    if (n?.desc) content = n.desc.substring(0, 800);
                                    if (n?.imageList) {
                                        images = n.imageList.map(img => 
                                            img.urlDefault || img.url || ''
                                        ).filter(u => u.length > 0).slice(0, 9);
                                    }
                                    return {content, images};
                                }
                            }
                        }
                    }
                } catch(e) {}
                // DOM fallback
                for (const sel of ['#detail-desc','.note-text','.note-content','div.desc','article']) {
                    const el = document.querySelector(sel);
                    if (el && el.innerText.trim().length > 20)
                        return {content: el.innerText.trim().substring(0, 800), images: []};
                }
                return {content: '', images: []};
            }""")

            if result and result.get("content"):
                note.content = result["content"]
                note.image_urls = result.get("images", [])
                status = f"✓ 正文{len(note.content)}字"
                if note.image_urls:
                    status += f" 图片{len(note.image_urls)}张"
            else:
                status = "✗ 无正文"

            # 评论
            await asyncio.sleep(0.5)
            async with comment_lock:
                raw_comments = comment_map.get(note.note_id, [])
            if raw_comments:
                parsed = []
                seen_texts = set()
                for c in raw_comments:
                    txt = c.get("content", "")
                    lk = int(c.get("like_count", 0) or 0)
                    au = c.get("user_info", {}).get("nickname", "")
                    if not txt or len(txt) <= 2:
                        continue
                    # 去重：用前30字作为指纹
                    fingerprint = txt[:30].strip().lower()
                    if fingerprint in seen_texts:
                        continue
                    seen_texts.add(fingerprint)
                    # 过滤广告：含多个营销关键词的跳过
                    ad_keywords = ["私信", "加我", "免费领", "点击链接", "优惠券", "下单", "代购", "微信", "vx", "wx"]
                    ad_count = sum(1 for kw in ad_keywords if kw in txt.lower())
                    if ad_count >= 2:
                        continue
                    parsed.append({"text": txt[:300], "likes": lk, "author": au})
                parsed.sort(key=lambda x: x["likes"], reverse=True)
                note.top_comments = parsed[:10]
                status += f" 评论{len(note.top_comments)}条"
            else:
                status += " 无评论"

            print(f"    {status}")
        except Exception as e:
            print(f"    ✗ 失败: {e}")
        finally:
            await dp.close()



def generate_report(notes: List[Note], query: str, total_count: int,
                    search_time: float, detail_time: float, total_time: float,
                    detail_count: int) -> str:
    """生成 MD 报告"""
    lines = []
    lines.append(f"# 小红书搜索结果：「{query}」（并行版）\n")
    lines.append(f"> 搜索时间：{time.strftime('%Y-%m-%d %H:%M')} | 并行 {CONCURRENCY} tab")
    lines.append(f"> 共 {total_count} 条搜索结果，获取前 {detail_count} 条详情")
    lines.append(f"> 搜索阶段: {search_time:.1f}s | 详情阶段: {detail_time:.1f}s | 总耗时: {total_time:.1f}s")
    lines.append(f"> 综合分 = 评论数×5 + 收藏数×2 + 点赞数\n")

    # 统计
    has_content = sum(1 for n in notes[:detail_count] if n.content)
    has_comments = sum(1 for n in notes[:detail_count] if n.top_comments)
    has_images = sum(1 for n in notes[:detail_count] if n.image_urls)
    lines.append(f"### 数据质量统计\n")
    lines.append(f"| 指标 | 数值 |")
    lines.append(f"|------|------|")
    lines.append(f"| 搜索结果总数 | {total_count} |")
    lines.append(f"| 详情获取数 | {detail_count} |")
    lines.append(f"| 正文成功率 | {has_content}/{detail_count} ({has_content*100//detail_count}%) |")
    lines.append(f"| 评论成功率 | {has_comments}/{detail_count} ({has_comments*100//detail_count}%) |")
    lines.append(f"| 含图片笔记 | {has_images}/{detail_count} |")
    lines.append(f"| 并行 tab 数 | {CONCURRENCY} |")
    lines.append(f"| 搜索耗时 | {search_time:.1f}s |")
    lines.append(f"| 详情耗时 | {detail_time:.1f}s |")
    lines.append(f"| 总耗时 | {total_time:.1f}s |")
    lines.append(f"| 平均每条详情 | {detail_time/detail_count:.1f}s（并行）|")
    lines.append("")

    lines.append("---\n")

    for i, n in enumerate(notes[:detail_count]):
        score = n.comments_count * 5 + n.collected * 2 + n.likes
        lines.append(f"## {i+1}. {n.title}\n")
        lines.append(f"| 指标 | 数值 |")
        lines.append(f"|------|------|")
        lines.append(f"| 👍 点赞 | {n.likes:,} |")
        lines.append(f"| ⭐ 收藏 | {n.collected:,} |")
        lines.append(f"| 💬 评论 | {n.comments_count:,} |")
        lines.append(f"| 综合分 | {score:,} |")
        lines.append(f"| 作者 | {n.author} |")
        lines.append(f"| 链接 | {n.url} |")
        if n.image_urls:
            lines.append(f"| 📷 图片数 | {len(n.image_urls)} |")
        lines.append("")

        if n.content:
            # 截取前200字作为摘要
            summary = n.content[:200].replace("\n", " ").strip()
            if len(n.content) > 200:
                summary += "..."
            lines.append(f"**正文摘要：**\n")
            lines.append(f"{summary}\n")

        if n.top_comments:
            lines.append(f"**高赞评论：**")
            for c in n.top_comments[:3]:
                lines.append(f"- [{c['likes']}赞] {c['text'][:80]}")
            lines.append("")

        lines.append("---\n")

    # 剩余结果（无详情）简表
    remaining = notes[detail_count:]
    if remaining:
        lines.append(f"## 其余 {len(remaining)} 条搜索结果（仅互动数据）\n")
        lines.append(f"| # | 标题 | 👍 | ⭐ | 💬 | 综合分 | 作者 |")
        lines.append(f"|---|------|-----|-----|-----|--------|------|")
        for i, n in enumerate(remaining):
            score = n.comments_count * 5 + n.collected * 2 + n.likes
            title_short = n.title[:30] + ("..." if len(n.title) > 30 else "")
            lines.append(f"| {detail_count+i+1} | {title_short} | {n.likes:,} | {n.collected:,} | {n.comments_count:,} | {score:,} | {n.author} |")
        lines.append("")

    return "\n".join(lines)



async def main():
    from playwright.async_api import async_playwright
    import random

    query = sys.argv[1] if len(sys.argv) > 1 else "agent开发"
    print(f"{'='*60}")
    print(f"小红书并行搜索 POC")
    print(f"关键词: {query} | 并行: {CONCURRENCY} tab | 详情: top {DETAIL_TOP_K}")
    print(f"{'='*60}")

    if not COOKIE_FILE.exists():
        print("Cookie 不存在，请先登录:")
        print("  venv\\Scripts\\python.exe scripts/poc_browser_search.py --login")
        return

    cookies = json.loads(COOKIE_FILE.read_text(encoding="utf-8"))
    print(f"Cookie: {len(cookies)} 条")

    total_start = time.time()

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            args=["--disable-blink-features=AutomationControlled"]
        )
        ctx = await browser.new_context(
            viewport={"width": 1280, "height": 900},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
            locale="zh-CN",
        )
        await ctx.add_init_script("Object.defineProperty(navigator,'webdriver',{get:()=>undefined})")
        await ctx.add_cookies(cookies)

        # ========== 阶段 1: 搜索 ==========
        search_start = time.time()
        page = await ctx.new_page()
        page.set_default_timeout(20000)
        page.on("response", on_search_response)

        url = f"https://www.xiaohongshu.com/search_result?keyword={quote(query)}&source=web_search_result_note"
        print(f"\n[阶段1] 搜索...")
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=20000)
        except Exception as e:
            print(f"  页面加载异常: {e}")
        await asyncio.sleep(4)

        if "search_result" not in page.url:
            print("  ⚠ Cookie 过期，需要重新登录")
            await browser.close()
            return

        # 滚动加载
        for i in range(6):
            await page.evaluate("window.scrollBy(0, 800)")
            await asyncio.sleep(random.uniform(1.5, 2.5))

        await page.close()
        search_time = time.time() - search_start
        print(f"  搜索完成: {len(search_items)} 条, {search_time:.1f}s")

        # 解析 + 去重 + 排序
        notes = []
        seen = set()
        for item in search_items:
            nc = item.get("note_card", {})
            if not nc:
                continue
            nid = nc.get("note_id", item.get("id", ""))
            if nid in seen:
                continue
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
                share_count=int(interact.get("share_count", 0) or 0),
                xsec_token=xt,
            )
            notes.append(n)

        notes.sort(key=lambda n: n.comments_count * 5 + n.collected * 2 + n.likes, reverse=True)
        total_count = len(notes)
        print(f"  去重后 {total_count} 条")

        # ========== 阶段 2: 并行详情 ==========
        detail_count = min(DETAIL_TOP_K, total_count)
        print(f"\n[阶段2] 并行获取 top {detail_count} 详情 ({CONCURRENCY} tab)...")
        detail_start = time.time()

        sem = asyncio.Semaphore(CONCURRENCY)
        tasks = [
            fetch_single_detail(ctx, note, i, detail_count, sem)
            for i, note in enumerate(notes[:detail_count])
        ]
        await asyncio.gather(*tasks)

        detail_time = time.time() - detail_start
        total_time = time.time() - total_start

        # 保存 cookie
        new_cookies = await ctx.cookies()
        COOKIE_FILE.write_text(json.dumps(new_cookies, ensure_ascii=False, indent=2), encoding="utf-8")
        await browser.close()

    # ========== 输出 ==========
    print(f"\n{'='*60}")
    print(f"完成!")
    print(f"  搜索: {total_count} 条, {search_time:.1f}s")
    print(f"  详情: {detail_count} 条, {detail_time:.1f}s (并行 {CONCURRENCY} tab)")
    print(f"  总耗时: {total_time:.1f}s")
    has_content = sum(1 for n in notes[:detail_count] if n.content)
    has_comments = sum(1 for n in notes[:detail_count] if n.top_comments)
    has_images = sum(1 for n in notes[:detail_count] if n.image_urls)
    print(f"  正文: {has_content}/{detail_count} | 评论: {has_comments}/{detail_count} | 图片: {has_images}/{detail_count}")
    print(f"{'='*60}")

    # 保存 JSON
    out = [asdict(n) for n in notes]
    Path("scripts/xhs_parallel_results.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    # 生成 MD 报告
    report = generate_report(notes, query, total_count, search_time, detail_time, total_time, detail_count)
    Path("scripts/xhs_parallel_report.md").write_text(report, encoding="utf-8")
    print(f"\n结果: scripts/xhs_parallel_results.json")
    print(f"报告: scripts/xhs_parallel_report.md")


if __name__ == "__main__":
    asyncio.run(main())
