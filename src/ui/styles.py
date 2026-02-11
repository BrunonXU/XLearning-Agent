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
        --sidebar-width: 420px;
        /* docs/ui_mockups 附录配色 */
        --primary: #F97316;
        --success: #22C55E;
        --error: #EF4444;
        --warning: #F59E0B;
        --info: #3B82F6;
        --secondary-bg: #F3F4F6;
    }
    
    .stApp {
        background-color: var(--bg-color);
        color: var(--text-primary);
        font-family: 'Inter', sans-serif;
        font-size: 18px;
    }
    
    /* ================================================================
       SIDEBAR：固定 420px，禁用拖拽，彻底隐藏滚动条
       ================================================================ */
    [data-testid="stSidebar"],
    section[data-testid="stSidebar"] {
        background-color: var(--sidebar-bg) !important;
        border-right: 1px solid #E6E4DD;
        width: var(--sidebar-width) !important;
        min-width: var(--sidebar-width) !important;
        max-width: var(--sidebar-width) !important;
        flex: 0 0 var(--sidebar-width) !important;
        overflow-y: auto !important;
        scrollbar-width: none !important;
        -ms-overflow-style: none !important;
    }
    [data-testid="stSidebar"]::-webkit-scrollbar,
    [data-testid="stSidebar"]::-webkit-scrollbar-track,
    [data-testid="stSidebar"]::-webkit-scrollbar-thumb,
    [data-testid="stSidebar"] > div::-webkit-scrollbar,
    [data-testid="stSidebar"] > div::-webkit-scrollbar-track,
    [data-testid="stSidebar"] > div::-webkit-scrollbar-thumb,
    section[data-testid="stSidebar"]::-webkit-scrollbar,
    section[data-testid="stSidebar"] > div::-webkit-scrollbar,
    section[data-testid="stSidebar"] > div > div::-webkit-scrollbar,
    [data-testid="stSidebar"] *::-webkit-scrollbar {
        display: none !important;
        width: 0 !important;
        height: 0 !important;
    }
    [data-testid="stSidebar"] * {
        scrollbar-width: none !important;
        -ms-overflow-style: none !important;
    }

    /* 遮挡拖拽把手：在侧边栏右边缘叠一层，阻止拖拽 */
    [data-testid="stSidebar"] {
        position: relative !important;
    }
    [data-testid="stSidebar"]::after {
        content: '';
        position: absolute;
        right: -8px;
        top: 0;
        bottom: 0;
        width: 18px;
        background: transparent;
        z-index: 99999;
        pointer-events: auto !important;
        cursor: default !important;
    }

    /* 关闭按钮(×)改为折叠箭头(◀) */
    [data-testid="baseButton-headerNoPadding"] svg,
    [data-testid="baseButton-header"] svg {
        display: none !important;
    }
    [data-testid="baseButton-headerNoPadding"]::before,
    [data-testid="baseButton-header"]::before {
        content: '◀' !important;
        font-size: 18px;
        color: #888;
    }
    [data-testid="baseButton-headerNoPadding"]:hover::before,
    [data-testid="baseButton-header"]:hover::before {
        color: var(--accent-color);
    }

    /* ================================================================
       主内容区
       ================================================================ */
    .block-container {
        padding-right: 2rem !important;
        padding-left: 2rem !important;
        max-width: 100% !important;
        overflow-x: hidden !important;
    }
    
    /* Sidebar Buttons（新对话、历史列表等） */
    [data-testid="stSidebar"] .stButton > button {
        background-color: transparent;
        border: none;
        color: #555;
        text-align: left;
        justify-content: flex-start;
        font-weight: 500;
        font-size: 13px !important;
        padding: 6px 10px;
        width: 100%;
        min-height: 36px;
        border-radius: 6px;
        transition: background-color 0.15s;
    }
    [data-testid="stSidebar"] .stButton > button:hover {
        background-color: #EAE9E4;
        color: #000;
    }
    .sidebar-footer {
        font-size: 12px;
        color: #9CA3AF;
        padding: 12px 0;
        text-align: center;
    }
    
    /* Tabs font size */
    button[data-baseweb="tab"] div {
        font-size: 18px !important;
        font-weight: 600 !important;
    }
    
    /* Sidebar Logo（仅展示） */
    .huge-sidebar-logo {
        font-size: 28px;
        font-weight: 800;
        text-align: center;
        margin-top: 12px;
        margin-bottom: 16px;
        color: var(--accent-color);
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

    /* ================================================================
       聊天气泡
       ================================================================ */
    .chat-row {
        display: flex;
        margin-bottom: 22px;
        align-items: flex-start;
        width: 100%;
    }
    .chat-bubble {
        padding: 16px 20px;
        border-radius: 14px;
        background-color: white;
        color: #1a1a1a;
        max-width: 92%;
        line-height: 1.6;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
        position: relative;
        flex: 1;
    }
    .user-bubble {
        background-color: #F3F4F6;
        border: 1px solid #E5E7EB;
        border-top-right-radius: 4px;
        font-size: 16px;
    }
    .assistant-bubble {
        background-color: #FFFFFF;
        border: 1px solid #E5E7EB;
        border-top-left-radius: 4px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.06);
    }
    .system-bubble {
        background-color: #F0FDF4;
        border: 1px solid #BBF7D0;
    }
    .chat-bubble-header {
        font-size: 13px;
        font-weight: 600;
        color: #6B7280;
        margin-bottom: 8px;
        text-transform: uppercase;
        letter-spacing: 0.3px;
    }
    .chat-bubble-body {
        font-size: 16px;
        line-height: 1.7;
        color: #1F2937;
        word-wrap: break-word;
        overflow-wrap: break-word;
    }
    .assistant-bubble .chat-bubble-body {
        font-size: 16.5px;
        line-height: 1.75;
    }

    /* Agent Markdown 渲染样式 */
    .chat-bubble-body h1, .chat-bubble-body h2, .chat-bubble-body h3 {
        font-weight: 700;
        margin: 0.8em 0 0.4em 0;
        line-height: 1.4;
        color: #111827;
    }
    .chat-bubble-body h1 { font-size: 1.2em; }
    .chat-bubble-body h2 { font-size: 1.12em; }
    .chat-bubble-body h3 { font-size: 1.05em; }
    .chat-bubble-body h1:first-child,
    .chat-bubble-body h2:first-child,
    .chat-bubble-body h3:first-child { margin-top: 0; }
    .chat-bubble-body hr {
        border: none;
        border-top: 1px solid #E5E7EB;
        margin: 1em 0;
    }
    .chat-bubble-body p { margin: 0.5em 0; }
    .chat-bubble-body p:first-child { margin-top: 0; }
    .chat-bubble-body p:last-child { margin-bottom: 0; }
    .chat-bubble-body ul, .chat-bubble-body ol {
        margin: 0.5em 0;
        padding-left: 1.5em;
    }
    .chat-bubble-body li { margin: 0.3em 0; }
    .chat-bubble-body strong { font-weight: 700; }
    .chat-bubble-body em { font-style: italic; }
    .chat-bubble-body code {
        background: var(--secondary-bg);
        padding: 2px 6px;
        border-radius: 4px;
        font-size: 0.9em;
        font-family: 'Consolas', 'Monaco', monospace;
    }
    .chat-bubble-body pre.chat-code-block {
        background: #1F2937;
        color: #F9FAFB;
        padding: 14px 16px;
        border-radius: 8px;
        overflow-x: auto;
        margin: 0.8em 0;
        font-size: 14px;
        line-height: 1.5;
    }
    .chat-bubble-body pre.chat-code-block code {
        background: transparent;
        padding: 0;
        color: inherit;
    }
    .chat-bubble-body blockquote.chat-blockquote {
        border-left: 4px solid var(--info);
        margin: 0.6em 0;
        padding: 8px 14px;
        background: #EFF6FF;
        color: #1E40AF;
        border-radius: 0 6px 6px 0;
    }

    /* 证据来源折叠区 */
    [data-testid="stExpander"] summary {
        font-size: 13px !important;
        color: #6B7280 !important;
    }

    /* 聊天输入框（GPT 风格：白底、宽大） */
    .chat-input-wrap {
        margin-top: 1rem;
        padding: 0;
        background: transparent;
    }
    .chat-input-wrap [data-testid="stTextArea"] {
        background: #FFFFFF !important;
        border: 1px solid #E5E7EB !important;
        border-radius: 12px !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04) !important;
    }
    .chat-input-wrap textarea {
        background: #FFFFFF !important;
        font-size: 15px !important;
        line-height: 1.5 !important;
        padding: 12px 16px !important;
        min-height: 88px !important;
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

    /* ================================================================
       Stepper 固定吸顶（放大、美化）
       ================================================================ */
    .stepper-fixed-spacer {
        height: 72px !important;
        margin: 0 !important;
        flex-shrink: 0 !important;
    }
    .stepper-fixed-wrap {
        position: fixed !important;
        top: 0 !important;
        left: 0 !important;
        right: 0 !important;
        z-index: 999 !important;
        margin-left: var(--sidebar-width) !important;
        overflow: visible !important;
    }
    .stepper-container {
        display: flex !important;
        flex-direction: row !important;
        justify-content: space-between !important;
        align-items: center !important;
        width: 100% !important;
        min-width: 720px !important;
        margin: 0 !important;
        padding: 12px 6% !important;
        gap: 0 4px;
        background: linear-gradient(180deg, #FFFFFF 0%, #F9FAFB 100%) !important;
        box-shadow: 0 2px 16px rgba(0, 0, 0, 0.06);
        border-bottom: 1px solid #E5E7EB;
        overflow: visible !important;
    }
    .stepper-item {
        position: relative !important;
        display: flex !important;
        flex-direction: column !important;
        align-items: center !important;
        flex: 1 0 auto !important;
        min-width: 58px !important;
        max-width: 90px !important;
        z-index: 2 !important;
        flex-shrink: 0 !important;
    }
    .stepper-circle {
        width: 44px !important;
        height: 44px !important;
        border-radius: 50% !important;
        background-color: #E5E7EB;
        color: white;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        font-weight: 700;
        font-size: 18px;
        margin-bottom: 8px;
        border: 2px solid #E5E7EB;
        position: relative !important;
        z-index: 3 !important;
    }
    .stepper-item.active .stepper-circle {
        background-color: var(--primary);
        border-color: var(--primary);
        box-shadow: 0 0 0 5px rgba(249, 115, 22, 0.22);
    }
    .stepper-item.done .stepper-circle {
        background-color: var(--success);
        border-color: var(--success);
    }
    .stepper-label {
        font-size: 13px;
        font-weight: 600;
        color: #9CA3AF;
        white-space: nowrap;
        overflow: visible;
        text-overflow: clip;
        position: relative !important;
        z-index: 3 !important;
    }
    .stepper-item.active .stepper-label {
        color: var(--primary);
    }
    .stepper-line {
        position: absolute;
        top: 22px;
        height: 3px;
        background-color: #E5E7EB;
        width: calc(100% - 24px);
        left: 50%;
        z-index: 1;
    }
    .stepper-item:last-child .stepper-line {
        display: none;
    }

    /* ================================================================
       工作区双列：聊天区 | 固定分隔线 | 准备面板
       直接瞄准 Streamlit 列容器（恰好 2 列时第一列加右边框）
       ================================================================ */
    /* 方案A: data-testid="column" (Streamlit >=1.28) */
    [data-testid="column"]:first-child:nth-last-child(2) {
        border-right: 2px solid #E5E7EB !important;
        padding-right: 1.2rem !important;
    }
    /* 方案B: stHorizontalBlock > div (旧版或不同结构) */
    [data-testid="stHorizontalBlock"] > div:first-child:nth-last-child(2) {
        border-right: 2px solid #E5E7EB !important;
        padding-right: 1.2rem !important;
    }
    /* 方案C: :has() 精确匹配恰好 2 列的容器 */
    [data-testid="stHorizontalBlock"]:has(> :nth-child(2):last-child) > :first-child {
        border-right: 2px solid #E5E7EB !important;
        padding-right: 1.2rem !important;
    }

    /* 右列面板吸顶 + 左边距（与灰色分隔线拉开距离） */
    .right-panel-sticky {
        position: sticky !important;
        top: 72px !important;
        align-self: flex-start !important;
        padding-left: 1.5rem !important;
    }
    [data-testid="stHorizontalBlock"] > div:last-child {
        position: sticky !important;
        top: 72px !important;
        align-self: flex-start !important;
        padding-left: 1.5rem !important;
    }

    /* ================================================================
       Action Banner
       ================================================================ */
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

    /* ================================================================
       Layout tweaks
       ================================================================ */
    .control-panel-container {
        background-color: white;
        border-radius: 12px;
        padding: 24px;
        border: 1px solid #F3F4F6;
        min-height: 500px;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05);
    }

    /* Scrollbar（主内容区） */
    ::-webkit-scrollbar { width: 6px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb { background: #ddd; border-radius: 3px; }
    ::-webkit-scrollbar-thumb:hover { background: #aaa; }
    
    div[data-testid="stForm"] { border: none; padding: 0; }

    /* ================================================================
       首页（去除多余白框感，与背景融合）
       ================================================================ */
    .home-hero {
        text-align: center;
        margin-bottom: 1.5rem;
    }
    .home-title {
        font-size: 1.8rem;
        margin: 0 0 0.3rem 0;
        color: var(--text-primary);
    }
    .home-subtitle {
        color: #6B7280;
        margin: 0;
        font-size: 0.95rem;
    }
    .home-quick-label {
        margin-top: 1.2rem;
        text-align: center;
        color: #9CA3AF;
        font-size: 0.9rem;
    }
    .home-input-wrap {
        background-color: var(--bg-color);
        border-radius: 18px;
        padding: 24px 28px 20px 28px;
        border: 1px solid #E5E7EB;
        max-width: 900px;
        margin: 0 auto;
        box-shadow: 0 4px 20px rgba(15, 23, 42, 0.04);
    }
    .home-input-wrap [data-testid="stTextInput"] input,
    .home-input-wrap textarea {
        font-size: 16px !important;
        background-color: #FFFFFF !important;
        min-height: 80px !important;
    }
    .home-input-wrap [data-testid="stFileUploaderDropzone"] {
        background-color: #F9FAFB !important;
        border: 1px solid #E5E7EB !important;
        border-radius: 10px !important;
    }
    .home-input-wrap [data-testid="stForm"] {
        background: transparent !important;
    }
    .home-input-wrap .stExpander {
        margin-top: 0.5rem !important;
    }

    /* ================================================================
       庆祝页 (mockups 第 7 节)
       ================================================================ */
    .completion-card-wrap {
        max-width: 720px;
        margin: 0 auto 2rem;
    }
    .completion-card {
        background: #FFFFFF;
        border: 1px solid #E5E7EB;
        border-radius: 16px;
        padding: 28px 32px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.06);
    }
    .completion-title {
        font-size: 1.5rem;
        font-weight: 700;
        text-align: center;
        color: #1F2937;
        margin-bottom: 24px;
    }
    .completion-stats {
        display: flex;
        justify-content: center;
        gap: 20px;
        flex-wrap: wrap;
        margin-bottom: 20px;
    }
    .completion-stat-card {
        text-align: center;
        min-width: 120px;
        padding: 18px 20px;
        border-radius: 12px;
        border: 1px solid;
    }
    .completion-stat-success {
        background: #F0FDF4;
        border-color: #BBF7D0;
    }
    .completion-stat-success .stat-value { color: var(--success); }
    .completion-stat-info {
        background: #EFF6FF;
        border-color: #BFDBFE;
    }
    .completion-stat-info .stat-value { color: var(--info); }
    .completion-stat-warning {
        background: #FFFBEB;
        border-color: #FDE68A;
    }
    .completion-stat-warning .stat-value { color: var(--warning); }
    .stat-icon { font-size: 1.8rem; margin-bottom: 4px; }
    .stat-value { font-size: 1.4rem; font-weight: 700; }
    .stat-label { font-size: 13px; color: #6B7280; }
    .completion-summary {
        font-size: 14px;
        color: #4B5563;
    }
    .summary-row { margin: 6px 0; }
    .summary-key {
        display: inline-block;
        width: 72px;
        color: #6B7280;
        font-weight: 500;
    }
    .completion-hr {
        border: none;
        border-top: 1px solid #E5E7EB;
        margin: 20px 0;
    }
    </style>
    """

def inject_styles():
    """Inject CSS into Streamlit app."""
    st.markdown(get_css(), unsafe_allow_html=True)
