"""
XLearning Agent - UI Renderer
==============================
Handles: Chat Tab, Trace Tab, Quiz Tab, Report Tab rendering
Strictly compatible with Streamlit 1.12.0.
"""

import html
import re

import streamlit as st
from src.ui.state import (
    t, get_current_messages, add_message, 
    create_new_session
)

# ============================================================================
# Constants
# ============================================================================

MAX_VISIBLE_MESSAGES = 20  # Performance: Fold old messages

AGENT_AVATARS = {
    "user": "🧑",
    "planner": "📋",
    "tutor": "🎓",
    "validator": "✅"
}


def _sanitize_message_content(content: str) -> str:
    """清理消息中的 HTML 标签碎片，避免破坏气泡结构。"""
    if not content:
        return ""
    cleaned = re.sub(r"</?div[^>]*>", "", content, flags=re.IGNORECASE)
    cleaned = re.sub(r"</?span[^>]*>", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"</?p[^>]*>", "", cleaned, flags=re.IGNORECASE)
    return cleaned.strip()


def _markdown_to_html(text: str) -> str:
    """
    将 Markdown 文本转换为 HTML（内置实现，零依赖）。
    
    支持: ### 标题, **粗体**, *斜体*, `代码`, ---, 无序列表, 有序列表, 段落,
    ``` 代码块 ```, > 引用
    """
    if not text:
        return ""

    def _inline(line: str) -> str:
        """处理行内格式：**粗体**, *斜体*, `代码`"""
        line = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', line)
        line = re.sub(r'__(.+?)__', r'<strong>\1</strong>', line)
        line = re.sub(r'(?<!\*)\*([^*]+?)\*(?!\*)', r'<em>\1</em>', line)
        line = re.sub(r'`([^`]+?)`', r'<code>\1</code>', line)
        return line

    lines = text.split('\n')
    parts = []
    in_ul = False
    in_ol = False
    in_code = False
    code_lines = []

    for raw_line in lines:
        stripped = raw_line.strip()

        # --- 代码块 ---
        if stripped.startswith('```'):
            if in_code:
                parts.append('<pre class="chat-code-block"><code>' + html.escape('\n'.join(code_lines)) + '</code></pre>')
                code_lines = []
                in_code = False
            else:
                if in_ul:
                    parts.append('</ul>')
                    in_ul = False
                if in_ol:
                    parts.append('</ol>')
                    in_ol = False
                in_code = True
                lang = stripped[3:].strip()
                if lang:
                    code_lines = []  # 首行语言标识不放入内容
            continue
        if in_code:
            code_lines.append(raw_line)
            continue

        # --- 空行 ---
        if not stripped:
            if in_ul:
                parts.append('</ul>')
                in_ul = False
            if in_ol:
                parts.append('</ol>')
                in_ol = False
            continue

        # --- 水平分隔线 ---
        if stripped in ('---', '***', '___', '- - -', '* * *'):
            if in_ul:
                parts.append('</ul>')
                in_ul = False
            if in_ol:
                parts.append('</ol>')
                in_ol = False
            parts.append('<hr>')
            continue

        # --- 引用 > ---
        if stripped.startswith('> '):
            if in_ul:
                parts.append('</ul>')
                in_ul = False
            if in_ol:
                parts.append('</ol>')
                in_ol = False
            parts.append(f'<blockquote class="chat-blockquote">{_inline(stripped[2:])}</blockquote>')
            continue

        # --- 标题 ---
        heading_match = re.match(r'^(#{1,3})\s+(.+)$', stripped)
        if heading_match:
            if in_ul:
                parts.append('</ul>')
                in_ul = False
            if in_ol:
                parts.append('</ol>')
                in_ol = False
            level = len(heading_match.group(1))
            content = _inline(heading_match.group(2))
            parts.append(f'<h{level}>{content}</h{level}>')
            continue

        # --- 无序列表 ---
        if stripped.startswith('- ') or stripped.startswith('* '):
            if in_ol:
                parts.append('</ol>')
                in_ol = False
            if not in_ul:
                parts.append('<ul>')
                in_ul = True
            item_text = _inline(stripped[2:])
            parts.append(f'<li>{item_text}</li>')
            continue

        # --- 有序列表 ---
        ol_match = re.match(r'^(\d+)\.\s+(.+)$', stripped)
        if ol_match:
            if in_ul:
                parts.append('</ul>')
                in_ul = False
            if not in_ol:
                parts.append('<ol>')
                in_ol = True
            item_text = _inline(ol_match.group(2))
            parts.append(f'<li>{item_text}</li>')
            continue

        # --- 普通段落 ---
        if in_ul:
            parts.append('</ul>')
            in_ul = False
        if in_ol:
            parts.append('</ol>')
            in_ol = False
        parts.append(f'<p>{_inline(stripped)}</p>')

    if in_code and code_lines:
        parts.append('<pre class="chat-code-block"><code>' + html.escape('\n'.join(code_lines)) + '</code></pre>')
    if in_ul:
        parts.append('</ul>')
    if in_ol:
        parts.append('</ol>')

    return '\n'.join(parts)


# ============================================================================
# Chat Tab
# ============================================================================

def render_chat_tab():
    """Render the Chat tab with messages and input."""
    
    # Check if we have a session
    if not st.session_state.current_session_id:
        from src.ui.layout import render_home_view
        render_home_view()
        return
    
    messages = get_current_messages()
    
    # ===== Message Rendering Wrap (Scrollable Anchor) =====
    st.markdown('<div class="chat-anchor"></div>', unsafe_allow_html=True)
    
    # ===== Empty Session State =====
    if not messages:
        pass 
    else:
        # ===== Message Rendering with Folding =====
        total = len(messages)
        if total > MAX_VISIBLE_MESSAGES:
            hidden_count = total - MAX_VISIBLE_MESSAGES
            with st.expander(f"📜 {t('earlier_messages')} ({hidden_count})"):
                for msg in messages[:hidden_count]:
                    _render_message(msg)
            for msg in messages[hidden_count:]:
                _render_message(msg)
        else:
            for msg in messages:
                _render_message(msg)
    
    # ===== Chat Input =====
    _render_chat_input()

def _render_message(msg: dict):
    """消息渲染：外层白框气泡，用户纯文本，Agent 用 Markdown→HTML。"""
    
    role = msg.get("role", "assistant")
    agent = msg.get("agent")
    content = msg.get("content", "")
    citations = msg.get("citations", [])
    status = msg.get("status", "complete")
    error = msg.get("error")
    
    if role == "user":
        avatar = AGENT_AVATARS["user"]
        bubble_class = "user-bubble"
    elif role == "system":
        avatar = "⚙️"
        bubble_class = "system-bubble"
    else:
        avatar = AGENT_AVATARS.get(agent, "🤖")
        bubble_class = "assistant-bubble"
    
    role_label = "你" if role == "user" else ("系统" if role == "system" else (agent.upper() if agent else "ASSISTANT"))
    
    if status == "streaming":
        content = content + "\n\n..."
    
    # ---- 渲染内容 ----
    if role == "user":
        # 用户消息：纯文本转义
        safe_text = _sanitize_message_content(content)
        safe_text = re.sub(r"<[^>]+>", "", safe_text)
        body_html = html.escape(safe_text or "").replace("\n", "<br>")
    else:
        # Agent / System 消息：Markdown → HTML
        safe_text = _sanitize_message_content(content)
        body_html = _markdown_to_html(safe_text)
        # 安全：移除 script 标签
        body_html = re.sub(r"<script[^>]*>.*?</script>", "", body_html, flags=re.DOTALL | re.IGNORECASE)
    
    html_block = f"""
    <div class="chat-row">
        <div class="avatar-icon">{avatar}</div>
        <div class="chat-bubble {bubble_class}">
            <div class="chat-bubble-header">{role_label}</div>
            <div class="chat-bubble-body">{body_html}</div>
        </div>
    </div>
    """
    st.markdown(html_block, unsafe_allow_html=True)
    
    # For complex elements like citations or errors, use Streamlit components below the bubble
    if status == "error":
        st.error("操作失败")
        if error:
            with st.expander("错误详情"):
                st.code(error)
    
    if citations:
        with st.expander(f"{t('evidence')} ({len(citations)})"):
            for c in citations:
                source = c.get("source", "Unknown")
                snippet = c.get("snippet", "")
                page = c.get("page", "")
                st.markdown(f"**{source}** {f'(p.{page})' if page else ''}")
                st.caption(f"_{snippet}_")

def _render_chat_input():
    """Render the chat input area at the bottom（GPT 风格：Enter 发送）。"""
    
    if st.session_state.is_processing:
        if st.button(t("stop"), key="stop_btn"):
            st.session_state.stop_requested = True
            st.experimental_rerun()
    
    st.markdown('<div class="chat-input-wrap">', unsafe_allow_html=True)

    if st.session_state.get("clear_chat_input", False):
        st.session_state.chat_input_val = ""
        st.session_state.clear_chat_input = False

    if "chat_input_val" not in st.session_state:
        st.session_state.chat_input_val = ""

    if not st.session_state.is_processing:
        # 使用 text_input：Enter 直接发送（类似 ChatGPT 体验）
        user_input = st.text_input(
            label=" ",
            placeholder=t("chat_placeholder"),
            key="chat_input_val",
        )
        if user_input and user_input.strip():
            from src.ui.logic import handle_chat_input
            handle_chat_input(user_input, should_rerun=False)
            st.session_state.clear_chat_input = True
            st.experimental_rerun()
    else:
        st.info("🕒 Agent 正在思考中，请稍候...")
    
    st.markdown("</div>", unsafe_allow_html=True)


# ============================================================================
# Plan Panel（规划阶段右侧面板）
# ============================================================================

def _extract_plan_from_messages(messages: list) -> tuple:
    """从消息列表中提取最新计划内容。返回 (plan_md, phases_preview)。"""
    plan_md = ""
    phases = []
    for msg in reversed(messages):
        if msg.get("role") != "assistant":
            continue
        content = msg.get("content", "")
        if "计划" in content and ("阶段" in content or "##" in content or "###" in content):
            plan_md = content
            phases = _parse_phases(content)
            break
    return plan_md, phases[:6]


def _extract_phases_from_text(text: str) -> tuple:
    """从单条计划文本中提取阶段列表。返回 (plan_md, phases_preview)。"""
    phases = _parse_phases(text)
    return text, phases[:6]


def _parse_phases(content: str) -> list:
    """从计划文本中解析阶段标题列表。"""
    phases = []
    for line in content.split("\n"):
        s = line.strip()
        if re.search(r"阶段\s*\d", s) or (s.startswith("##") and "阶段" in s):
            title = re.sub(r"^#{1,3}\s*", "", s)
            title = re.sub(r"^[⬜✓●]\s*", "", title)
            if title and len(phases) < 6:
                phases.append(title[:50])
    if not phases:
        for line in content.split("\n"):
            s = line.strip()
            if re.match(r"^#{2,3}\s+", s):
                phases.append(re.sub(r"^#{2,3}\s*", "", s)[:50])
            if len(phases) >= 6:
                break
    return phases


def _parse_daily_plan(content: str) -> list:
    """
    从计划 Markdown 中解析出按天的结构化数据。

    返回: [{"day": 1, "title": "项目初探", "tasks": [...], "resources": [...], "outcomes": [...], "preview": "..."}]
    """
    days = []
    lines = content.split("\n")
    current_day = None
    current_section = None  # 'tasks' | 'resources' | 'outcomes'

    for line in lines:
        s = line.strip()

        # 匹配 Day 标题: ### 📅 第X天：XXX 或 ### 📅 Day X: XXX
        day_match = re.match(r'^#{2,3}\s*📅?\s*第?\s*(\d+)\s*天[：:]\s*(.+)', s)
        if not day_match:
            day_match = re.match(r'^#{2,3}\s*📅?\s*Day\s*(\d+)[：:]\s*(.+)', s, re.IGNORECASE)
        if not day_match:
            # 也匹配 "⬜ 阶段 X: ..." 格式
            day_match = re.match(r'^#{2,3}\s*[⬜✓●]?\s*阶段\s*(\d+)[：:]\s*(.+)', s)

        if day_match:
            if current_day:
                days.append(current_day)
            day_num = int(day_match.group(1))
            title = day_match.group(2).strip()
            # 清理标题中的天数标注 (3 天) 等
            title = re.sub(r'\s*[\(（]\d+\s*天[\)）]', '', title)
            current_day = {
                "day": day_num,
                "title": title,
                "tasks": [],
                "resources": [],
                "outcomes": [],
                "preview": "",
            }
            current_section = "tasks"
            continue

        if not current_day:
            continue

        # 检测 section 切换
        if re.match(r'^\*\*任务\*\*|^-\s*\*\*任务\*\*|^任务', s):
            current_section = "tasks"
            continue
        if re.match(r'^\*\*资源\*\*|^-\s*\*\*资源\*\*|^\*\*推荐资源|^资源', s):
            current_section = "resources"
            continue
        if re.match(r'^\*\*收获\*\*|^\*\*目标\*\*|^\*\*验收\*\*|^收获|^目标', s):
            current_section = "outcomes"
            continue

        # 收集列表项（支持 `- item` 和 `  - sub-item` 缩进格式）
        item_match = re.match(r'^\s*[-*]\s+(.+)', s)
        if item_match and current_section:
            item_text = item_match.group(1).strip()
            # 去掉 markdown 加粗
            item_text = re.sub(r'\*\*(.+?)\*\*', r'\1', item_text)
            # 跳过 section 标签本身（如 "任务："）
            if item_text in ("任务：", "资源：", "收获：", "目标：", "验收："):
                continue
            if current_section == "tasks":
                current_day["tasks"].append(item_text)
            elif current_section == "resources":
                current_day["resources"].append(item_text)
            elif current_section == "outcomes":
                current_day["outcomes"].append(item_text)

    if current_day:
        days.append(current_day)

    # 如果没有解析到 day 格式，回退到 phase 格式
    if not days:
        phases = _parse_phases(content)
        for i, p in enumerate(phases, 1):
            days.append({
                "day": i,
                "title": p,
                "tasks": [],
                "resources": [],
                "outcomes": [],
                "preview": "",
            })

    # 为每个 day 添加 preview（下一天的标题）
    for i in range(len(days) - 1):
        days[i]["preview"] = f"明日预告：{days[i+1]['title']}"
    if days:
        days[-1]["preview"] = "🎉 恭喜完成全部学习计划！"

    return days


def _render_timeline(days: list, completed: dict, title: str = "学习计划"):
    """渲染交互式菱形时间线组件（5天视窗 + 左右箭头滑动）。

    Args:
        days: _parse_daily_plan 返回的结构化数据
        completed: {day_num: True/False} 完成状态字典
        title: 计划标题
    """
    import json
    import streamlit.components.v1 as components

    max_days = min(len(days), 14)
    display_days = days[:max_days]

    days_json = json.dumps(display_days, ensure_ascii=False)
    completed_json = json.dumps({str(k): v for k, v in completed.items()})
    safe_title = html.escape(title)
    visible_count = min(5, len(display_days))

    timeline_html = f"""
    <style>
      .tl-wrap {{ font-family: 'Inter', -apple-system, sans-serif; padding: 16px 8px; user-select: none; }}
      .tl-title {{ text-align: center; font-size: 15px; font-weight: 700; color: #1F2937; margin-bottom: 20px; }}
      /* 导航行：箭头 + 轨道 */
      .tl-nav {{ display: flex; align-items: center; justify-content: center; gap: 8px; }}
      .tl-arrow {{
        width: 32px; height: 32px; border-radius: 50%;
        border: 1px solid #D1D5DB; background: #F9FAFB;
        display: flex; align-items: center; justify-content: center;
        cursor: pointer; font-size: 14px; color: #6B7280;
        transition: all 0.15s; flex-shrink: 0;
      }}
      .tl-arrow:hover {{ background: #F3F4F6; border-color: #F97316; color: #F97316; }}
      .tl-arrow.disabled {{ opacity: 0.3; cursor: default; pointer-events: none; }}
      .tl-viewport {{ overflow: hidden; }}
      .tl-track {{ display: flex; align-items: center; gap: 0; transition: transform 0.3s ease; }}
      .tl-node-group {{ display: flex; align-items: center; }}
      .tl-diamond {{
        width: 44px; height: 44px;
        background: #F3F4F6; border: 2px solid #D1D5DB;
        transform: rotate(45deg);
        display: flex; align-items: center; justify-content: center;
        cursor: pointer; transition: all 0.25s ease;
        flex-shrink: 0; border-radius: 4px;
      }}
      .tl-diamond:hover {{ border-color: #F97316; background: #FFF7ED; box-shadow: 0 0 12px rgba(249,115,22,0.25); }}
      .tl-diamond.active {{ border-color: #F97316; background: #FFF7ED; box-shadow: 0 0 16px rgba(249,115,22,0.3); }}
      .tl-diamond.done {{ border-color: #22C55E; background: #F0FDF4; }}
      .tl-diamond.done:hover {{ box-shadow: 0 0 12px rgba(34,197,94,0.3); }}
      .tl-diamond-text {{
        transform: rotate(-45deg);
        font-size: 11px; font-weight: 700; color: #6B7280;
        pointer-events: none; white-space: nowrap;
      }}
      .tl-diamond.done .tl-diamond-text {{ color: #16A34A; }}
      .tl-diamond.active .tl-diamond-text {{ color: #EA580C; }}
      .tl-connector {{
        width: 28px; height: 2px; flex-shrink: 0;
        border-top: 2px dashed #D1D5DB;
      }}
      .tl-connector.done {{ border-top: 2px solid #22C55E; }}
      @keyframes breathe {{ 0%,100% {{ opacity: 0.3; }} 50% {{ opacity: 1; }} }}
      .tl-connector.breathing {{ animation: breathe 2s ease-in-out infinite; border-top-color: #F97316; }}
      /* 页码指示 */
      .tl-page-info {{ text-align: center; font-size: 11px; color: #9CA3AF; margin-top: 8px; }}
      /* 详情卡片 */
      .tl-detail {{
        display: none; margin-top: 16px;
        background: #FFFFFF; border: 1px solid #E5E7EB; border-radius: 12px;
        padding: 20px; box-shadow: 0 4px 16px rgba(0,0,0,0.06);
        animation: fadeIn 0.2s ease;
      }}
      .tl-detail.show {{ display: block; }}
      @keyframes fadeIn {{ from {{ opacity: 0; transform: translateY(-8px); }} to {{ opacity: 1; transform: translateY(0); }} }}
      .tl-detail-title {{ font-size: 16px; font-weight: 700; color: #1F2937; margin-bottom: 14px; display: flex; align-items: center; gap: 8px; }}
      .tl-detail-title .day-badge {{
        background: #F97316; color: #fff; font-size: 11px; font-weight: 600;
        padding: 2px 8px; border-radius: 10px;
      }}
      .tl-section {{ margin-bottom: 12px; }}
      .tl-section-label {{ font-size: 12px; font-weight: 600; color: #9CA3AF; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 6px; }}
      .tl-section-list {{ list-style: none; padding: 0; margin: 0; }}
      .tl-section-list li {{ font-size: 13px; color: #374151; padding: 3px 0; padding-left: 16px; position: relative; line-height: 1.5; }}
      .tl-section-list li::before {{ content: '•'; position: absolute; left: 4px; color: #F97316; font-weight: bold; }}
      .tl-section-list.res li::before {{ content: '📎'; left: 0; }}
      .tl-preview {{ font-size: 12px; color: #6B7280; font-style: italic; padding: 8px 12px; background: #F9FAFB; border-radius: 8px; border-left: 3px solid #F97316; }}
      .tl-complete-btn {{
        margin-top: 14px; padding: 8px 20px;
        background: #22C55E; color: #fff; border: none; border-radius: 8px;
        font-size: 13px; font-weight: 600; cursor: pointer;
        transition: all 0.2s;
      }}
      .tl-complete-btn:hover {{ background: #16A34A; }}
      .tl-complete-btn.completed {{ background: #E5E7EB; color: #9CA3AF; cursor: default; }}
      .tl-close-btn {{
        float: right; background: none; border: none; font-size: 18px;
        color: #9CA3AF; cursor: pointer; padding: 0 4px; line-height: 1;
      }}
      .tl-close-btn:hover {{ color: #374151; }}
    </style>
    <div class="tl-wrap">
      <div class="tl-title">🎯 {safe_title}</div>
      <div class="tl-nav">
        <div class="tl-arrow" id="tl-prev">◀</div>
        <div class="tl-viewport" id="tl-viewport">
          <div class="tl-track" id="tl-track"></div>
        </div>
        <div class="tl-arrow" id="tl-next">▶</div>
      </div>
      <div class="tl-page-info" id="tl-page-info"></div>
      <div class="tl-detail" id="tl-detail"></div>
    </div>
    <script>
    (function() {{
      const days = {days_json};
      const completed = {completed_json};
      const VISIBLE = {visible_count};
      let viewStart = 0;
      let activeDay = null;
      const track = document.getElementById('tl-track');
      const detail = document.getElementById('tl-detail');
      const prevBtn = document.getElementById('tl-prev');
      const nextBtn = document.getElementById('tl-next');
      const pageInfo = document.getElementById('tl-page-info');

      prevBtn.onclick = () => {{ if (viewStart > 0) {{ viewStart--; render(); }} }};
      nextBtn.onclick = () => {{ if (viewStart + VISIBLE < days.length) {{ viewStart++; render(); }} }};

      function render() {{
        // 箭头状态
        prevBtn.className = 'tl-arrow' + (viewStart <= 0 ? ' disabled' : '');
        nextBtn.className = 'tl-arrow' + (viewStart + VISIBLE >= days.length ? ' disabled' : '');
        // 页码
        const endIdx = Math.min(viewStart + VISIBLE, days.length);
        pageInfo.textContent = days.length > VISIBLE ? ('Day ' + days[viewStart].day + ' - Day ' + days[endIdx-1].day + '  (' + days.length + ' 天)') : '';

        // 渲染可见节点
        track.innerHTML = '';
        const visibleDays = days.slice(viewStart, viewStart + VISIBLE);
        visibleDays.forEach((d, i) => {{
          const globalIdx = viewStart + i;
          const isDone = completed[String(d.day)] === true;
          const isActive = activeDay === d.day;
          if (i > 0) {{
            const conn = document.createElement('div');
            conn.className = 'tl-connector';
            const prevDay = days[globalIdx - 1];
            const prevDone = completed[String(prevDay.day)] === true;
            if (prevDone && isDone) conn.classList.add('done');
            else if (prevDone && !isDone) conn.classList.add('breathing');
            track.appendChild(conn);
          }}
          const group = document.createElement('div');
          group.className = 'tl-node-group';
          const diamond = document.createElement('div');
          diamond.className = 'tl-diamond' + (isDone ? ' done' : '') + (isActive ? ' active' : '');
          diamond.innerHTML = '<span class="tl-diamond-text">D' + d.day + '</span>';
          diamond.onclick = () => {{ activeDay = (activeDay === d.day) ? null : d.day; render(); }};
          group.appendChild(diamond);
          track.appendChild(group);
        }});

        // 详情卡片
        if (activeDay !== null) {{
          const d = days.find(x => x.day === activeDay);
          if (!d) {{ detail.className = 'tl-detail'; return; }}
          const isDone = completed[String(d.day)] === true;
          let h = '<button class="tl-close-btn" onclick="document.getElementById(\\'tl-detail\\').className=\\'tl-detail\\'">&times;</button>';
          h += '<div class="tl-detail-title"><span class="day-badge">Day ' + d.day + '</span>' + escHtml(d.title) + '</div>';
          if (d.tasks.length) {{
            h += '<div class="tl-section"><div class="tl-section-label">📝 今日学习内容</div><ul class="tl-section-list">';
            d.tasks.forEach(t => {{ h += '<li>' + escHtml(t) + '</li>'; }});
            h += '</ul></div>';
          }}
          if (d.resources.length) {{
            h += '<div class="tl-section"><div class="tl-section-label">📚 学习资料推荐</div><ul class="tl-section-list res">';
            d.resources.forEach(r => {{ h += '<li>' + escHtml(r) + '</li>'; }});
            h += '</ul></div>';
          }}
          if (d.outcomes.length) {{
            h += '<div class="tl-section"><div class="tl-section-label">🎯 验收标准</div><ul class="tl-section-list">';
            d.outcomes.forEach(o => {{ h += '<li>' + escHtml(o) + '</li>'; }});
            h += '</ul></div>';
          }}
          if (d.preview) {{
            h += '<div class="tl-preview">' + escHtml(d.preview) + '</div>';
          }}
          const btnLabel = isDone ? '✅ 已完成' : '✅ 标记完成';
          const btnClass = isDone ? 'tl-complete-btn completed' : 'tl-complete-btn';
          h += '<button class="' + btnClass + '" id="tl-done-btn" data-day="' + d.day + '">' + btnLabel + '</button>';
          detail.innerHTML = h;
          detail.className = 'tl-detail show';
          const btn = document.getElementById('tl-done-btn');
          if (btn && !isDone) {{
            btn.onclick = () => {{
              completed[String(d.day)] = true;
              const msg = JSON.stringify({{type: 'day_complete', day: d.day}});
              window.parent.postMessage({{type: 'streamlit:setComponentValue', value: msg}}, '*');
              render();
            }};
          }}
        }} else {{
          detail.className = 'tl-detail';
        }}
      }}
      function escHtml(s) {{
        const d = document.createElement('div');
        d.textContent = s;
        return d.innerHTML;
      }}
      render();
    }})();
    </script>
    """

    # 高度：轨道区 ~100 + 详情卡片充足空间 ~500
    components.html(timeline_html, height=620, scrolling=True)


def render_plan_panel():
    """规划面板：学习资料 + 交互式时间线路线图 + 学习大纲 + 下载。"""
    if not st.session_state.current_session:
        st.info("请先开始一个学习会话。")
        return

    # ===== 学习资料 =====
    kb_info = st.session_state.kb_info
    if kb_info.get("source"):
        st.markdown("#### 📄 学习资料")
        st.success(f"**{kb_info['source']}**")
        st.caption(f"已索引 {kb_info.get('count', 0)} 个知识切片")
        st.markdown("---")

    # ===== 学习大纲 =====
    messages = get_current_messages()

    # 优先使用缓存的最新计划，否则从消息中提取
    cached_plan = st.session_state.current_session.get("_cached_plan_md")
    if cached_plan:
        plan_md = cached_plan
    else:
        plan_md, _ = _extract_plan_from_messages(messages)

    if plan_md:
        # 解析为按天结构化数据
        days = _parse_daily_plan(plan_md)

        if days:
            # 获取完成状态
            completed = st.session_state.current_session.get("_day_completed", {})

            # 获取标题
            doc_meta = st.session_state.current_session.get("_doc_meta")
            map_title = (doc_meta.get("title") if doc_meta else None) or "学习计划"

            # 渲染交互式时间线
            st.markdown("#### 🗺️ 学习路线图")
            _render_timeline(days, completed, map_title)

            # 进度统计
            total = len(days)
            done_count = sum(1 for d in days if completed.get(str(d["day"]), False))
            if done_count > 0:
                st.caption(f"📊 进度：{done_count}/{total} 天已完成")
                # 同步 study_progress
                st.session_state.current_session["study_progress"] = done_count
            
            # 标记完成（Streamlit 原生交互）
            incomplete_days = [d for d in days if not completed.get(str(d["day"]), False)]
            if incomplete_days:
                next_day = incomplete_days[0]
                if st.button(f"✅ 完成 Day {next_day['day']}", key="mark_day_done"):
                    if "_day_completed" not in st.session_state.current_session:
                        st.session_state.current_session["_day_completed"] = {}
                    st.session_state.current_session["_day_completed"][str(next_day["day"])] = True
                    st.session_state.current_session["study_progress"] = done_count + 1
                    from src.ui.state import save_session_data
                    save_session_data(st.session_state.current_session_id, st.session_state.current_session)
                    st.experimental_rerun()
            else:
                st.success("🎉 全部完成！")

            st.markdown("---")

            # 完整大纲折叠展示
            with st.expander("📋 查看完整大纲", expanded=False):
                st.markdown(plan_md)

            st.download_button(
                label="📥 下载大纲",
                data=plan_md,
                file_name="xlearning_plan.md",
                mime="text/markdown",
                key="plan_panel_dl",
            )
        else:
            st.info("大纲已生成，详见左侧对话。")
    elif st.session_state.current_session.get("plan"):
        st.info("大纲已生成，详见左侧对话。")
    else:
        st.markdown("#### 📋 学习大纲")
        st.info("在左侧对话中输入学习主题，或点击下方生成大纲。")
        if st.session_state.is_processing:
            st.info("🕒 正在生成学习大纲，请稍候...")
        else:
            if st.button("📋 生成学习大纲", key="gen_plan_btn"):
                from src.ui.logic import handle_chat_input
                topic = ""
                doc_meta = st.session_state.current_session.get("_doc_meta")
                if doc_meta:
                    topic = doc_meta.get("title") or doc_meta.get("filename") or ""
                if not topic:
                    for msg in messages:
                        if msg.get("role") == "user":
                            topic = msg["content"]
                            break
                plan_prompt = f"请为以下主题生成一份详细的学习计划：{topic}" if topic else "请根据已上传的学习资料，生成一份详细的学习计划"
                handle_chat_input(plan_prompt)


# ============================================================================
# Study Panel（学习阶段右侧面板）
# ============================================================================

def render_study_panel():
    """学习面板：知识库状态 + 大纲进度 + 学习提示。"""
    if not st.session_state.current_session:
        st.info("请先开始一个学习会话。")
        return

    # ===== 知识库状态 =====
    kb_info = st.session_state.kb_info
    if kb_info.get("source"):
        st.markdown("#### 🧠 知识库")
        st.success(f"**{kb_info['source']}**")
        st.caption(f"状态: {'✅ 就绪' if st.session_state.kb_status == 'ready' else st.session_state.kb_status} | 切片: {kb_info.get('count', 0)}")
        st.markdown("---")

    # ===== 学习进度 =====
    cached_plan = st.session_state.current_session.get("_cached_plan_md")
    if cached_plan:
        days = _parse_daily_plan(cached_plan)
    else:
        plan_md, _ = _extract_plan_from_messages(get_current_messages())
        days = _parse_daily_plan(plan_md) if plan_md else []

    if days:
        st.markdown("#### 📋 学习进度")
        completed = st.session_state.current_session.get("_day_completed", {})
        total = len(days)
        done_count = sum(1 for d in days if completed.get(str(d["day"]), False))
        st.progress(done_count / max(total, 1))
        for d in days:
            is_done = completed.get(str(d["day"]), False)
            st.markdown(f"{'✅' if is_done else '⬜'} **Day {d['day']}** {d['title']}")
        st.markdown("---")

    # ===== 学习助手提示 =====
    st.markdown("#### 📖 学习助手")
    st.caption("在左侧对话框中向 Tutor 提问，基于你的学习资料获得个性化回答。")
    st.markdown("💡 **试试这些问题：**")
    st.caption("• 什么是 XXX？\n• 帮我解释一下这个概念\n• 能举个例子吗？\n• 它和 YYY 有什么区别？")


# ============================================================================
# Brain Tab (Knowledge & Artifacts)
# ============================================================================

def render_brain_tab():
    """Render the Brain tab: Uploaded Files & Generated Artifacts."""
    
    if not st.session_state.current_session:
        st.info("请先开始一个学习会话。")
        return

    st.markdown("### 🧠 记忆与知识 (Brain)")
    
    st.markdown("#### 📄 上传的上下文 (Context)")
    kb_info = st.session_state.kb_info
    if kb_info.get("source"):
        st.success(f"**{kb_info['source']}**")
        st.caption(f"Status: {st.session_state.kb_status} | Chunks: {kb_info.get('count', 0)}")
    else:
        st.info("当前会话未关联 PDF/URL。")
        
    st.markdown("---")
    
    st.markdown("#### 📦 生成的产物 (Artifacts)")
    # Check for report
    report = st.session_state.current_session.get("report", {})
    if report.get("generated"):
        st.markdown(f"**📊 学习报告**")
        st.download_button(
            label="📥 下载 Markdown",
            data=report.get("content", ""),
            file_name="report.md",
            mime="text/markdown",
            key="brain_dl_report"
        )
    else:
        st.info("暂无生成产物。")

# ============================================================================
# Trace Tab
# ============================================================================

def render_trace_tab():
    """Render the Trace tab with step-grouped timeline."""
    
    if not st.session_state.current_session:
        st.info("暂无 Trace 数据。开始对话后将记录工具调用。")
        return
    
    trace_events = st.session_state.current_session.get("trace", [])
    
    if not trace_events:
        st.info("暂无 Trace 数据。开始对话后将记录工具调用。")
        return
    
    # Group by step_id
    steps = {}
    for event in trace_events:
        step_id = event.get("step_id", "unknown")
        if step_id not in steps:
            steps[step_id] = []
        steps[step_id].append(event)
    
    # Render each step as an expander (Reverse order: newest first)
    step_list = list(steps.items())
    step_list.reverse()
    
    for step_id, events in step_list:
        first_event = events[0]
        step_name = first_event.get("name", step_id)
        
        # Calculate duration if we have start and end
        duration = ""
        start_ts = None
        end_ts = None
        for e in events:
            if e["type"] == "tool_start":
                start_ts = e["ts"]
            if e["type"] == "tool_end":
                end_ts = e["ts"]
        if start_ts and end_ts:
            duration = " (完成)"
        
        with st.expander(f"🔧 {step_name}{duration}", expanded=False):
            for event in events:
                _render_trace_event(event)

def _render_trace_event(event: dict):
    """Render a single trace event."""
    
    event_type = event.get("type", "unknown")
    name = event.get("name", "")
    detail = event.get("detail", "")
    ts = event.get("ts", "")[:19]  # Truncate to seconds
    
    icon_map = {
        "tool_start": "🟢",
        "tool_end": "🔴",
        "progress": "🔄"
    }
    icon = icon_map.get(event_type, "⚪")
    
    st.markdown(f"`{ts}` {icon} **{event_type}**: {name}")
    if detail:
        st.caption(detail)

# ============================================================================
# Quiz Tab
# ============================================================================

def render_quiz_tab():
    """Render the Quiz tab with questions, answers, and scoring."""
    
    if not st.session_state.current_session:
        st.info("请先开始一个学习会话，然后可以生成测验。")
        return
    
    quiz = st.session_state.current_session.get("quiz", {})
    questions = quiz.get("questions", [])
    answers = quiz.get("answers", {})
    score = quiz.get("score")
    wrong_questions = quiz.get("wrong_questions", [])
    
    # No quiz yet
    if not questions:
        st.markdown("### 🎓 准备好测试你的学习成果了吗？")
        if st.session_state.is_processing:
            st.info("🕒 正在生成测验题目，请稍候...")
        else:
            if st.button("生成测验", key="generate_quiz"):
                from src.ui.logic import handle_generate_quiz
                handle_generate_quiz()
        return
    
    # Quiz in progress or completed
    st.markdown(f"### 📝 测验 ({len(questions)} 题)")
    
    # Render each question
    for q in questions:
        qid = q.get("qid", "")
        question_text = q.get("question", "")
        # Compatible with both 'options' (new) and 'choices' (old)
        choices = q.get("options", q.get("choices", []))
        
        # Handle correct answer (letter or index)
        correct_answer = q.get("correct_answer")
        correct_idx = q.get("answer_index", 0)
        
        if correct_answer and isinstance(correct_answer, str) and choices:
            # Map 'A' -> 0
            if correct_answer in ["A", "B", "C", "D"]:
                mapping = {"A": 0, "B": 1, "C": 2, "D": 3}
                correct_idx = mapping.get(correct_answer, 0)
            # Or if correct_answer is the string itself match index
            elif correct_answer in choices:
                 correct_idx = choices.index(correct_answer)

        explanation = q.get("explanation", "")
        
        user_answer = answers.get(qid)
        is_wrong = qid in wrong_questions
        
        st.markdown(f"**{question_text}**")
        
        # Show radio for unanswered, or result for answered
        if score is None:
            # Quiz in progress
            selected = st.radio(
                f"选择答案 ({qid})",
                choices,
                index=user_answer if user_answer is not None else 0,
                key=f"quiz_{qid}"
            )
            # Store index
            answers[qid] = choices.index(selected)
        else:
            # Quiz completed - show results
            for i, choice in enumerate(choices):
                if i == correct_idx:
                    st.markdown(f"✅ {choice}")
                elif i == user_answer and is_wrong:
                    st.markdown(f"❌ ~~{choice}~~")
                else:
                    st.markdown(f"○ {choice}")
            
            if is_wrong and explanation:
                st.caption(f"💡 {explanation}")
        
        st.markdown("---")
    
    # Submit or Score display
    if score is None:
        if st.button("提交答案", key="submit_quiz"):
            _score_quiz()
    else:
        st.success(f"🎉 你的得分：{score} / {len(questions)}")
        wrong_count = len(wrong_questions)
        if wrong_count > 0:
            st.warning(f"错题数：{wrong_count}")

        # Report section (merged into Quiz tab)
        st.markdown("---")
        report = st.session_state.current_session.get("report", {})
        if report.get("generated"):
            st.markdown("### 📊 学习报告")
            with st.expander("预览报告", expanded=False):
                st.markdown(report.get("content", ""))
            st.download_button(
                label="📥 下载报告",
                data=report.get("content", ""),
                file_name="xlearning_report.md",
                mime="text/markdown",
                key="quiz_dl_report"
            )
        else:
            if st.session_state.is_processing:
                st.info("🕒 正在生成学习报告，请稍候...")
            else:
                if st.button("📊 生成学习报告", key="gen_report_from_quiz"):
                    from src.ui.logic import handle_generate_report
                    handle_generate_report()

def _score_quiz():
    """Score the current quiz."""
    if not st.session_state.current_session:
        return
    
    quiz = st.session_state.current_session.get("quiz", {})
    questions = quiz.get("questions", [])
    answers = quiz.get("answers", {})
    
    correct = 0
    wrong = []
    
    for q in questions:
        qid = q.get("qid")
        
        # Calculate correct index again
        choices = q.get("options", q.get("choices", []))
        correct_answer = q.get("correct_answer")
        correct_idx = q.get("answer_index", 0)
        
        if correct_answer and isinstance(correct_answer, str):
            if correct_answer in ["A", "B", "C", "D"]:
                mapping = {"A": 0, "B": 1, "C": 2, "D": 3}
                correct_idx = mapping.get(correct_answer, 0)
        
        user_answer = answers.get(qid)
        
        if user_answer == correct_idx:
            correct += 1
        else:
            wrong.append(qid)
    
    quiz["score"] = correct
    quiz["wrong_questions"] = wrong
    
    from src.ui.state import save_session_data
    save_session_data(st.session_state.current_session_id, st.session_state.current_session)
    st.experimental_rerun()

# ============================================================================
# Report Tab
# ============================================================================

def render_report_tab():
    """Render the Report tab with markdown preview and download."""
    
    if not st.session_state.current_session:
        st.info("请先开始一个学习会话，然后可以生成报告。")
        return
    
    report = st.session_state.current_session.get("report", {})
    generated = report.get("generated", False)
    content = report.get("content", "")
    
    if not generated:
        st.markdown("### 📊 学习进度报告")
        st.markdown("完成学习后，可以生成一份 Markdown 格式的进度报告。")
        if st.session_state.is_processing:
            st.info("🕒 正在生成报告，请稍候...")
        else:
            if st.button("📊 生成报告", key="generate_report"):
                from src.ui.logic import handle_generate_report
                handle_generate_report()
        return
    
    # Report generated - show preview and download
    st.markdown("### 📊 学习进度报告")
    
    # Preview
    with st.expander("预览报告", expanded=True):
        st.markdown(content)
    
    # Download button
    st.download_button(
        label="📥 下载 Markdown",
        data=content,
        file_name="xlearning_report.md",
        mime="text/markdown"
    )
