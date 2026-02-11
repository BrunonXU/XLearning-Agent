"""
XLearning Agent - UI Layout
============================
Handles: Sidebar, Home View (Project Context), Workspace View (Tabs)
Refactored for ChatGPT-style Interaction (Unified Input).
"""

import html
import streamlit as st
import streamlit.components.v1 as components
from src.ui.state import (
    t, init_session_state, create_new_session, switch_session,
    set_kb_status, get_current_messages
)

# JavaScript：让双列分隔线支持拖拽调整宽度
_COLUMN_RESIZE_JS = """
<script>
(function() {
    const doc = window.parent.document;
    const blocks = doc.querySelectorAll('[data-testid="stHorizontalBlock"]');
    let target = null;
    for (const b of blocks) {
        if (b.children.length === 2) target = b;
    }
    if (!target || target.dataset.resizeInit) return;
    target.dataset.resizeInit = '1';

    // 关键：强制不换行 + 无间隙，防止右列掉下去
    target.style.flexWrap = 'nowrap';
    target.style.gap = '0px';
    target.style.display = 'flex';

    const left = target.children[0];
    const right = target.children[1];
    left.style.minWidth = '0';
    left.style.overflow = 'hidden';
    right.style.minWidth = '220px';
    right.style.flexShrink = '0';
    right.style.overflow = 'visible';

    // 拖拽手柄
    const handle = doc.createElement('div');
    handle.style.cssText =
        'position:absolute;right:-6px;top:0;bottom:0;width:14px;' +
        'cursor:col-resize;z-index:1000;';
    left.style.position = 'relative';
    left.appendChild(handle);

    handle.addEventListener('mouseenter', function() {
        left.style.borderRightColor = '#9CA3AF';
        left.style.borderRightWidth = '3px';
    });
    handle.addEventListener('mouseleave', function() {
        if (!isDragging) {
            left.style.borderRightColor = '#E5E7EB';
            left.style.borderRightWidth = '2px';
        }
    });

    let isDragging = false, startX = 0, startLeftW = 0, totalW = 0;

    handle.addEventListener('mousedown', function(e) {
        isDragging = true;
        startX = e.clientX;
        startLeftW = left.getBoundingClientRect().width;
        totalW = target.getBoundingClientRect().width;
        doc.body.style.cursor = 'col-resize';
        doc.body.style.userSelect = 'none';
        left.style.borderRightColor = '#6B7280';
        left.style.borderRightWidth = '3px';
        e.preventDefault();
    });

    doc.addEventListener('mousemove', function(e) {
        if (!isDragging) return;
        const newLeftW = startLeftW + (e.clientX - startX);
        if (newLeftW < totalW * 0.3 || newLeftW > totalW * 0.75) return;
        const newRightW = totalW - newLeftW;
        left.style.width = newLeftW + 'px';
        left.style.flex = 'none';
        left.style.maxWidth = 'none';
        right.style.width = newRightW + 'px';
        right.style.flex = 'none';
        right.style.maxWidth = 'none';
    });

    doc.addEventListener('mouseup', function() {
        if (isDragging) {
            isDragging = false;
            doc.body.style.cursor = '';
            doc.body.style.userSelect = '';
            left.style.borderRightColor = '#E5E7EB';
            left.style.borderRightWidth = '2px';
        }
    });
})();
</script>
"""

# ============================================================================
# Sidebar: Navigation & Settings
# ============================================================================

def render_sidebar():
    """Render the sidebar: Title -> Settings -> History."""
    
    with st.sidebar:
        # ===== 1. Logo（仅展示，不可点击）=====
        st.markdown('<div class="huge-sidebar-logo">⚛️ XLearning</div>', unsafe_allow_html=True)
        
        # ===== New Project Button =====
        if st.button(f"✨ {t('new_chat')}", key="new_chat_btn"):
            st.session_state.current_session_id = None
            st.experimental_rerun()
            
        st.markdown("---")
        
        # ===== 2. Global Settings =====
        st.markdown("**⚙️ 设置**")
        
        # Language
        lang_options = ["中文", "English"]
        lang_idx = 0 if st.session_state.lang == "zh" else 1
        selected_lang = st.selectbox("语言 Language", lang_options, index=lang_idx, key="lang_select")
        st.session_state.lang = "zh" if selected_lang == "中文" else "en"
        
        # UI Mode
        ui_modes = {"Guided": "引导模式 (推荐)", "Free": "自由模式"}
        rev_modes = {v: k for k, v in ui_modes.items()}
        selected_mode_label = st.radio(
            "交互模式 Mode", 
            options=list(ui_modes.values()), 
            index=0 if st.session_state.ui_mode == "guided" else 1,
            key="ui_mode_radio"
        )
        st.session_state.ui_mode = rev_modes[selected_mode_label].lower()

        # Dev Options（mockups 8：开发者选项 + LangGraph 预留）
        if "langgraph_mode" not in st.session_state:
            st.session_state.langgraph_mode = False
        with st.expander("🛠️ 开发者选项", expanded=st.session_state.dev_mode):
            st.session_state.dev_mode = st.checkbox("启用开发模式", value=st.session_state.dev_mode, key="dev_toggle")
            if st.session_state.dev_mode:
                st.session_state.show_trace = st.checkbox("显示 Trace", value=st.session_state.show_trace, key="trace_toggle")
            st.session_state.langgraph_mode = st.checkbox("🆕 LangGraph 模式", value=st.session_state.langgraph_mode, key="langgraph_toggle")

        st.markdown("---")
        
        # ===== 3. History List =====
        st.markdown(f"**🗂️ {t('recents')}**")
        
        # Filter Logic: Only show real sessions (has messages or custom title)
        # Always show current session even if empty
        history_limit = 15
        count = 0
        
        for meta in st.session_state.session_index:
            if count >= history_limit: break
            
            is_current = meta["id"] == st.session_state.current_session_id
            
            # Skip empty "New Chat" sessions unless it's the current one
            if not is_current and meta['title'] in ["New Chat", "New Project"]:
                # Check if it has content? (Too expensive to load all data, rely on title/preview)
                if not meta.get("last_preview"): 
                    continue
            
            # Icon styling
            icon = "📂" if is_current else "•"
            if "Python" in meta['title']: icon = "🐍"
            if "PDF" in meta['title']: icon = "📄"
            if "GitHub" in meta['title']: icon = "🔗"
            
            # Button Label
            label = f"{icon} {meta['title'][:18]}"
            
            if st.button(label, key=f"session_{meta['id']}"):
                switch_session(meta["id"])
                st.experimental_rerun()
            count += 1

        # 底部状态（mockups 8：版本号 + LangSmith）
        st.markdown("---")
        try:
            from src.core.config import Config
            cfg = Config.get()
            ls_ok = cfg.langsmith.enabled and cfg.has_langsmith_key
        except Exception:
            import os
            ls_ok = bool(os.environ.get("LANGCHAIN_API_KEY") or os.environ.get("LANGSMITH_API_KEY"))
        ls_text = "LangSmith ✅" if ls_ok else "LangSmith ❌"
        st.markdown(f'<div class="sidebar-footer">v0.2.0 | {ls_text}</div>', unsafe_allow_html=True)

# ============================================================================
# Main Controller
# ============================================================================

def render_main_area():
    """Decide whether to render Home View or Workspace View."""
    
    # Check if we have an active session
    has_session = st.session_state.current_session_id is not None
    
    if not has_session:
        render_home_view()
    else:
        render_workspace_view()

# ============================================================================
# Home View: 原始稳定版本（先恢复可用，再迭代视觉）
# ============================================================================

def render_home_view():
    """首页：主输入框优先、大而宽，PDF 收起到下方，无多余白框。"""

    if "home_prompt_prefill" in st.session_state and st.session_state.home_prompt_prefill:
        st.session_state.home_prompt_input = st.session_state.home_prompt_prefill
        st.session_state.home_prompt_prefill = ""

    st.markdown(
        f"<div class='home-hero'><h1 class='home-title'>👋 {t('welcome_title')}</h1>"
        f"<p class='home-subtitle'>{t('welcome_subtitle')}</p></div>",
        unsafe_allow_html=True,
    )

    st.markdown('<div class="home-input-wrap">', unsafe_allow_html=True)
    with st.form("home_input_form", clear_on_submit=False):
        # 主输入框放最上面，大而宽（避免上方白框错觉）
        prompt = st.text_area(
            "💬 输入问题 / 粘贴 GitHub URL",
            placeholder="问任何问题、粘贴 GitHub 仓库链接，或上传 PDF 开始学习...",
            key="home_prompt_input",
            height=120,
        )

        # PDF 收起到下方 expander，不再占主视觉
        with st.expander("📄 上传 PDF（可选）", expanded=False):
            uploaded_file = st.file_uploader(
                " ",
                type=["pdf"],
                key="home_pdf_uploader",
            )

        submitted = st.form_submit_button("🚀 开始学习")

        if submitted:
            if not prompt and not uploaded_file:
                st.warning("请先输入问题或上传文件。")
            else:
                _handle_home_submit(prompt, uploaded_file)
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='home-quick-label'>💡 快捷示例</div>", unsafe_allow_html=True)

    row1_col1, row1_col2, row1_col3 = st.columns(3)
    with row1_col1:
        if st.button("📄 分析这篇论文", key="home_quick_1"):
            st.session_state.home_prompt_prefill = "请分析这篇论文，给我摘要、关键结论和可复现要点。"
            st.experimental_rerun()
    with row1_col2:
        if st.button("🔗 分析 GitHub 仓库", key="home_quick_2"):
            st.session_state.home_prompt_prefill = "https://github.com/langchain/langchain"
            st.experimental_rerun()
    with row1_col3:
        if st.button("🎓 制定学习计划", key="home_quick_3"):
            st.session_state.home_prompt_prefill = "我想系统学习 Transformer，请帮我制定一个 7 天学习计划。"
            st.experimental_rerun()

    row2_col1, row2_col2, row2_col3 = st.columns(3)
    with row2_col1:
        if st.button("🐍 Python 学习路径", key="home_quick_4"):
            st.session_state.home_prompt_prefill = "请给我一份从入门到项目实战的 Python 学习路径。"
            st.experimental_rerun()
    with row2_col2:
        if st.button("🧠 面试复习计划", key="home_quick_5"):
            st.session_state.home_prompt_prefill = "我准备 AI 工程师面试，请给我 14 天复习计划。"
            st.experimental_rerun()
    with row2_col3:
        if st.button("🧩 LeetCode 刷题安排", key="home_quick_6"):
            st.session_state.home_prompt_prefill = "我准备算法面试，请给我 LeetCode 两周刷题计划。"
            st.experimental_rerun()

# ============================================================================
# Workspace View: Tabbed Interface
# ============================================================================


def render_workspace_view():
    """Render the active project workspace with Stepper and 2-column layout."""
    
    from src.ui.state import calculate_stage_logic
    
    # 1. Calculate Logic
    logic = calculate_stage_logic(st.session_state.current_session)
    stages = logic.get("stages", {})
    current_stage = st.session_state.active_tab # Use active_tab to track current view
    
    # 1.5. 检查是否全流程完成 → 显示庆祝页
    if _check_completion(st.session_state.current_session) and current_stage == "Complete":
        _render_completion_view(st.session_state.current_session, stages)
        return
    
    # 2. Stepper 固定吸顶（聊天向下滚动时始终可见，单次输出确保 DOM 正确）
    stepper_html = _render_stepper_html(stages, current_stage)
    st.markdown(
        f'<div class="stepper-fixed-spacer"></div><div class="stepper-fixed-wrap"><div class="stepper-container">{stepper_html}</div></div>',
        unsafe_allow_html=True,
    )
    _render_stepper_dev_controls(current_stage)

    # 3. 双列布局：聊天区（带右边框分隔线）| 准备面板
    c_chat, c_panel = st.columns([0.6, 0.4])
    
    with c_chat:
        from src.ui.renderer import render_chat_tab
        render_chat_tab()
        _render_action_banner(stages, st.session_state.active_tab)
        
    with c_panel:
        st.markdown('<div class="right-panel-sticky">', unsafe_allow_html=True)
        st.markdown(f"#### 🛠️ {stages.get(current_stage, {}).get('label', current_stage)} 面板")

        # Render View based on active_tab (formerly stage)
        if current_stage == "Input":
            # Repurpose Brain tab for Input/KB
            from src.ui.renderer import render_brain_tab
            render_brain_tab()
        elif current_stage == "Plan":
            from src.ui.renderer import render_plan_panel
            render_plan_panel()
        elif current_stage == "Study":
            from src.ui.renderer import render_study_panel
            render_study_panel()
        elif current_stage == "Quiz":
            from src.ui.renderer import render_quiz_tab
            render_quiz_tab()
        elif current_stage == "Report":
            from src.ui.renderer import render_report_tab
            render_report_tab()
        elif current_stage == "Trace":
            from src.ui.renderer import render_trace_tab
            render_trace_tab()
        st.markdown('</div>', unsafe_allow_html=True)

    # 4. 注入拖拽调整宽度的 JS（iframe 高度为 0，不占空间）
    components.html(_COLUMN_RESIZE_JS, height=0)

def _render_stepper_html(stages: dict, active_stage: str) -> str:
    """返回 Stepper 的 HTML 字符串（供 layout 包裹在固定容器中一次性输出）。"""
    stage_keys = ["Input", "Plan", "Study", "Quiz", "Report", "Trace"]
    items_html = ""
    for i, key in enumerate(stage_keys):
        s = stages.get(key, {})
        status_class = ""
        if key == active_stage: status_class = "active"
        elif s.get("done"): status_class = "done"
        elif s.get("ready"): status_class = "ready"
        label = s.get("label", key)
        circle_content = "✓" if status_class == "done" else str(i+1)
        items_html += f'<div class="stepper-item {status_class}"><div class="stepper-circle">{circle_content}</div><div class="stepper-label">{label}</div><div class="stepper-line"></div></div>'
    return items_html


def _render_stepper(stages: dict, active_stage: str):
    """Render the horizontal stepper component（用于完成页等无需吸顶的场景）。"""
    items = _render_stepper_html(stages, active_stage)
    st.markdown(f'<div class="stepper-container">{items}</div>', unsafe_allow_html=True)


def _render_stepper_dev_controls(active_stage: str):
    """开发者模式下显示阶段选择器。"""
    stage_keys = ["Input", "Plan", "Study", "Quiz", "Report", "Trace"]
    if st.session_state.get("dev_mode"):
        current_idx = stage_keys.index(active_stage) if active_stage in stage_keys else 0
        selected = st.selectbox(
            "当前阶段（仅开发者可见）",
            stage_keys,
            index=current_idx,
            key="dev_stage_select",
        )
        if selected != active_stage:
            st.session_state.active_tab = selected
            st.experimental_rerun()

def _render_action_banner(stages: dict, active_stage: str):
    """
    Render the Guided mode Action Banner.
    
    核心改进：按钮不再只切换 Tab，而是真正触发后端动作。
    每个阶段的"下一步"按钮绑定到对应的后端函数。
    """
    
    if st.session_state.get("ui_mode") != "guided":
        return
        
    # Get current logic
    s = stages.get(active_stage, {})
    banner_text = s.get("banner", "")
    action = s.get("action", "")
    
    target_stage = active_stage
    # If done, suggest next stage
    if s.get("done"):
        stage_keys = ["Input", "Plan", "Study", "Quiz", "Report"]
        try:
            idx = stage_keys.index(active_stage)
        except ValueError:
            idx = -1
        if 0 <= idx < len(stage_keys) - 1:
            next_stage = stage_keys[idx+1]
            if stages.get(next_stage, {}).get("ready"):
                banner_text = stages[next_stage]["banner"]
                action = stages[next_stage]["action"]
                target_stage = next_stage

    if not banner_text:
        return

    # 根据 action 决定按钮文案（对照 docs/ui_mockups.md 9.2）
    btn_labels = {
        "input": "✨ 开始",
        "generate_plan": "📋 生成学习计划",
        "start_study": "📖 开始学习第一章",
        "start_quiz": "📝 开始测验",
        "view_report": "📊 生成报告",
        "view_completion": "🎉 查看总结",
        "view_trace": "🔍 查看追踪",
    }
    btn_label = btn_labels.get(action, "✨ 执行下一步")

    st.markdown(f"""
    <div class="action-banner">
        <div class="action-text">{banner_text}</div>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button(btn_label, key="action_banner_btn"):
        _dispatch_action(action, target_stage)


def _dispatch_action(action: str, target_stage: str):
    """
    分发引导流程的真实后端动作。
    
    这是引导模式的核心——每个阶段的按钮绑定到真实的后端函数，
    而不只是切换 Tab。
    """
    
    if action == "generate_plan":
        # 真正触发 Orchestrator 生成计划
        from src.ui.logic import handle_chat_input
        handle_chat_input("请根据已上传的学习资料，生成一份详细的学习计划", should_rerun=False)
        st.session_state.active_tab = "Plan"
        st.experimental_rerun()
        
    elif action == "start_study":
        # 切换到学习模式
        st.session_state.active_tab = "Study"
        st.experimental_rerun()
        
    elif action == "start_quiz":
        # 真正触发 Quiz 生成
        from src.ui.logic import handle_generate_quiz
        st.session_state.active_tab = "Quiz"
        handle_generate_quiz()  # 内部会 rerun
        
    elif action == "view_report":
        # 真正触发 Report 生成
        from src.ui.logic import handle_generate_report
        st.session_state.active_tab = "Report"
        handle_generate_report()  # 内部会 rerun
        
    elif action == "view_completion":
        st.session_state.active_tab = "Complete"
        st.experimental_rerun()
        
    elif action == "view_trace":
        st.session_state.active_tab = "Trace"
        st.experimental_rerun()
        
    else:
        # 默认：只切换 Tab
        st.session_state.active_tab = target_stage
        st.experimental_rerun()


# ============================================================================
# Helpers & Handlers
# ============================================================================

def _handle_home_submit(prompt: str, file):
    """Handle Home Form Submission -> Create Session -> Dispatch Logic."""
    
    # 1. Determine Title
    title = "New Project"
    if file:
        title = f"📄 {file.name}"
    elif "github.com" in prompt:
        title = f"🔗 {prompt.split('/')[-1]}"
    elif prompt:
        title = prompt[:20]
        
    # 2. Create Session
    create_new_session(title=title)
    
    # 3. Handle File (if any)
    if file:
        from src.ui.logic import handle_file_upload
        handle_file_upload(file)
    
    # 4. Handle Text/URL (if any)
    if prompt:
        # Check if URL
        if "http" in prompt and "github" in prompt:
            from src.ui.state import set_kb_status
            set_kb_status("parsing", source=prompt)
        # Or Chat
        else:
            from src.ui.logic import handle_chat_input
            handle_chat_input(prompt, should_rerun=False)
            
    # 5. Rerun to enter Workspace
    st.experimental_rerun()

def _render_kb_status_bar():
    """Render a slim status bar for KB."""
    status = st.session_state.kb_status
    info = st.session_state.kb_info
    
    color = "#2e7bcf" # Blue
    if status == "ready": color = "#28a745" # Green
    if status == "error": color = "#dc3545" # Red
    
    icon_map = {"parsing": "🔄", "ready": "✅", "error": "❌", "idle": "⚪"}
    icon = icon_map.get(status, "⚪")
    
    # Styled HTML Banner
    st.markdown(f"""
    <div style="
        padding: 8px 15px; 
        background-color: #f8f9fa; 
        border-radius: 6px; 
        margin-bottom: 15px; 
        border-left: 4px solid {color};
        display: flex;
        align-items: center;
        gap: 10px;
        font-size: 0.9rem;
    ">
        <span style="font-weight: bold;">Knowledge Base {icon}</span>
        <span>{status.upper()}</span>
        <span style="color: grey;">|</span>
        <span>{info.get('source', 'Unknown')}</span>
        <span style="color: grey;">|</span>
        <span>{info.get('count', 0)} chunks</span>
    </div>
    """, unsafe_allow_html=True)


# ============================================================================
# Completion View: Learning Journey Finished
# ============================================================================

def _check_completion(session: dict) -> bool:
    """检查学习流程是否全部完成。"""
    if not session:
        return False
    has_plan = session.get("plan") is not None
    has_quiz = session.get("quiz_attempts", 0) > 0
    has_report = session.get("report", {}).get("generated", False)
    return has_plan and has_quiz and has_report


def _render_completion_view(session: dict, stages: dict):
    """
    渲染学习完成庆祝页 — 闭环仪式感。对照 docs/ui_mockups.md 第 7 节。
    
    显示：全绿 Stepper + 三指标卡片（学习阶段、题目数、正确率）+ 摘要 + 下载报告 + 出口按钮
    """
    # 1. Stepper 全绿
    all_done_stages = {}
    for key in ["Input", "Plan", "Study", "Quiz", "Report"]:
        s = stages.get(key, {})
        all_done_stages[key] = {**s, "done": True}
    all_done_stages["Trace"] = stages.get("Trace", {"label": "追踪", "done": False})
    _render_stepper(all_done_stages, "Complete")
    
    # 2. 数据提取（对照 mockups）
    quiz_data = session.get("quiz", {})
    quiz_score = quiz_data.get("score")
    quiz_total = len(quiz_data.get("questions", []))
    accuracy_pct = f"{(quiz_score / quiz_total * 100):.0f}%" if quiz_score is not None and quiz_total > 0 else "N/A"
    report_data = session.get("report", {})
    plan = session.get("plan")
    if plan and isinstance(plan, dict):
        study_phases = len(plan.get("phases", []))
    elif plan and isinstance(plan, list):
        study_phases = len(plan)
    else:
        study_phases = session.get("study_progress", 0) or 0
    
    # 3. 居中大框 + 庆祝标题
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("""
    <div class="completion-card-wrap">
        <div class="completion-card">
            <div class="completion-title">🎉 恭喜！学习旅程已完成！</div>
    """, unsafe_allow_html=True)
    
    # 4. 三指标卡片（mockups：学习阶段、测验道题、正确率）
    st.markdown(f"""
            <div class="completion-stats">
                <div class="completion-stat-card completion-stat-success">
                    <div class="stat-icon">📚</div>
                    <div class="stat-value">{study_phases}</div>
                    <div class="stat-label">学习阶段</div>
                </div>
                <div class="completion-stat-card completion-stat-info">
                    <div class="stat-icon">📝</div>
                    <div class="stat-value">{quiz_total}</div>
                    <div class="stat-label">测验道题</div>
                </div>
                <div class="completion-stat-card completion-stat-warning">
                    <div class="stat-icon">📊</div>
                    <div class="stat-value">{accuracy_pct}</div>
                    <div class="stat-label">正确率</div>
                </div>
            </div>
    """, unsafe_allow_html=True)
    
    # 5. 摘要行（主题、薄弱点等）
    title = "—"
    for m in st.session_state.get("session_index", []):
        if m.get("id") == st.session_state.current_session_id:
            title = m.get("title", "—")[:30]
            break
    wrong_qs = quiz_data.get("wrong_questions", [])
    questions = quiz_data.get("questions", [])
    weak_topics = set()
    for qid in wrong_qs:
        for q in questions:
            if q.get("qid") == qid and q.get("topic"):
                weak_topics.add(q["topic"])
    weak_str = ", ".join(weak_topics) if weak_topics else "无"
    
    st.markdown(f"""
            <div class="completion-summary">
                <div class="summary-row"><span class="summary-key">主题</span> {html.escape(str(title))}</div>
                <div class="summary-row"><span class="summary-key">薄弱点</span> {html.escape(weak_str)}</div>
            </div>
            <hr class="completion-hr">
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # 6. 下载报告 + 7. 出口按钮（Streamlit 组件需单独渲染）
    if report_data.get("content"):
        st.download_button(
            label="📥 下载完整报告",
            data=report_data["content"],
            file_name="xlearning_report.md",
            mime="text/markdown",
            key="completion_dl_report"
        )
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("🔄 继续深入学习", key="continue_study"):
            st.session_state.active_tab = "Study"
            st.experimental_rerun()
    with col_b:
        if st.button("✨ 开始新课程", key="new_course"):
            st.session_state.current_session_id = None
            st.session_state.current_session = None
            st.experimental_rerun()
