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
        font-size: 18px;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: var(--sidebar-bg);
        border-right: 1px solid #E6E4DD;
        overflow-y: hidden !important;
    }
    
    [data-testid="stSidebar"]::-webkit-scrollbar {
        display: none !important;
    }
    
    .block-container {
        padding-right: 5rem !important;
        padding-left: 5rem !important;
        max-width: 100% !important;
        overflow-x: hidden !important;
    }
    
    /* Sidebar Buttons */
    [data-testid="stSidebar"] .stButton > button {
        background-color: transparent;
        border: none;
        color: #555;
        text-align: left;
        justify-content: flex-start;
        font-weight: 500;
        font-size: 18px !important;
        padding: 8px 12px;
    }
    [data-testid="stSidebar"] .stButton > button:hover {
        background-color: #EAE9E4;
        color: #000;
    }
    
    /* Tabs font size */
    button[data-baseweb="tab"] div {
        font-size: 18px !important;
        font-weight: 600 !important;
    }
    
    /* Sidebar Huge Logo */
    .huge-sidebar-logo {
        font-size: 38px;
        font-weight: 800;
        text-align: center;
        margin-top: 15px;
        margin-bottom: 25px;
        color: var(--accent-color);
        display: flex;
        align-items: center;
        justify-content: center;
        flex-direction: column;
        width: 100%;
    }
    
    /* Custom Navigation Buttons */
    button[kind="secondary"] div[data-testid="stMarkdownContainer"] p, 
    button[kind="primary"] div[data-testid="stMarkdownContainer"] p {
        font-size: 16px !important;
        font-weight: 600 !important;
    }
    button[kind="secondary"], button[kind="primary"] {
        padding: 4px 10px !important;
        height: 42px !important;
        min-width: 120px !important;
        border-radius: 8px !important;
        border: 2px solid transparent !important;
    }
    
    /* Chat Bubble Styles */
    .chat-row {
        display: flex;
        margin-bottom: 20px;
        align-items: flex-start;
        width: 100%;
    }
    .chat-bubble {
        padding: 14px 18px;
        border-radius: 12px;
        background-color: white;
        color: #1a1a1a;
        max-width: 85%;
        line-height: 1.5;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        font-size: 16px;
        position: relative;
    }
    .user-bubble {
        background-color: #F3F4F6;
        border-top-right-radius: 2px;
    }
    .assistant-bubble {
        background-color: white;
        border: 1px solid #E5E7EB;
        border-top-left-radius: 2px;
    }
    .avatar-icon {
        font-size: 20px;
        margin-right: 12px;
        width: 36px;
        height: 36px;
        display: flex;
        align-items: center;
        justify-content: center;
        background: #F9FAFB;
        border-radius: 50%;
        border: 1px solid #E5E7EB;
        flex-shrink: 0;
    }

    /* Loading dots */
    @keyframes blink { 0% { opacity: .2; } 20% { opacity: 1; } 100% { opacity: .2; } }
    .loading-dots { animation: blink 1.4s infinite both; font-weight: bold; }

    /* === UI 2.0: Stepper === */
    .stepper-container {
        display: flex !important;
        flex-direction: row !important;
        justify-content: space-around !important;
        align-items: center !important;
        width: 100% !important;
        margin: 0 0 25px 0 !important;
        padding: 15px 5% !important;
        position: sticky !important;
        top: 0 !important;
        z-index: 999 !important;
        background-color: white !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        border-bottom: 1px solid #f0f0f0;
    }
    .stepper-item {
        display: flex !important;
        flex-direction: column !important;
        align-items: center !important;
        flex: 1 !important;
    }
    .stepper-circle {
        width: 30px !important;
        height: 30px !important;
        border-radius: 50% !important;
        background-color: #E5E7EB;
        color: white;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        font-weight: bold;
        font-size: 14px;
        margin-bottom: 5px;
        border: 2px solid #E5E7EB;
    }
    .stepper-item.active .stepper-circle {
        background-color: var(--accent-color);
        border-color: var(--accent-color);
        box-shadow: 0 0 0 4px rgba(217, 119, 87, 0.15);
    }
    .stepper-item.done .stepper-circle {
        background-color: #10B981;
        border-color: #10B981;
    }
    .stepper-label {
        font-size: 13px;
        font-weight: 600;
        color: #9CA3AF;
    }
    .stepper-item.active .stepper-label {
        color: var(--accent-color);
    }
    .stepper-line {
        position: absolute;
        top: 15px;
        height: 2px;
        background-color: #E5E7EB;
        width: 100%;
        left: 50%;
        z-index: 1;
    }
    .stepper-item:last-child .stepper-line {
        display: none;
    }

    /* === UI 2.0: Action Banner === */
    .action-banner {
        background-color: #FEF3C7;
        border: 1px solid #FDE68A;
        border-radius: 10px;
        padding: 12px 18px;
        margin-top: 20px;
        display: flex;
        flex-direction: column;
        gap: 10px;
    }
    .action-text {
        font-size: 14px;
        color: #92400E;
        font-weight: 500;
        line-height: 1.4;
    }

    /* Layout tweaks */
    .control-panel-container {
        background-color: white;
        border-radius: 12px;
        padding: 24px;
        border: 1px solid #F3F4F6;
        min-height: 500px;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05);
    }

    /* Scrollbar */
    ::-webkit-scrollbar { width: 8px; }
    ::-webkit-scrollbar-track { background: #f1f1f1; }
    ::-webkit-scrollbar-thumb { background: #ccc; border-radius: 4px; }
    ::-webkit-scrollbar-thumb:hover { background: #888; }
    
    div[data-testid="stForm"] { border: none; padding: 0; }
    </style>
    """

def inject_styles():
    """Inject CSS into Streamlit app."""
    st.markdown(get_css(), unsafe_allow_html=True)
