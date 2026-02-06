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
        
        # ===== 2. Global Settings (Top Placement) =====
        # Compact Mode/Lang Selector
        c1, c2 = st.columns(2)
        with c1:
            # Mode
            mode_options = [t("standalone"), t("orchestrated")]
            mode_idx = 0 if st.session_state.mode == "standalone" else 1
            selected_mode = st.selectbox("Mode", mode_options, index=mode_idx, key="mode_select")
            st.session_state.mode = "standalone" if selected_mode == t("standalone") else "orchestrated"
        with c2:
            # Lang
            lang_options = ["中文", "English"]
            lang_idx = 0 if st.session_state.lang == "zh" else 1
            selected_lang = st.selectbox("Lang", lang_options, index=lang_idx, key="lang_select")
            st.session_state.lang = "zh" if selected_lang == "中文" else "en"
            
        # Trace Toggle
        st.session_state.show_trace = st.checkbox(t("show_trace"), value=st.session_state.show_trace, key="trace_toggle")

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
    """Render the active project workspace with Tabs."""
    
    # KB Status Bar
    if st.session_state.kb_status != "idle":
        _render_kb_status_bar()
    
    # Custom Nav Bar (Replaces st.tabs) with Sticky Class
    st.markdown('<div class="sticky-nav">', unsafe_allow_html=True)
    nav_cols = st.columns(5)
    
    tabs = [t("chat_tab"), "🧠 Brain", t("trace_tab"), t("quiz_tab"), t("report_tab")]
    
    for i, tab_name in enumerate(tabs):
        with nav_cols[i]:
            is_active = st.session_state.active_tab == tab_name
            # 1.12.0 Compat: No 'type'. Use emoji prefix to show active state.
            display_name = f"● {tab_name}" if is_active else tab_name
            if st.button(display_name, key=f"nav_{tab_name}"):
                st.session_state.active_tab = tab_name
                st.experimental_rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Render selected View based on active_tab
    active = st.session_state.active_tab
    
    if active == t("chat_tab"):
        from src.ui.renderer import render_chat_tab
        render_chat_tab()
    elif active == "🧠 Brain":
        from src.ui.renderer import render_brain_tab
        render_brain_tab()
    elif active == t("trace_tab"):
        from src.ui.renderer import render_trace_tab
        render_trace_tab()
    elif active == t("quiz_tab"):
        from src.ui.renderer import render_quiz_tab
        render_quiz_tab()
    elif active == t("report_tab"):
        from src.ui.renderer import render_report_tab
        render_report_tab()


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
