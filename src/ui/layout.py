"""
XLearning Agent - UI Layout
============================
3-tab stepper: Plan | Study | Resources
Stepper tabs are clickable for navigation. No action banner.
"""

import html
import streamlit as st
import streamlit.components.v1 as components
from src.ui.state import (
    t, init_session_state, create_new_session, switch_session,
    set_kb_status, get_current_messages, delete_session, clear_all_sessions,
    rename_session
)

# JavaScript: 最小化 — 仅用于标记双列容器，让 CSS 接管布局
_WORKSPACE_JS = """
<script>
(function() {
    // 空操作：所有布局由 CSS 控制
})();
</script>
"""

# ============================================================================
# Sidebar
# ============================================================================

def render_sidebar():
    with st.sidebar:
        st.markdown('<div class="huge-sidebar-logo">⚛️ XLearning</div>', unsafe_allow_html=True)

        if st.button(f"✨ {t('new_chat')}", key="new_chat_btn"):
            st.session_state.current_session_id = None
            st.experimental_rerun()

        st.markdown("---")

        # Settings
        st.markdown("**⚙️ 设置**")
        lang_options = ["中文", "English"]
        lang_idx = 0 if st.session_state.lang == "zh" else 1
        selected_lang = st.selectbox("语言 Language", lang_options, index=lang_idx, key="lang_select")
        st.session_state.lang = "zh" if selected_lang == "中文" else "en"

        # Dev Options
        if "langgraph_mode" not in st.session_state:
            st.session_state.langgraph_mode = False
        with st.expander("🛠️ 开发者选项", expanded=st.session_state.dev_mode):
            st.session_state.dev_mode = st.checkbox("启用开发模式", value=st.session_state.dev_mode, key="dev_toggle")
            if st.session_state.dev_mode:
                st.session_state.show_trace = st.checkbox("显示 Trace", value=st.session_state.show_trace, key="trace_toggle")
            st.session_state.langgraph_mode = st.checkbox("🆕 LangGraph 模式", value=st.session_state.langgraph_mode, key="langgraph_toggle")

        # Clear all data
        if st.button("🗑️ 清除所有对话", key="clear_all_btn", help="删除所有对话记录和缓存数据"):
            clear_all_sessions()
            st.experimental_rerun()

        st.markdown("---")

        # History
        st.markdown(f"**🗂️ {t('recents')}**")
        history_limit = 15
        count = 0
        for meta in st.session_state.session_index:
            if count >= history_limit:
                break
            sid = meta["id"]
            is_current = sid == st.session_state.current_session_id
            if not is_current and meta['title'] in ["New Chat", "New Project"]:
                if not meta.get("last_preview"):
                    continue
            icon = "📂" if is_current else "•"
            if "Python" in meta['title']: icon = "🐍"
            if "PDF" in meta['title']: icon = "📄"
            if "GitHub" in meta['title']: icon = "🔗"
            title_text = meta['title'][:20]

            if is_current:
                # 当前对话：显示名称 + 改名/删除（紧凑行内布局）
                st.markdown(
                    f'<div class="sess-item sess-active">{icon} {html.escape(title_text)}</div>',
                    unsafe_allow_html=True,
                )
                # 改名模式
                if st.session_state.get(f"_renaming_{sid}", False):
                    new_name = st.text_input(
                        "新名称",
                        value=meta['title'],
                        key=f"rename_input_{sid}",
                    )
                    if st.button("✅ 确认", key=f"rename_ok_{sid}"):
                        if new_name.strip():
                            rename_session(sid, new_name.strip())
                        st.session_state[f"_renaming_{sid}"] = False
                        st.experimental_rerun()
                    if st.button("❌ 取消", key=f"rename_cancel_{sid}"):
                        st.session_state[f"_renaming_{sid}"] = False
                        st.experimental_rerun()
                else:
                    # 改名和删除：用独立按钮，不用 st.columns 避免 CSS 冲突
                    if st.button("✏️ 改名", key=f"ren_{sid}"):
                        st.session_state[f"_renaming_{sid}"] = True
                        st.experimental_rerun()
                    if st.button("🗑 删除", key=f"del_{sid}"):
                        delete_session(sid)
                        st.experimental_rerun()
            else:
                # 其他对话：单按钮切换
                if st.button(f"{icon} {title_text}", key=f"session_{sid}"):
                    switch_session(sid)
                    st.experimental_rerun()
            count += 1

        # Footer
        st.markdown("---")
        try:
            from src.core.config import Config
            cfg = Config.get()
            ls_ok = cfg.langsmith.enabled and cfg.has_langsmith_key
        except Exception:
            import os
            ls_ok = bool(os.environ.get("LANGCHAIN_API_KEY") or os.environ.get("LANGSMITH_API_KEY"))
        ls_text = "LangSmith ✅" if ls_ok else "LangSmith ❌"
        st.markdown(f'<div class="sidebar-footer">v0.3.0 | {ls_text}</div>', unsafe_allow_html=True)

# ============================================================================
# Main Controller
# ============================================================================

def render_main_area():
    if st.session_state.current_session_id is not None:
        render_workspace_view()
    else:
        render_home_view()


# ============================================================================
# Home View
# ============================================================================

def render_home_view():
    # prefill 处理
    if "home_prompt_prefill" not in st.session_state:
        st.session_state.home_prompt_prefill = ""
    if "_home_submitted" not in st.session_state:
        st.session_state._home_submitted = False
    if "_show_file_upload" not in st.session_state:
        st.session_state._show_file_upload = False

    # 如果上一轮标记了提交，执行提交
    if st.session_state._home_submitted:
        st.session_state._home_submitted = False
        val = st.session_state.get("home_input_widget", "").strip()
        if val:
            _handle_home_submit(val, None)
            return

    # Hero 标题
    st.markdown(
        f"<div class='home-hero'><h1 class='home-title'>👋 {t('welcome_title')}</h1>"
        f"<p class='home-subtitle'>{t('welcome_subtitle')}</p></div>",
        unsafe_allow_html=True,
    )

    def _on_home_input_change():
        st.session_state._home_submitted = True

    default_val = ""
    if st.session_state.home_prompt_prefill:
        default_val = st.session_state.home_prompt_prefill
        st.session_state.home_prompt_prefill = ""

    # ===== 输入栏容器（+ 按钮 和 输入框 同行） =====
    # 用一个带 id 的标记 div，CSS 通过 :has() 定位紧随其后的 columns
    st.markdown('<div id="home-chatbar-anchor" style="display:none"></div>', unsafe_allow_html=True)
    bar_left, bar_right = st.columns([1, 12])
    with bar_left:
        if st.button("➕", key="home_plus_btn"):
            st.session_state._show_file_upload = not st.session_state._show_file_upload
            st.experimental_rerun()
    with bar_right:
        st.text_input(
            "",
            value=default_val,
            placeholder="有问题，尽管问...  按 Enter 开始学习",
            key="home_input_widget",
            on_change=_on_home_input_change,
        )
    
    # 文件上传弹出层
    if st.session_state._show_file_upload:
        uploaded_file = st.file_uploader(
            "📎 选择文件（PDF / MD / TXT / DOCX）",
            type=["pdf", "md", "txt", "docx"],
            key="home_file_uploader",
        )
        if uploaded_file:
            st.session_state._show_file_upload = False
            prompt_val = st.session_state.get("home_input_widget", "").strip()
            _handle_home_submit(prompt_val, uploaded_file)
            return

    # ===== 快捷示例 =====
    st.markdown("<div class='home-quick-label'>💡 试试这些</div>", unsafe_allow_html=True)
    row1_col1, row1_col2, row1_col3 = st.columns(3)
    with row1_col1:
        if st.button("📄 分析论文", key="home_quick_1"):
            st.session_state.home_prompt_prefill = "请分析这篇论文，给我摘要、关键结论和可复现要点。"
            st.experimental_rerun()
    with row1_col2:
        if st.button("🔗 GitHub 仓库", key="home_quick_2"):
            st.session_state.home_prompt_prefill = "https://github.com/langchain/langchain"
            st.experimental_rerun()
    with row1_col3:
        if st.button("🎓 学习计划", key="home_quick_3"):
            st.session_state.home_prompt_prefill = "我想系统学习 Transformer，请帮我制定一个 7 天学习计划。"
            st.experimental_rerun()
    row2_col1, row2_col2, row2_col3 = st.columns(3)
    with row2_col1:
        if st.button("🐍 Python 路径", key="home_quick_4"):
            st.session_state.home_prompt_prefill = "请给我一份从入门到项目实战的 Python 学习路径。"
            st.experimental_rerun()
    with row2_col2:
        if st.button("🧠 面试复习", key="home_quick_5"):
            st.session_state.home_prompt_prefill = "我准备 AI 工程师面试，请给我 14 天复习计划。"
            st.experimental_rerun()
    with row2_col3:
        if st.button("🧩 LeetCode", key="home_quick_6"):
            st.session_state.home_prompt_prefill = "我准备算法面试，请给我 LeetCode 两周刷题计划。"
            st.experimental_rerun()


def _handle_home_submit(prompt: str, file):
    title = "New Project"
    if file:
        title = f"📄 {file.name}"
    elif "github.com" in prompt:
        title = f"🔗 {prompt.split('/')[-1]}"
    elif prompt:
        title = prompt[:20]

    create_new_session(title=title)

    if file:
        from src.ui.logic import handle_file_upload
        handle_file_upload(file)

    if prompt and prompt.strip():
        from src.ui.logic import handle_chat_input
        if "http" in prompt and "github" in prompt:
            from src.ui.state import set_kb_status
            set_kb_status("parsing", source=prompt)
        handle_chat_input(prompt, should_rerun=False)

    st.experimental_rerun()


# ============================================================================
# Workspace View: 2-tab clickable stepper + 2-column layout
# ============================================================================

def render_workspace_view():
    from src.ui.state import calculate_stage_logic

    logic = calculate_stage_logic(st.session_state.current_session)
    stages = logic.get("stages", {})
    active_tab = st.session_state.active_tab

    # Ensure active_tab is valid for 3-tab system (Plan | Study | Resources)
    if active_tab not in ("Plan", "Study", "Resources", "Trace"):
        active_tab = "Plan"
        st.session_state.active_tab = "Plan"

    # ===== Clickable Stepper =====
    _render_clickable_stepper(stages, active_tab)

    # ===== 2-column layout (chat wider by default) =====
    c_chat, c_panel = st.columns([3, 2])

    with c_chat:
        from src.ui.renderer import render_chat_tab
        render_chat_tab()

    with c_panel:
        st.markdown('<div class="right-panel-sticky">', unsafe_allow_html=True)
        if active_tab == "Plan":
            from src.ui.renderer import render_plan_panel
            render_plan_panel()
        elif active_tab == "Study":
            from src.ui.renderer import render_study_panel
            render_study_panel()
        elif active_tab == "Resources":
            from src.ui.renderer import render_resources_panel
            render_resources_panel()
        elif active_tab == "Trace":
            from src.ui.renderer import render_trace_tab
            render_trace_tab()

        # Brain 区域 — 始终显示在所有 Tab 内容下方
        from src.ui.renderer import render_brain_tab
        render_brain_tab()

        st.markdown('</div>', unsafe_allow_html=True)

    components.html(_WORKSPACE_JS, height=0)

    # ===== Footer =====
    st.markdown(
        '<div class="workspace-footer">'
        '<span>⚛️ XLearning Agent v0.3.0</span>'
        '<span>·</span>'
        '<span>Powered by LangChain + RAG</span>'
        '</div>',
        unsafe_allow_html=True,
    )


def _render_clickable_stepper(stages: dict, active_tab: str):
    """Render a compact tab bar — buttons centered, active tab with accent underline."""
    tab_keys = ["Plan", "Study", "Resources"]
    if st.session_state.get("dev_mode") and st.session_state.get("show_trace"):
        tab_keys.append("Trace")

    # 用 5 列布局让 tab 居中（两侧留空）
    col_widths = [1.2] + [0.8] * len(tab_keys) + [1.2]
    all_cols = st.columns(col_widths)

    for i, key in enumerate(tab_keys):
        s = stages.get(key, {"label": key, "icon": "🔧"})
        is_active = key == active_tab
        label = s.get("label", key)
        icon = s.get("icon", str(i + 1))
        display = f"{icon} {label}"
        with all_cols[i + 1]:  # 跳过第一个空列
            if st.button(display, key=f"stepper_btn_{key}"):
                st.session_state.active_tab = key
                st.experimental_rerun()
            # 当前 tab 下方加橙色指示线
            if is_active:
                st.markdown(
                    '<div style="height:3px;background:#F97316;border-radius:2px;margin:-8px auto 0;width:60%;"></div>',
                    unsafe_allow_html=True,
                )


