"""
XLearning Agent - UI Styles
===========================
Handles: CSS injection for a premium, clean look (Claude-like).
"""

import streamlit as st

def get_css() -> str:
    """Return the CSS string."""
    return """
    <style>
    /* Headers */
    @import url('https://fonts.googleapis.com/css2?family=Merriweather:wght@300;400;700&family=Inter:wght@400;500;600&display=swap');
    
    :root {
        --bg-color: #FEFDF9;
        --text-primary: #38352F;
        --accent-color: #D97757;
        --sidebar-bg: #F4F3EF;
    }
    
    .stApp {
        background-color: var(--bg-color);
        color: var(--text-primary);
        font-family: 'Inter', sans-serif;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: var(--sidebar-bg);
        border-right: 1px solid #E6E4DD;
    }
    
    /* Buttons in Sidebar */
    [data-testid="stSidebar"] .stButton > button {
        background-color: transparent;
        border: none;
        color: #555;
        text-align: left;
        justify-content: flex-start;
        font-weight: 500;
    }
    [data-testid="stSidebar"] .stButton > button:hover {
        background-color: #EAE9E4;
        color: #000;
    }
    
    /* Legacy Chat Message Styles (1.12.0) */
    .chat-row {
        display: flex;
        margin-bottom: 20px;
        align-items: flex-start;
    }
    .chat-bubble {
        padding: 12px 16px;
        border-radius: 12px;
        background-color: #F4F3EF;
        color: var(--text-primary);
        max-width: 85%;
        line-height: 1.6;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
    }
    .assistant-bubble {
        background-color: transparent;
        border: 1px solid #E6E4DD;
    }
    .user-bubble {
        background-color: #F4F3EF;
    }
    .avatar-icon {
        font-size: 1.5rem;
        margin-right: 15px;
        margin-top: 5px;
        min-width: 40px;
        text-align: center;
    }
    
    /* Hide radio labels in Quiz */
    div[data-testid="stRadio"] > label {
        display: none;
    }
    </style>
    """

def inject_styles():
    """Inject CSS into Streamlit app."""
    st.markdown(get_css(), unsafe_allow_html=True)
