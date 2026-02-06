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
        initial_sidebar_state="expanded"
    )
    
    # 2. Inject CSS
    inject_styles()
    
    # 3. Initialize State
    init_session_state()
    
    # 4. Render Layout
    render_sidebar()
    render_main_area()

if __name__ == "__main__":
    main()
