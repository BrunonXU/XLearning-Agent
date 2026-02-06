"""
XLearning Agent - UI Renderer
==============================
Handles: Chat Tab, Trace Tab, Quiz Tab, Report Tab rendering
Strictly compatible with Streamlit 1.12.0.
"""

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
    """Render a single message using legacy st.columns and custom HTML."""
    
    role = msg.get("role", "assistant")
    agent = msg.get("agent")
    content = msg.get("content", "")
    citations = msg.get("citations", [])
    status = msg.get("status", "complete")
    error = msg.get("error")
    
    # Determine avatar
    if role == "user":
        avatar = AGENT_AVATARS["user"]
        bubble_class = "user-bubble"
    else:
        avatar = AGENT_AVATARS.get(agent, "🤖")
        bubble_class = "assistant-bubble"
    
    # Render using custom HTML for a clean look
    st.markdown(f"""
    <div class="chat-row">
        <div class="avatar-icon">{avatar}</div>
        <div class="chat-bubble {bubble_class}">
            {f'<b>[{agent.upper()}]</b><br>' if agent else ''}
            {content}
        </div>
    </div>
    """, unsafe_allow_html=True)
    
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
    """Render the chat input area at the bottom."""
    
    # Show stop button during processing
    if st.session_state.is_processing:
        if st.button(t("stop"), key="stop_btn"):
            st.session_state.stop_requested = True
            st.experimental_rerun()
            
    st.markdown("---")

    # Callback to handle input submission
    def on_input_change():
        user_input = st.session_state.chat_input_val
        if user_input.strip():
            from src.ui.logic import handle_chat_input
            handle_chat_input(user_input, should_rerun=False)
            # Clear input
            st.session_state.chat_input_val = ""

    # Ensure session state key exists
    if "chat_input_val" not in st.session_state:
        st.session_state.chat_input_val = ""
    
    # Wider Input Container
    c1, c2 = st.columns([12, 1])
    with c1:
        st.text_input(
            label="Message",
            placeholder=t("chat_placeholder"), 
            value="", 
            key="chat_input_val",
            on_change=on_input_change,
        )
    with c2:
        if st.button("🚀", key="send_btn_icon"):
            on_input_change()
            st.experimental_rerun()


# ============================================================================
# Brain Tab (Knowledge & Artifacts)
# ============================================================================

def render_brain_tab():
    """Render the Brain tab: Uploaded Files & Generated Artifacts."""
    
    if not st.session_state.current_session:
        st.info("请先开始一个学习会话。")
        return

    st.markdown("### 🧠 记忆与知识 (Brain)")
    
    c1, c2 = st.columns(2)
    
    with c1:
        st.markdown("#### 📄 上传的上下文 (Context)")
        kb_info = st.session_state.kb_info
        if kb_info.get("source"):
            st.success(f"**{kb_info['source']}**")
            st.caption(f"Status: {st.session_state.kb_status} | Chunks: {kb_info.get('count', 0)}")
            st.caption(f"Indexed at: {kb_info.get('ts', 'N/A')}")
        else:
            st.info("当前会话未关联 PDF/URL。")
            
    with c2:
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
        qid = q["qid"]
        question_text = q["question"]
        choices = q["choices"]
        correct_idx = q["answer_index"]
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
        qid = q["qid"]
        correct_idx = q["answer_index"]
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
        if st.button("生成报告", key="generate_report"):
            # TODO: Call report generator
            st.info("报告生成功能即将上线...")
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
