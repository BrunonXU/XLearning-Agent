"""
XLearning Agent - Main UI Entry Point (src/ui/app.py)
=====================================================
Initializes state, styles, layout, and renderer.
"""

import streamlit as st
from src.ui.state import init_session_state, t
from src.ui.styles import inject_styles
from src.ui.layout import render_sidebar, render_main_area

def main():
    # 1. Page Config
    st.set_page_config(
        page_title="XLearning Agent",
        page_icon="🎓",
        layout="wide",
        initial_sidebar_state="expanded",
        menu_items={
            'Get Help': 'https://github.com/BrunonXU/XLearning-Agent',
            'Report a bug': "https://github.com/BrunonXU/XLearning-Agent/issues",
            'About': "### XLearning Agent\n你的 AI 学习助手。支持 PDF 实时分析、RAG 检索与智能规划。"
        }
    )
    
    # 2. Inject CSS
    inject_styles()
    
    # 3. Initialize State
    init_session_state()
    
    
    # 3.1 Handle Background Processing
    # No longer needed here, moved to end.
    pass
    
    # 4. Render Layout
    render_sidebar()
    render_main_area()
    
    # 5. Handle Background Processing (Last step to allow UI to render first)
    from src.ui.logic import process_pending_chat
    process_pending_chat()

if __name__ == "__main__":
    main()
