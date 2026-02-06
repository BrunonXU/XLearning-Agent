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
    
    /* Legacy Chat Message Styles */
    .chat-row {
        display: flex;
        margin-bottom: 24px;
        align-items: flex-start;
    }
    .chat-bubble {
        padding: 16px 20px;
        border-radius: 18px;
        background-color: #FFFFFF;
        color: #1a1a1a;
        max-width: 80%;
        line-height: 1.6;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05), 0 4px 12px rgba(0,0,0,0.02);
        font-size: 16px;
    }
    .user-bubble {
        background-color: #F3F4F6; /* Light Gray for User */
        border-top-right-radius: 4px;
    }
    .assistant-bubble {
        background-color: #FFFFFF;
        border: 1px solid #E5E7EB;
        border-top-left-radius: 4px;
    }
    .avatar-icon {
        font-size: 24px;
        margin-right: 16px;
        margin-top: 4px;
        width: 40px;
        height: 40px;
        display: flex;
        align-items: center;
        justify-content: center;
        background: #F9FAFB;
        border-radius: 50%;
        border: 1px solid #E5E7EB;
    }
    
    /* Quiz & Radio */
    div[data-testid="stRadio"] > label {
        display: none;
    }
    
    /* Input Area Polish */
    div[data-testid="stForm"] {
        border: none;
        padding: 0;
    }
    </style>
    """

def inject_styles():
    """Inject CSS into Streamlit app."""
    st.markdown(get_css(), unsafe_allow_html=True)
