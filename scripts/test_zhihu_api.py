"""测试知乎搜索 — 直接从搜索页 DOM 提取结果（不需要登录）"""
import asyncio
import json
import re
from pathlib import Path

from playwright.async_api import async_playwright

PROJECT_ROOT = Path(__file__).resolve().parent.parent
STEALTH_JS = PROJECT_ROOT / "scripts" / "MediaCrawler" / "libs" / "stealth.min.js"


async def main():
    print("1. 启动浏览器...")
    async with async_playwright() as pw:
        ctx = await pw.chromium.launch_persistent_context(
            user_data_dir=str(PROJECT_ROOT / "browser_data" / "zhihu_test3"),
            headless=True,
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                       "(KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
        )
        if STEALTH_JS.exists():
            await ctx.add_init_script(path=str(STEALTH_JS))

        page = await ctx.new_page()

        print("2. 访问知乎搜索页...")
        await page.goto("https://www.zhihu.com/search?q=agent&type=content",
                        wait_until="networkidle", timeout=30000)
        await page.wait_for_timeout(3000)

        # 尝试从 js-initialData 提取
        print("3. 尝试从 js-initialData 提取...")
        init_data = await page.evaluate("""() => {
            const el = document.getElementById('js-initialData');
            return el ? el.textContent : null;
        }""")

        if init_data:
            data = json.loads(init_data)
            # 看看数据结构
            entities = data.get("initialState", {}).get("entities", {})
            search = data.get("initialState", {}).get("search", {})
            print(f"   entities keys: {list(entities.keys())[:10]}")
            print(f"   search keys: {list(search.keys())[:10]}")

            # 尝试提取搜索结果
            answers = entities.get("answers", {})
            articles = entities.get("articles", {})
            print(f"   answers: {len(answers)}, articles: {len(articles)}")

            for aid, answer in list(answers.items())[:3]:
                title = answer.get("question", {}).get("title", "") if isinstance(answer.get("question"), dict) else ""
                voteup = answer.get("voteupCount", 0)
                comment = answer.get("commentCount", 0)
                excerpt = re.sub(r"<[^>]+>", "", answer.get("excerpt", ""))[:80]
                print(f"   [回答] {title[:50]} | 👍{voteup} 💬{comment}")
                print(f"          {excerpt}")
        else:
            print("   js-initialData 不存在")

        # 方案 B：直接从 DOM 提取搜索卡片
        print("\n4. 从 DOM 提取搜索卡片...")
        cards = await page.evaluate("""() => {
            const items = document.querySelectorAll('.SearchResult-Card, .List-item');
            const results = [];
            items.forEach(item => {
                const titleEl = item.querySelector('h2, .ContentItem-title a');
                const excerptEl = item.querySelector('.RichContent-inner, .content');
                const voteEl = item.querySelector('.VoteButton--up');
                results.push({
                    title: titleEl ? titleEl.textContent.trim() : '',
                    excerpt: excerptEl ? excerptEl.textContent.trim().slice(0, 100) : '',
                    votes: voteEl ? voteEl.textContent.trim() : '',
                });
            });
            return results;
        }""")

        print(f"   DOM 卡片数: {len(cards)}")
        for c in cards[:5]:
            print(f"   - {c['title'][:60]}")
            if c['excerpt']:
                print(f"     {c['excerpt'][:80]}")

        # 看看页面上有没有登录弹窗遮挡
        print("\n5. 检查登录弹窗...")
        modal = await page.query_selector('.Modal-wrapper, .signFlowModal')
        print(f"   登录弹窗: {'有' if modal else '无'}")

        await ctx.close()


asyncio.run(main())
