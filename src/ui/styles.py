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
        font-size: 18px;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: var(--sidebar-bg);
        border-right: 1px solid #E6E4DD;
        overflow-y: hidden !important; /* Hide Sidebar Scrollbar */
    }
    
    /* Hide scrollbar for Chrome/Safari */
    [data-testid="stSidebar"]::-webkit-scrollbar {
        display: none !important;
    }
    
    /* Increase App Margin to push scrollbar left */
    .block-container {
        padding-right: 5rem !important;
        padding-left: 5rem !important;
        max-width: 100% !important;
    }
    
    /* Sidebar Buttons (Increased size) */
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
    
    /* Tabs font size - SUPER SCALED */
    button[data-baseweb="tab"] div {
        font-size: 40px !important;
        font-weight: 700 !important;
        padding: 5px 15px;
    }
    
    /* Sidebar Huge Logo */
    .huge-sidebar-logo {
        font-size: 64px;
        font-weight: 900;
        text-align: center;
        margin-top: 20px;
        margin-bottom: 40px;
        color: var(--accent-color);
        display: flex;
        align-items: center;
        justify-content: center;
        flex-direction: column;
        width: 100%;
    }
    
    /* Sticky Navigation Header (Dynamic Island Style) */
    div[data-testid="stVerticalBlock"]:has(div.sticky-nav) {
        position: sticky;
        top: 0;
        z-index: 1000;
        background-color: rgba(254, 253, 249, 0.9); /* Glassmorphism bg */
        backdrop-filter: blur(10px);
        padding: 15px 10px !important;
        border-radius: 0 0 20px 20px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
        margin-bottom: 40px !important;
    }
    
    .sticky-nav {
        display: none;
    }
    
    /* Custom Navigation Buttons Scale - MASSIVE & UNIFORM WIDTH */
    button[kind="secondary"] div[data-testid="stMarkdownContainer"] p, 
    button[kind="primary"] div[data-testid="stMarkdownContainer"] p {
        font-size: 26px !important;
        font-weight: 700 !important;
    }
    button[kind="secondary"], button[kind="primary"] {
        padding: 0 !important;
        height: 64px !important;
        min-width: 180px !important; /* Force Uniformity */
        border-radius: 12px !important;
        border: 2px solid transparent !important;
        transition: all 0.2s ease;
    }
    button[kind="secondary"]:hover {
        background-color: #E6E4DD !important;
        border-color: #D1D5DB !important;
    }
    
    /* Alert/Error Width Alignment - Matches Chat Bubble */
    [data-testid="stNotification"] {
        max-width: 82% !important;
        border-radius: 18px !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.02) !important;
    }
    
    /* Sidebar New Chat Button - PROMINENT */
    .new-chat-container {
        padding: 10px 0;
        display: flex;
        justify-content: center;
        width: 100%;
        margin-top: 10px;
    }
    .new-chat-container button {
        width: 85% !important;
        border: 1px solid var(--accent-color) !important;
        background-color: white !important;
        color: var(--accent-color) !important;
        font-size: 20px !important;
        font-weight: 600 !important;
        padding: 10px !important;
        border-radius: 8px !important;
        display: flex !important;
        justify-content: center !important;
    }
    .new-chat-container button:hover {
        background-color: var(--accent-color) !important;
        color: white !important;
    }

    /* Legacy Chat Message Styles */
    .chat-row {
        display: flex;
        margin-bottom: 24px;
        align-items: flex-start;
    }
    .chat-bubble {
        padding: 18px 22px;
        border-radius: 18px;
        background-color: #FFFFFF;
        color: #1a1a1a;
        max-width: 82%;
        line-height: 1.6;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05), 0 4px 12px rgba(0,0,0,0.02);
        font-size: 18px;
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
    
    /* INPUT AREA OVERHAUL (Targeting st.text_input) */
    /* Remove orange outline (.st-bt/focus) */
    .stInput input:focus {
        border-color: #D1D5DB !important;
        box-shadow: 0 0 0 1px #D1D5DB !important;
        outline: none !important;
    }
    .stInput input {
        border-radius: 20px !important;
        padding: 15px 25px !important;
        background-color: #FFFFFF !important;
        border: 1px solid #E5E7EB !important;
        font-size: 20px !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
    }
    
    /* Fix potential horizontal scroll */
    .block-container {
        overflow-x: hidden !important;
    }
    
    /* Scrollbar Styling - THICKER & POSITIVE POSITION */
    ::-webkit-scrollbar {
        width: 12px; /* Thicker */
    }
    ::-webkit-scrollbar-track {
        background: #f1f1f1;
        border-radius: 10px;
    }
    ::-webkit-scrollbar-thumb {
        background: #ccc;
        border-radius: 10px;
        border: 3px solid #f1f1f1; /* Padding look */
    }
    ::-webkit-scrollbar-thumb:hover {
        background: #888;
    }

    /* Legacy Chat Message Styles */
    .chat-row {
...
    div[data-testid="stForm"] {
        border: none;
        padding: 0;
    }
    </style>
    """

def inject_styles():
    """Inject CSS into Streamlit app."""
    st.markdown(get_css(), unsafe_allow_html=True)
