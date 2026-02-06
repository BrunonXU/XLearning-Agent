"""
XLearning Agent - Claude 风格高级 UI (Simplified Clean Version)
===============================================================
核心文件：实现类 Claude 的 "米白色/高级感" 对话体验
**策略变更**: 放弃在底部 Input Bar 内融合 File Uploader，采用更可靠的分离式设计。
"""

import streamlit as st
from datetime import datetime
import uuid

# ============================================================================
# 🎨 Claude 风格样式定义 (Cream & Serif) - SIMPLIFIED
# ============================================================================

def get_premium_styles():
    """返回 Claude 风格的高级 CSS - 简化版，不再尝试 hack file_uploader"""
    return """
    <style>
    /* 引入字体 */
    @import url('https://fonts.googleapis.com/css2?family=Merriweather:wght@300;400;700&family=Inter:wght@400;500;600&display=swap');
    
    :root {
        --bg-color: #FEFDF9;
        --sidebar-bg: #F4F3EF;
        --text-primary: #38352F;
        --text-secondary: #777570;
        --accent-color: #D97757;
        --border-color: #E6E4DD;
        --card-bg: #FFFFFF;
        --hover-bg: #EAE9E4;
    }
    
    /* 全局重置 */
    .stApp {
        background-color: var(--bg-color);
        color: var(--text-primary);
        font-family: 'Inter', sans-serif;
    }
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* ==================== 侧边栏 ==================== */
    [data-testid="stSidebar"] {
        background-color: var(--sidebar-bg);
        border-right: 1px solid var(--border-color);
    }
    
    .sidebar-header {
        padding: 24px 16px 12px;
        margin-bottom: 24px;
        font-family: 'Merriweather', serif;
    }
    
    .sidebar-header h1 {
        font-size: 1.25rem; font-weight: 700; margin: 0; display: flex; align-items: center; gap: 8px; color: var(--text-primary);
    }
    
    .nav-section {
        color: var(--text-secondary); font-size: 0.75rem; font-weight: 600; letter-spacing: 0.05em; padding: 0 16px; margin-bottom: 8px; text-transform: uppercase;
    }
    
    /* 侧边栏按钮 */
    [data-testid="stSidebar"] .stButton > button {
        background-color: transparent !important;
        border: none !important;
        box-shadow: none !important;
        padding: 8px 12px !important;
        min-height: auto !important;
        font-size: 0.9rem !important;
        color: var(--text-primary) !important;
        font-weight: 400 !important;
        border-radius: 6px !important;
        justify-content: flex-start !important;
    }

    [data-testid="stSidebar"] .stButton > button:hover {
        background-color: var(--hover-bg) !important;
    }
    
    /* ==================== 消息流 ==================== */
    .chat-container {
        max-width: 768px;
        margin: 0 auto;
        padding-bottom: 120px; /* 留出底部空间 */
    }
    
    .user-msg {
        background-color: #F4F3EF; color: var(--text-primary); padding: 10px 16px; border-radius: 20px; border-bottom-right-radius: 4px; max-width: 80%; margin-left: auto; margin-bottom: 24px; box-shadow: 0 1px 2px rgba(0,0,0,0.05); font-size: 1rem;
    }
    
    .agent-msg-row {
        display: flex; gap: 16px; margin-bottom: 24px;
    }
    
    .agent-avatar {
        width: 32px; height: 32px; border-radius: 50%; background: #FDFBF7; border: 1px solid #E6E4DD; display: flex; align-items: center; justify-content: center; color: #D97757; font-family: 'Merriweather', serif; font-weight: 700; flex-shrink: 0;
    }
    
    .agent-content {
        color: var(--text-primary); font-size: 1rem; line-height: 1.6; padding-top: 4px;
    }
    
    /* ==================== 底部输入栏 (Simplified) ==================== */
    
    /* 底部固定区域 - 使用 Streamlit 自带 Form 容器 */
    [data-testid="stForm"] {
        position: fixed !important;
        bottom: 20px !important;
        left: 50% !important;
        transform: translateX(-50%) !important;
        width: 700px !important;
        max-width: 90% !important;
        z-index: 10000 !important;
        background: white !important;
        border: 1px solid #E6E4DD !important;
        border-radius: 26px !important;
        padding: 8px 16px !important;
        box-shadow: 0 4px 20px rgba(0,0,0,0.1) !important;
    }
    
    /* 隐藏 Form 内部所有 Label */
    [data-testid="stForm"] label {
        display: none !important;
    }
    
    /* Form 内部的 HorizontalBlock (columns) */
    [data-testid="stForm"] [data-testid="stHorizontalBlock"] {
        align-items: center !important;
        gap: 8px !important;
    }
    
    /* Form 内部的 Column */
    [data-testid="stForm"] [data-testid="column"] {
        padding: 0 !important;
        display: flex !important;
        align-items: center !important;
    }
    
    /* Text Input Styling */
    [data-testid="stForm"] [data-testid="stTextInput"] {
        width: 100% !important;
    }
    
    [data-testid="stForm"] [data-testid="stTextInput"] input {
        border: none !important;
        background: transparent !important;
        padding: 10px !important;
        height: 44px !important;
        font-size: 1rem !important;
        box-shadow: none !important;
    }
    
    [data-testid="stForm"] [data-testid="stTextInput"] input:focus {
        outline: none !important;
        box-shadow: none !important;
    }
    
    /* Submit Button Styling */
    [data-testid="stForm"] [data-testid="stFormSubmitButton"] button {
        background: #D97757 !important;
        border: none !important;
        color: white !important;
        width: 44px !important;
        height: 44px !important;
        border-radius: 22px !important;
        padding: 0 !important;
        font-size: 18px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
    }
    
    [data-testid="stForm"] [data-testid="stFormSubmitButton"] button:hover {
        background: #C66A4A !important;
    }
    
    /* ==================== Zero State ==================== */
    .zero-state { text-align: center; padding-top: 15vh; }
    .greeting { font-family: 'Merriweather', serif; font-size: 2.5rem; color: var(--text-primary); margin-bottom: 40px; }
    
    /* Suggestion Cards (Main Area Buttons) */
    .main .stButton > button {
        background-color: var(--card-bg);
        border: 1px solid var(--border-color);
        color: var(--text-primary);
        text-align: left;
        padding: 16px;
        font-weight: 500;
        border-radius: 12px;
        box-shadow: 0 1px 2px rgba(0,0,0,0.02);
        display: block;
        height: auto;
        width: 100%;
    }
    
    .main .stButton > button:hover {
        border-color: var(--accent-color);
        background-color: #FFFBF9;
        color: var(--accent-color);
    }
    
    /* File Uploader in Sidebar (Clean Style) */
    [data-testid="stSidebar"] [data-testid="stFileUploader"] label {
        display: none !important;
    }
    
    [data-testid="stSidebar"] [data-testid="stFileUploader"] section {
        border: 1px dashed var(--border-color) !important;
        border-radius: 8px !important;
        padding: 12px !important;
        background: white !important;
    }
    
    [data-testid="stSidebar"] [data-testid="stFileUploader"] button {
        background: var(--accent-color) !important;
        color: white !important;
        border: none !important;
        border-radius: 6px !important;
    }
    </style>
    """

def init_session_state():
    if "projects" not in st.session_state: st.session_state.projects = []
    if "current_project_id" not in st.session_state: st.session_state.current_project_id = None

def create_new_project(name, ptype, source=None):
    p = {"id": str(uuid.uuid4())[:8], "name": name, "type": ptype, "source": source, "messages": [], "progress": 0.0}
    st.session_state.projects.insert(0, p)
    st.session_state.current_project_id = p["id"]
    return p

def get_current_project():
    if not st.session_state.current_project_id: return None
    for p in st.session_state.projects:
        if p["id"] == st.session_state.current_project_id: return p
    return None

def add_message(role, content):
    p = get_current_project()
    if p: p["messages"].append({"role": role, "content": content})

# ============================================================================
# Core UI Logic
# ============================================================================

def render_sidebar():
    with st.sidebar:
        st.markdown('<div class="sidebar-header"><h1><span style="color:#D97757">✦</span> XLearning</h1></div>', unsafe_allow_html=True)
        
        if st.button("✎  Start new chat", key="new_chat"):
            st.session_state.current_project_id = None
            st.experimental_rerun()
        
        st.markdown("---")
        
        # 📎 文件上传放在侧边栏 - 清晰、稳定
        st.markdown('<div class="nav-section">📎 Upload PDF</div>', unsafe_allow_html=True)
        uploaded_file = st.file_uploader("", type=["pdf"], key="sidebar_upload")
        if uploaded_file:
            name = uploaded_file.name.replace(".pdf", "")[:20]
            # Check if this file is already the current project
            p = get_current_project()
            if not p or p.get("source") != uploaded_file.name:
                create_new_project(name, "pdf", uploaded_file.name)
                add_message("agent", f"I've loaded **{uploaded_file.name}**. What would you like to learn from it?")
                st.experimental_rerun()
        
        st.markdown("---")
        
        st.markdown('<div class="nav-section" style="margin-top:24px;">Recents</div>', unsafe_allow_html=True)
        for p in st.session_state.projects[:8]:
            label = f"{'📄' if p['type']=='pdf' else '💬'} {p['name'][:18]}..."
            if st.button(label, key=f"nav_{p['id']}"):
                st.session_state.current_project_id = p['id']
                st.experimental_rerun()
        
        st.markdown('<div style="position:absolute;bottom:20px;left:16px;right:16px;"><hr></div>', unsafe_allow_html=True)

def render_input_bar():
    """渲染简化的底部输入栏 - 只有文本输入和发送按钮"""
    
    # Spacer to prevent content from hiding behind fixed input bar
    st.markdown('<div style="height: 100px;"></div>', unsafe_allow_html=True)
    
    def handle_input(text):
        if not text:
            return
        p = get_current_project()
        if not p:
            create_new_project(text[:15], "topic", text)
            add_message("user", text)
            add_message("agent", f"Let's explore **{text}** together!")
        else:
            add_message("user", text)
            if text.lower() == "/quiz":
                add_message("agent", "🎓 Let's test your knowledge! Here's a quick quiz...")
            else:
                add_message("agent", f"Thinking about: {text}...")
        st.experimental_rerun()

    # Clean Form with just Text Input and Send Button
    with st.form("chat_form", clear_on_submit=True):
        col1, col2 = st.columns([0.9, 0.1])
        
        with col1:
            text = st.text_input("", key="chat_input", placeholder="Message XLearning...")
        
        with col2:
            submitted = st.form_submit_button("↑")
            
        if submitted and text:
            handle_input(text)

def render_main():
    p = get_current_project()
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    
    if not p:
        # Zero State
        st.markdown('<div class="zero-state"><div class="greeting">Good afternoon, Bruno.</div></div>', unsafe_allow_html=True)
        
        # Suggestions
        c1, c2, c3 = st.columns(3)
        with c1: 
            if st.button("📄 Analyze a PDF\n\nUpload in the sidebar", key="s1"): 
                pass
        with c2:
            if st.button("🔗 GitHub Repo\n\nAnalyze repository", key="s2"): 
                pass
        with c3:
            if st.button("🎓 Study Plan\n\nCreate learning path", key="s3"): 
                pass
    else:
        # Chat Messages
        for m in p["messages"]:
            if m["role"] == "user":
                st.markdown(f'<div class="user-msg">{m["content"]}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="agent-msg-row"><div class="agent-avatar">X</div><div class="agent-content">{m["content"]}</div></div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Render the simplified input bar
    render_input_bar()

def main():
    st.set_page_config(page_title="XLearning", page_icon="🎓", layout="wide", initial_sidebar_state="expanded")
    st.markdown(get_premium_styles(), unsafe_allow_html=True)
    init_session_state()
    render_sidebar()
    render_main()

if __name__ == "__main__":
    main()
