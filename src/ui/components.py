"""
UI 组件模块 - 重构版本 (匹配 Mockup 设计)
"""

import streamlit as st
from contextlib import contextmanager


def render_sidebar_nav() -> str:
    """
    渲染侧边栏导航 - 使用按钮模拟菜单项
    
    Returns:
        选择的页面 (plan/quiz/progress)
    """
    # 初始化 session state
    if "current_page" not in st.session_state:
        st.session_state.current_page = "plan"
    
    with st.sidebar:
        # Logo / Title
        st.markdown("""
        <div style="padding: 10px 0 20px 0;">
            <h2 style="margin: 0; color: #1F2937;">🎓 XLearning</h2>
        </div>
        """, unsafe_allow_html=True)
        
        # Navigation Items
        nav_items = [
            ("📋", "学习计划", "plan"),
            ("📄", "知识测验", "quiz"),
            ("📊", "进度追踪", "progress")
        ]
        
        for icon, label, page_key in nav_items:
            is_selected = st.session_state.current_page == page_key
            
            # 用按钮来模拟导航项
            if is_selected:
                # 选中状态 - 显示橙色竖条
                st.markdown(f"""
                <div style="
                    display: flex;
                    align-items: center;
                    padding: 10px 15px;
                    margin: 4px 0;
                    background-color: #FFF7ED;
                    border-radius: 8px;
                    border-left: 4px solid #F97316;
                    cursor: pointer;
                ">
                    <span style="margin-right: 10px;">{icon}</span>
                    <span style="color: #F97316; font-weight: 600;">{label}</span>
                </div>
                """, unsafe_allow_html=True)
            else:
                # 非选中状态 - 使用按钮
                if st.button(f"{icon} {label}", key=f"nav_{page_key}"):
                    st.session_state.current_page = page_key
                    st.experimental_rerun()
        
        st.markdown("---")
        
        # Bottom Section
        st.markdown("""
        <div style="margin-top: 20px;">
        """, unsafe_allow_html=True)
        
        if st.button("⚙️ 设置", key="nav_settings"):
            st.info("设置功能即将上线")
        
        if st.button("❓ 帮助", key="nav_help"):
            st.info("XLearning Agent v0.1")
        
        st.markdown("</div>", unsafe_allow_html=True)
        
    return st.session_state.current_page


def render_chat_message(role: str, content: str):
    """
    渲染聊天消息 (兼容模式)
    """
    if role == "user":
        bg_color = "#FFF7ED"  # Orange-50
        border_color = "#F97316"
        name = "你"
    else:
        bg_color = "#F9FAFB"  # Gray-50
        border_color = "#E5E7EB"
        name = "🤖 XLearning Agent"

    st.markdown(f"""
    <div style="
        background-color: {bg_color};
        border-left: 3px solid {border_color};
        padding: 12px 16px;
        margin: 8px 0;
        border-radius: 0 8px 8px 0;
    ">
        <div style="font-weight: 600; margin-bottom: 6px; color: #374151;">{name}</div>
        <div style="color: #4B5563; white-space: pre-wrap;">{content}</div>
    </div>
    """, unsafe_allow_html=True)


@contextmanager
def render_expandable_section(title: str, icon: str = "▶", expanded: bool = False):
    """
    渲染可折叠的手风琴区块 (模拟 Mockup 中的 Week 区块)
    """
    # 使用 Streamlit 的 expander
    with st.expander(f"{icon} {title}", expanded=expanded):
        yield


@contextmanager
def render_card_container(title: str, icon: str = "📄"):
    """
    渲染卡片容器 (简化版)
    """
    st.markdown(f"""
    <div style="
        background-color: #F9FAFB;
        border: 1px solid #E5E7EB;
        border-radius: 12px;
        padding: 20px;
        margin: 16px 0;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    ">
        <div style="display: flex; align-items: center; margin-bottom: 12px;">
            <span style="font-size: 20px; margin-right: 8px;">{icon}</span>
            <h3 style="margin: 0; color: #1F2937; font-weight: 600;">{title}</h3>
        </div>
    """, unsafe_allow_html=True)
    
    yield
    
    st.markdown("</div>", unsafe_allow_html=True)


def render_progress_bar(label: str, value: float, color: str = "#F97316"):
    """
    渲染带标签的进度条 (匹配 Mockup 中的橙色渐变进度条)
    """
    percentage = int(value * 100)
    st.markdown(f"""
    <div style="margin: 8px 0;">
        <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
            <span style="font-size: 14px; color: #4B5563;">{label}</span>
            <span style="font-size: 14px; color: #F97316; font-weight: 600;">{percentage}%</span>
        </div>
        <div style="background-color: #E5E7EB; border-radius: 4px; height: 8px; overflow: hidden;">
            <div style="
                background: linear-gradient(90deg, #FDBA74, #F97316);
                width: {percentage}%;
                height: 100%;
                border-radius: 4px;
            "></div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_code_block(code: str, language: str = "python"):
    """
    渲染代码块 (匹配 Mockup 中的代码片段样式)
    """
    st.markdown(f"""
    <div style="
        background-color: #1F2937;
        border-radius: 8px;
        padding: 16px;
        margin: 12px 0;
        font-family: 'Fira Code', 'Consolas', monospace;
        font-size: 13px;
        color: #F3F4F6;
        overflow-x: auto;
    ">
        <pre style="margin: 0; white-space: pre-wrap;">{code}</pre>
    </div>
    """, unsafe_allow_html=True)


def render_orange_button(label: str, key: str) -> bool:
    """
    渲染橙色按钮 (匹配 Mockup 中的 "Start Week 1 Quiz" 按钮)
    """
    # 由于 Streamlit 1.12.0 不支持 type="primary", 我们用 HTML + session state 模拟
    clicked = st.button(label, key=key)
    
    # 注入橙色样式到最后一个按钮
    st.markdown(f"""
    <style>
        div[data-testid="stButton"] button:last-child {{
            background-color: #F97316 !important;
            color: white !important;
            border: none !important;
            padding: 10px 24px !important;
            border-radius: 8px !important;
            font-weight: 600 !important;
        }}
        div[data-testid="stButton"] button:last-child:hover {{
            background-color: #EA580C !important;
        }}
    </style>
    """, unsafe_allow_html=True)
    
    return clicked
