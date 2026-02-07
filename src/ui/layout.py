"""
XLearning Agent - UI Layout
============================
Handles: Sidebar, Home View (Project Context), Workspace View (Tabs)
Refactored for ChatGPT-style Interaction (Unified Input).
"""

import streamlit as st
from src.ui.state import (
    t, init_session_state, create_new_session, switch_session,
    set_kb_status, get_current_messages
)

# ============================================================================
# Sidebar: Navigation & Settings
# ============================================================================

def render_sidebar():
    """Render the sidebar: Title -> Settings -> History."""
    
    with st.sidebar:
        # ===== 1. App Title Centered & Massive =====
        st.markdown(f'<div class="huge-sidebar-logo">⚛️ XLearning</div>', unsafe_allow_html=True)
        
        # ===== New Project Button =====
        st.markdown('<div class="new-chat-container">', unsafe_allow_html=True)
        if st.button(f"✨ {t('new_chat')}", key="new_chat_btn"):
            st.session_state.current_session_id = None
            st.experimental_rerun()
        st.markdown('</div>', unsafe_allow_html=True)
            
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

        # Dev Options
        with st.expander("🛠️ 开发者选项", expanded=st.session_state.dev_mode):
            st.session_state.dev_mode = st.checkbox("启用开发模式", value=st.session_state.dev_mode, key="dev_toggle")
            if st.session_state.dev_mode:
                 st.session_state.show_trace = st.checkbox("显示 Trace", value=st.session_state.show_trace, key="trace_toggle")

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
# Home View: ChatGPT-style Unified Input
# ============================================================================

def render_home_view():
    """Render the detailed centered input interface."""
    
    # Spacer to push content down
    st.markdown("<br>" * 4, unsafe_allow_html=True)
    
    # Centered Column
    _, center_col, _ = st.columns([1, 2, 1])
    
    with center_col:
        # Title Greeting
        st.markdown(f"<h1 style='text-align: center'>👋 {t('welcome_title')}</h1>", unsafe_allow_html=True)
        st.markdown(f"<p style='text-align: center; color: gray'>{t('welcome_subtitle')}</p>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Unified Input Box (Form)
        with st.form("home_input_form", clear_on_submit=False):
            
            # File Upload Section (Visual "Drop Zone")
            uploaded_file = st.file_uploader(
                "📄 Upload Context (PDF)", 
                type=["pdf"], 
                key="home_pdf_uploader"
            )
            
            # Text / URL Input
            prompt = st.text_input(
                "💬 Message / URL",
                placeholder="Ask anything, paste GitHub URL, or upload PDF...",
                key="home_prompt_input"
            )
            
            # Action Button
            submitted = st.form_submit_button("🚀 Start") 
            
            if submitted:
                if not prompt and not uploaded_file:
                    st.warning("Please provide input or file.")
                else:
                    _handle_home_submit(prompt, uploaded_file)

        # Quick Tips / Examples
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("Try: `Analyze this paper`, `https://github.com/langchain`, `Python Study Plan`")

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
    
    # 2. Render Stepper
    _render_stepper(stages, current_stage)
    
    # Custom Split Ratio (Workaround for non-resizable columns)
    split_ratio = st.sidebar.slider("↔️ 聊天栏宽度 Chat Width", 30, 70, 60, key="layout_split") / 100
    
    # 3. Double Column Layout
    # Column 1: Chat | Column 2: Panel
    c_chat, c_panel = st.columns([split_ratio, 1 - split_ratio])
    
    with c_chat:

        from src.ui.renderer import render_chat_tab
        render_chat_tab()
        
        # Action Banner at the bottom of Chat
        _render_action_banner(stages, st.session_state.active_tab)
        
    with c_panel:
        st.markdown(f"#### 🛠️ {stages.get(current_stage, {}).get('label', current_stage)} 面板")
        st.markdown('<div class="control-panel-container">', unsafe_allow_html=True)
        
        # Render View based on active_tab (formerly stage)
        if current_stage == "Input":
            # Repurpose Brain tab for Input/KB
            from src.ui.renderer import render_brain_tab
            render_brain_tab()
        elif current_stage == "Plan":
            # For now show plan in markdown or customized
            # I will use a simplified render_plan if exists, or reuse Brain
            from src.ui.renderer import render_brain_tab
            render_brain_tab()
        elif current_stage == "Study":
            st.info("学习模式：点击左侧对话提问，或查看右侧知识卡片。")
            from src.ui.renderer import render_brain_tab
            render_brain_tab()
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

def _render_stepper(stages: dict, active_stage: str):
    """Render the horizontal stepper component."""
    
    stage_keys = ["Input", "Plan", "Study", "Quiz", "Report", "Trace"]
    
    # HTML-based Stepper for beautiful UI
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

    full_html = f'<div class="stepper-container">{items_html}</div>'
    st.write(full_html, unsafe_allow_html=True)
    
    # Hidden Streamlit selectors to actually change the stage (Free Mode)
    st.markdown('<div style="margin-top: -5px;">', unsafe_allow_html=True)
    cols = st.columns(len(stage_keys))
    for i, key in enumerate(stage_keys):
        with cols[i]:
            s = stages.get(key, {})
            # If ready or dev_mode, let user click
            # Use ghost button or transparent button for overlay effect
            btn_label = "Go" if s.get("ready") or st.session_state.get("dev_mode") else "🔒"
            if st.button(btn_label, key=f"step_btn_{key}"):
                if s.get("ready") or st.session_state.get("dev_mode"):
                    st.session_state.active_tab = key
                    st.experimental_rerun()
                else:
                    st.warning(s.get("block_msg", "尚未解锁"))
    st.markdown('</div>', unsafe_allow_html=True)

def _render_action_banner(stages: dict, active_stage: str):
    """Render the Guided mode Action Banner."""
    
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
        idx = stage_keys.index(active_stage)
        if idx < len(stage_keys) - 1:
            next_stage = stage_keys[idx+1]
            if stages.get(next_stage, {}).get("ready"):
                banner_text = stages[next_stage]["banner"]
                action = stages[next_stage]["action"]
                target_stage = next_stage

    if not banner_text:
        return

    st.markdown(f"""
    <div class="action-banner">
        <div class="action-text">{banner_text}</div>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("✨ 执行下一步", key="action_banner_btn"):
        # Switch to target stage panel
        st.session_state.active_tab = target_stage
        
        # If input stage and no prompt, maybe suggest?
        # For now just switch view
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
