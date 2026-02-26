"""
POC: 小红书 API 方式搜索测试

用 httpx 直接调用小红书 Web API，跳过浏览器渲染。
复用之前 Playwright 登录保存的 Cookie。

对比浏览器方案：
- 速度更快（纯 HTTP 请求，不需要渲染页面）
- 数据更完整（API 返回结构化 JSON）
- 更稳定（不受前端 CSS 变化影响）

用法:
    venv\Scripts\python.exe scripts/poc_xhs_api.py "GRE 备考"
"""

import httpx
import json
import sys
import time
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
    collected: int = 0       # 收藏数
    comments_count: int = 0  # 评论数
    share_count: int = 0
    content: str = ""
    note_type: str = ""      # normal / video
    top_comments: List[dict] = field(default_factory=list)


def load_cookies() -> dict:
    """从 Playwright 保存的 cookie 文件加载，转换为 httpx 可用的 dict"""
    if not COOKIE_FILE.exists():
        print(f"Cookie 文件不存在: {COOKIE_FILE}")
        print("请先运行 poc_browser_search.py --login 登录一次")
        sys.exit(1)

    raw_cookies = json.loads(COOKIE_FILE.read_text(encoding="utf-8"))
    # Playwright cookie 格式 → 简单 dict {name: value}
    cookies = {}
    for c in raw_cookies:
        cookies[c["name"]] = c["value"]
    print(f"已加载 {len(cookies)} 条 cookie")
    return cookies


def get_headers() -> dict:
    return {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Origin": "https://www.xiaohongshu.com",
        "Referer": "https://www.xiaohongshu.com/",
        "Content-Type": "application/json;charset=UTF-8",
        "Accept": "application/json, text/plain, */*",
    }


def search_notes(query: str, cookies: dict, page: int = 1, page_size: int = 20) -> List[dict]:
    """调用小红书搜索 API"""
    url = "https://edith.xiaohongshu.com/api/sns/web/v1/search/notes"
    payload = {
        "keyword": query,
        "page": page,
        "page_size": page_size,
        "search_id": "",
        "sort": "general",       # general=综合, time_descending=最新, popularity_descending=最热
        "note_type": 0,          # 0=全部, 1=图文, 2=视频
    }

    with httpx.Client(cookies=cookies, headers=get_headers(), timeout=15) as client:
        resp = client.post(url, json=payload)
        print(f"  搜索 API 状态码: {resp.status_code}")

        if resp.status_code != 200:
            print(f"  响应: {resp.text[:500]}")
            return []

        data = resp.json()
        if data.get("code") != 0 and data.get("success") is not True:
            print(f"  API 返回错误: {data.get('msg', data.get('code', 'unknown'))}")
            # 打印完整响应帮助调试
            print(f"  完整响应: {json.dumps(data, ensure_ascii=False)[:800]}")
            return []

        items = data.get("data", {}).get("items", [])
        print(f"  搜索到 {len(items)} 条结果")
        return items


def get_note_detail(note_id: str, cookies: dict, xsec_token: str = "") -> Optional[dict]:
    """获取笔记详情"""
    url = "https://edith.xiaohongshu.com/api/sns/web/v1/feed"
    payload = {
        "source_note_id": note_id,
        "image_formats": ["jpg", "webp", "avif"],
        "extra": {"need_body_topic": 1},
        "xsec_source": "pc_search",
        "xsec_token": xsec_token,
    }

    with httpx.Client(cookies=cookies, headers=get_headers(), timeout=15) as client:
        resp = client.post(url, json=payload)
        if resp.status_code != 200:
            print(f"    详情 API 失败: {resp.status_code}")
            return None

        data = resp.json()
        if data.get("code") != 0 and data.get("success") is not True:
            print(f"    详情 API 错误: {data.get('msg', 'unknown')}")
            return None

        items = data.get("data", {}).get("items", [])
        if items:
            return items[0].get("note_card", {})
        return None


def get_comments(note_id: str, cookies: dict, xsec_token: str = "", cursor: str = "") -> List[dict]:
    """获取笔记评论（按热度排序）"""
    url = "https://edith.xiaohongshu.com/api/sns/web/v2/comment/page"
    params = {
        "note_id": note_id,
        "cursor": cursor,
        "top_comment_id": "",
        "image_formats": "jpg,webp,avif",
        "xsec_source": "pc_search",
        "xsec_token": xsec_token,
    }

    with httpx.Client(cookies=cookies, headers=get_headers(), timeout=15) as client:
        resp = client.get(url, params=params)
        if resp.status_code != 200:
            print(f"    评论 API 失败: {resp.status_code}")
            return []

        data = resp.json()
        if data.get("code") != 0 and data.get("success") is not True:
            print(f"    评论 API 错误: {data.get('msg', 'unknown')}")
            return []

        return data.get("data", {}).get("comments", [])


def parse_search_item(item: dict) -> Optional[XhsNote]:
    """解析搜索结果中的单条笔记"""
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
        url=f"https://www.xiaohongshu.com/explore/{note_id}",
        author=user.get("nickname", ""),
        author_id=user.get("user_id", ""),
        likes=int(interact.get("liked_count", "0")),
        collected=int(interact.get("collected_count", "0")),
        comments_count=int(interact.get("comment_count", "0")),
        share_count=int(interact.get("share_count", "0")),
        note_type=note_card.get("type", ""),
    ), xsec_token


def parse_detail(detail: dict, note: XhsNote) -> XhsNote:
    """用详情数据补充笔记信息"""
    # 正文
    desc = detail.get("desc", "")
    if desc:
        note.content = desc[:800]

    # 更精确的互动数据
    interact = detail.get("interact_info", {})
    if interact:
        note.likes = int(interact.get("liked_count", note.likes))
        note.collected = int(interact.get("collected_count", note.collected))
        note.comments_count = int(interact.get("comment_count", note.comments_count))
        note.share_count = int(interact.get("share_count", note.share_count))

    return note


def parse_comments(raw_comments: List[dict]) -> List[dict]:
    """解析评论列表，提取文本和点赞数，按赞数排序"""
    parsed = []
    for c in raw_comments:
        text = c.get("content", "")
        likes = int(c.get("like_count", 0))
        user = c.get("user_info", {})
        author = user.get("nickname", "")

        if text and len(text) > 2:
            parsed.append({
                "text": text[:300],
                "likes": likes,
                "author": author,
            })

    # 按赞数降序
    parsed.sort(key=lambda x: x["likes"], reverse=True)
    return parsed[:10]


def main():
    query = sys.argv[1] if len(sys.argv) > 1 else "GRE 备考"

    print("=" * 60)
    print(f"小红书 API 搜索 POC")
    print(f"搜索关键词: {query}")
    print("=" * 60)

    cookies = load_cookies()
    start = time.time()

    # 1. 搜索
    print(f"\n[1] 搜索笔记...")
    raw_items = search_notes(query, cookies)

    if not raw_items:
        print("搜索失败，可能 Cookie 已过期，请重新登录")
        return

    # 2. 解析搜索结果
    print(f"\n[2] 解析搜索结果...")
    notes = []
    tokens = {}  # note_id → xsec_token
    for item in raw_items:
        result = parse_search_item(item)
        if result:
            note, xsec_token = result
            notes.append(note)
            tokens[note.note_id] = xsec_token
            print(f"  [{len(notes)}] {note.title[:50]}  👍{note.likes} ⭐{note.collected} 💬{note.comments_count}")

    # 3. 获取前 5 条的详情和评论
    detail_count = min(5, len(notes))
    print(f"\n[3] 获取前 {detail_count} 条详情和评论...")

    for i, note in enumerate(notes[:detail_count]):
        print(f"\n  --- [{i+1}/{detail_count}] {note.title[:30]} ---")
        xsec_token = tokens.get(note.note_id, "")

        # 详情
        detail = get_note_detail(note.note_id, cookies, xsec_token)
        if detail:
            note = parse_detail(detail, note)
            print(f"  正文: {note.content[:80]}..." if note.content else "  正文: (无)")
            print(f"  👍{note.likes} ⭐{note.collected} 💬{note.comments_count} 🔗{note.share_count}")
        else:
            print(f"  详情获取失败")

        # 评论
        raw_comments = get_comments(note.note_id, cookies, xsec_token)
        if raw_comments:
            note.top_comments = parse_comments(raw_comments)
            print(f"  高赞评论 ({len(note.top_comments)} 条):")
            for c in note.top_comments[:3]:
                print(f"    [{c['likes']}赞] {c['text'][:60]}  —{c['author']}")
        else:
            print(f"  评论获取失败")

        notes[i] = note

    elapsed = time.time() - start

    # 4. 按价值排序
    notes.sort(key=lambda n: n.comments_count * 3 + n.collected * 2 + n.likes, reverse=True)

    # 5. 输出结果
    print(f"\n{'=' * 60}")
    print(f"完成! 耗时 {elapsed:.1f}s, {len(notes)} 条结果")
    print(f"排序: 评论数×3 + 收藏数×2 + 点赞数")
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

    # 保存 JSON
    output_path = "scripts/xhs_api_results.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump([asdict(n) for n in notes], f, ensure_ascii=False, indent=2)
    print(f"\n结果已保存到 {output_path}")


if __name__ == "__main__":
    main()
