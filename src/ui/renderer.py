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
    """Render the chat input area at the bottom（GPT 风格：白底、宽大输入框）。"""
    
    if st.session_state.is_processing:
        if st.button(t("stop"), key="stop_btn"):
            st.session_state.stop_requested = True
            st.experimental_rerun()
    
    st.markdown('<div class="chat-input-wrap">', unsafe_allow_html=True)

    def on_input_change():
        user_input = st.session_state.chat_input_val
        if user_input.strip():
            from src.ui.logic import handle_chat_input
            handle_chat_input(user_input, should_rerun=False)
            # Streamlit 1.12 限制：组件实例化后不能直接改同 key 的 session_state
            st.session_state.clear_chat_input = True

    if st.session_state.get("clear_chat_input", False):
        st.session_state.chat_input_val = ""
        st.session_state.clear_chat_input = False

    if "chat_input_val" not in st.session_state:
        st.session_state.chat_input_val = ""

    if not st.session_state.is_processing:
        # 使用 text_area 替代 text_input，更宽大、GPT 风格（不可嵌套 columns）
        st.text_area(
            label=" ",
            placeholder=t("chat_placeholder"),
            key="chat_input_val",
            height=88,
        )
        if st.button("🚀 发送", key="send_btn_icon"):
            on_input_change()
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
            for line in content.split("\n"):
                s = line.strip()
                # 匹配 ### 阶段 X: 或 ## 阶段 X 或 ⬜ 阶段 X:
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
            break
    return plan_md, phases[:6]


def render_plan_panel():
    """规划阶段右侧面板：记忆与知识 + 学习计划结构化预览 + 下载。"""
    if not st.session_state.current_session:
        st.info("请先开始一个学习会话。")
        return

    # 上传的上下文
    st.markdown("#### 📄 上传的上下文")
    kb_info = st.session_state.kb_info
    if kb_info.get("source"):
        st.success(f"**{kb_info['source']}**")
        st.caption(f"Status: {st.session_state.kb_status} | Chunks: {kb_info.get('count', 0)}")
    else:
        st.info("当前会话未关联 PDF/URL。")
    st.markdown("---")

    # 学习计划预览
    st.markdown("#### 📋 学习计划预览")
    messages = get_current_messages()
    plan_md, phases = _extract_plan_from_messages(messages)

    if plan_md and phases:
        for i, p in enumerate(phases, 1):
            st.markdown(f"**阶段 {i}**: {p}")
        st.markdown("---")
        st.download_button(
            label="📥 下载计划 .md",
            data=plan_md,
            file_name="xlearning_plan.md",
            mime="text/markdown",
            key="plan_panel_dl",
        )
    elif st.session_state.current_session.get("plan"):
        st.info("计划已生成，详细内容请查看左侧对话。")
    else:
        st.info("点击左侧「生成学习计划」按钮生成计划。")


# ============================================================================
# Study Panel（学习阶段右侧面板）
# ============================================================================

def render_study_panel():
    """学习阶段右侧面板：记忆与知识 + 学习计划进度 + 学习卡片占位。"""
    if not st.session_state.current_session:
        st.info("请先开始一个学习会话。")
        return

    # 上传的上下文
    st.markdown("#### 📄 上传的上下文")
    kb_info = st.session_state.kb_info
    if kb_info.get("source"):
        st.success(f"**{kb_info['source']}**")
        st.caption(f"Chunks: {kb_info.get('count', 0)}")
    else:
        st.info("当前会话未关联 PDF/URL。")

    # 学习计划进度
    st.markdown("#### 📋 学习计划")
    plan = st.session_state.current_session.get("plan")
    progress = st.session_state.current_session.get("study_progress", 0)
    _, phases = _extract_plan_from_messages(get_current_messages())
    total_phases = max(len(phases), 1)
    current = min(progress, total_phases)
    st.caption(f"当前阶段: {current}/{total_phases}")
    if plan:
        st.progress(current / total_phases if total_phases > 0 else 0)
    else:
        st.info("先生成学习计划再开始学习。")

    # 学习卡片（占位：后续可从对话中自动提取）
    st.markdown("---")
    st.markdown("#### 💡 学习卡片")
    st.caption("关键概念与问答将在此展示。")
    st.info("在左侧对话中提问，Tutor 会基于资料回答；学习卡片功能后续增强。")


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
