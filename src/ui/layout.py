"""
XLearning Agent - UI Layout
============================
Handles: Sidebar, Main Area (Tabs), Welcome Panel
"""

import streamlit as st
from src.ui.state import (
    t, init_session_state, create_new_session, switch_session,
    set_kb_status
)

# ============================================================================
# Sidebar
# ============================================================================

def render_sidebar():
    """Render the complete sidebar: Mode, Import, KB Status, Recents."""
    
    with st.sidebar:
        # ===== Header =====
        st.markdown(f"### ✦ {t('app_title')}")
        st.markdown("---")
        
        # ===== Mode Toggle =====
        mode_options = [t("standalone"), t("orchestrated")]
        mode_idx = 0 if st.session_state.mode == "standalone" else 1
        selected_mode = st.selectbox(
            t("mode"),
            mode_options,
            index=mode_idx,
            key="mode_select"
        )
        st.session_state.mode = "standalone" if selected_mode == t("standalone") else "orchestrated"
        
        # ===== Language Toggle =====
        lang_options = ["中文", "English"]
        lang_idx = 0 if st.session_state.lang == "zh" else 1
        selected_lang = st.selectbox(
            t("language"),
            lang_options,
            index=lang_idx,
            key="lang_select"
        )
        st.session_state.lang = "zh" if selected_lang == "中文" else "en"
        
        # ===== Show Trace Toggle =====
        st.session_state.show_trace = st.checkbox(
            t("show_trace"),
            value=st.session_state.show_trace,
            key="trace_toggle"
        )
        
        st.markdown("---")
        
        # ===== New Chat Button =====
        if st.button(t("new_chat"), key="new_chat_btn"):
            create_new_session()
            st.experimental_rerun()
        
        st.markdown("---")
        
        # ===== Import Section =====
        st.markdown(f"**📥 {t('import_pdf')}**")
        uploaded_file = st.file_uploader(
            "",
            type=["pdf"],
            key="pdf_uploader"
        )
        if uploaded_file:
            _handle_pdf_upload(uploaded_file)
        
        github_url = st.text_input(
            t("import_github"),
            placeholder="https://github.com/user/repo",
            key="github_input"
        )
        if github_url and st.button("导入", key="import_github_btn"):
            _handle_github_import(github_url)
        
        st.markdown("---")
        
        # ===== KB Status =====
        _render_kb_status()
        
        st.markdown("---")
        
        # ===== Recents =====
        st.markdown(f"**📜 {t('recents')}**")
        for meta in st.session_state.session_index[:10]:
            is_current = meta["id"] == st.session_state.current_session_id
            label = f"{'➤ ' if is_current else ''}{meta['title'][:20]}"
            if st.button(label, key=f"session_{meta['id']}"):
                switch_session(meta["id"])
                st.experimental_rerun()

# ============================================================================
# KB Status Widget
# ============================================================================
# ... code ...
# ============================================================================
# Import Handlers
# ============================================================================

def _handle_pdf_upload(file):
    """Handle PDF upload via logic bridge."""
    from src.ui.logic import handle_file_upload
    handle_file_upload(file)

def _handle_github_import(url: str):
    """Handle GitHub import."""
    # Placeholder for now, can extend logic.py later
    from src.ui.state import set_kb_status
    set_kb_status("parsing", source=url)
    st.experimental_rerun()
# ============================================================================
# Welcome Panel (Empty State)
# ============================================================================

def render_welcome_panel():
    """Render the welcome panel when no session is active or session is empty."""
    
    st.markdown(f"## {t('welcome_title')}")
    st.markdown(f"*{t('welcome_subtitle')}*")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button(t("action_pdf"), key="welcome_pdf"):
            # Focus on PDF uploader (handled by sidebar)
            pass
        
        if st.button(t("action_github"), key="welcome_github"):
            # Focus on GitHub input (handled by sidebar)
            pass
    
    with col2:
        if st.button(t("action_plan"), key="welcome_plan"):
            # Create a new session with a study plan prompt
            create_new_session(t("action_plan"))
            from src.ui.state import add_message
            add_message("user", "请帮我创建一个学习计划")
            st.experimental_rerun()
        
        if st.button(t("action_chat"), key="welcome_chat"):
            create_new_session("New Chat")
            st.experimental_rerun()
