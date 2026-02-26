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
        --bg-color: #FFFFFF;
        --text-primary: #38352F;
        --accent-color: #D97757;
        --sidebar-bg: #F4F3EF;
        --sidebar-width: 235px;
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

    /* 遮挡拖拽把手：允许侧边栏折叠/展开 */
    [data-testid="stSidebar"] {
        position: relative !important;
        transition: width 0.3s, min-width 0.3s, max-width 0.3s !important;
    }

    /* 侧边栏折叠时：宽度归零，主内容区自动扩展 */
    [data-testid="stSidebar"][aria-expanded="false"],
    section[data-testid="stSidebar"][aria-expanded="false"] {
        width: 0 !important;
        min-width: 0 !important;
        max-width: 0 !important;
        flex: 0 0 0 !important;
        overflow: hidden !important;
        border-right: none !important;
    }

    /* 主内容区随侧边栏折叠自适应 */
    .block-container {
        transition: margin-left 0.3s, padding-left 0.3s !important;
    }

    /* 底部 footer 也跟随侧边栏折叠 */
    .workspace-footer {
        transition: left 0.3s !important;
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
        padding-top: 1rem !important;
        padding-bottom: 1rem !important;
        max-width: 100% !important;
        overflow-x: hidden !important;
        overflow-y: hidden !important;
    }
    
    /* 侧边栏内部 padding 缩减：让文字区域更宽 */
    [data-testid="stSidebar"] > div:first-child {
        padding-left: 8px !important;
        padding-right: 8px !important;
    }
    [data-testid="stSidebar"] .block-container,
    [data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
        padding-left: 0 !important;
        padding-right: 0 !important;
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
        padding: 4px 8px;
        width: 100%;
        min-height: 34px;
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

    /* 侧边栏对话列表 */
    .sess-item {
        font-size: 13px;
        font-weight: 500;
        color: #555;
        padding: 5px 8px;
        border-radius: 6px;
        margin-bottom: 2px;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    .sess-active {
        background-color: #EAE9E4;
        color: #000;
        font-weight: 600;
    }
    /* 当前对话操作按钮（改名/删除）紧凑行内布局 */
    .sess-actions-row {
        display: flex;
        gap: 6px;
        margin: 2px 8px 6px 8px;
    }
    .sess-actions-row .sess-btn {
        font-size: 12px;
        padding: 2px 10px;
        border: 1px solid #D1D5DB;
        border-radius: 5px;
        background: transparent;
        color: #555;
        cursor: pointer;
        transition: background 0.15s;
        line-height: 24px;
    }
    .sess-actions-row .sess-btn:hover {
        background: #EAE9E4;
        color: #000;
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
        margin-top: 8px;
        margin-bottom: 12px;
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
    .chat-input-wrap [data-testid="stTextArea"],
    .chat-input-wrap [data-testid="stTextInput"] {
        background: #FFFFFF !important;
        border: 1px solid #E5E7EB !important;
        border-radius: 12px !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04) !important;
    }
    .chat-input-wrap textarea,
    .chat-input-wrap input {
        background: #FFFFFF !important;
        font-size: 15px !important;
        line-height: 1.5 !important;
        padding: 12px 16px !important;
    }
    .chat-input-wrap textarea {
        min-height: 88px !important;
    }
    .chat-input-wrap input {
        height: 48px !important;
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
       隐藏 Streamlit 自带的 hamburger 菜单和页脚
       ================================================================ */
    #MainMenu { visibility: hidden !important; }
    footer { visibility: hidden !important; display: none !important; }
    header[data-testid="stHeader"] {
        height: 0 !important;
        min-height: 0 !important;
        padding: 0 !important;
        overflow: hidden !important;
    }
    /* 去掉 Streamlit 底部多余空间 */
    .block-container::after { display: none !important; }
    [data-testid="stBottomBlockContainer"] { display: none !important; }

    /* ================================================================
       Stepper: tab bar 导航
       列布局（空 | tab | tab | tab | 空），匹配 5-6 子元素的 HorizontalBlock
       ================================================================ */
    [data-testid="stHorizontalBlock"]:has(> :nth-child(5):last-child),
    [data-testid="stHorizontalBlock"]:has(> :nth-child(6):last-child) {
        padding: 4px 0 2px 0 !important;
        margin-bottom: 2px !important;
        border-bottom: 1px solid #E5E7EB !important;
        background: #FFFFFF !important;
    }
    [data-testid="stHorizontalBlock"]:has(> :nth-child(5):last-child) .stButton > button,
    [data-testid="stHorizontalBlock"]:has(> :nth-child(6):last-child) .stButton > button {
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
        color: #9CA3AF !important;
        font-size: 15px !important;
        font-weight: 600 !important;
        padding: 8px 12px !important;
        border-radius: 8px !important;
        cursor: pointer !important;
        transition: all 0.15s ease !important;
        width: auto !important;
        min-height: 38px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        margin: 0 auto !important;
    }
    [data-testid="stHorizontalBlock"]:has(> :nth-child(5):last-child) .stButton > button:hover,
    [data-testid="stHorizontalBlock"]:has(> :nth-child(6):last-child) .stButton > button:hover {
        background: #F3F4F6 !important;
        color: #374151 !important;
    }

    /* ================================================================
       工作区双列：聊天区 | 固定分隔线 | 功能面板
       两列独立滚动，互不影响
       仅作用于主内容区（排除侧边栏）
       ================================================================ */
    /* 恰好 2 列的容器（主内容区） */
    .block-container [data-testid="stHorizontalBlock"]:has(> :nth-child(2):last-child) {
        flex-wrap: nowrap !important;
        align-items: stretch !important;
        gap: 0 !important;
    }
    /* 左列（聊天区）：独立滚动 + 右边框 */
    .block-container [data-testid="stHorizontalBlock"]:has(> :nth-child(2):last-child) > :first-child {
        border-right: 2px solid #E5E7EB !important;
        padding-right: 1.2rem !important;
        padding-bottom: 1rem !important;
        overflow-y: auto !important;
        overflow-x: hidden !important;
        max-height: calc(100vh - 130px) !important;
        min-width: 0 !important;
    }
    /* 右列（功能面板）：独立滚动 */
    .block-container [data-testid="stHorizontalBlock"]:has(> :nth-child(2):last-child) > :last-child {
        overflow-y: auto !important;
        overflow-x: hidden !important;
        padding-bottom: 1rem !important;
        max-height: calc(100vh - 130px) !important;
        min-width: 200px !important;
        flex-shrink: 0 !important;
        padding-left: 1.5rem !important;
    }

    /* 右列面板内边距 */
    .right-panel-sticky {
        padding-left: 0 !important;
    }

    /* Action Banner removed — navigation via stepper tabs */

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
       首页 — GPT 风格，纯白背景，大圆角输入框
       ================================================================ */
    .home-hero {
        text-align: center;
        margin-bottom: 2rem;
        padding-top: 12vh;
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
        max-width: 680px;
        margin: 1.8rem auto 0.5rem;
        text-align: center;
        color: #9CA3AF;
        font-size: 0.85rem;
    }

    /* ===== GPT 风格输入栏：圆角药丸，+ 按钮在左 ===== */
    /* 定位：紧跟 #home-chatbar-anchor 标记的 2 列容器 */
    [data-testid="stMarkdown"]:has(#home-chatbar-anchor) + [data-testid="stHorizontalBlock"] {
        max-width: 680px !important;
        margin: 0 auto !important;
        background: #FFFFFF !important;
        border: 1.5px solid #E5E7EB !important;
        border-radius: 26px !important;
        box-shadow: 0 2px 12px rgba(0,0,0,0.05) !important;
        padding: 4px 4px 4px 8px !important;
        align-items: center !important;
        flex-wrap: nowrap !important;
        gap: 0 !important;
    }
    /* 左列（+ 按钮）：圆形，紧凑 */
    [data-testid="stMarkdown"]:has(#home-chatbar-anchor) + [data-testid="stHorizontalBlock"] > :first-child {
        flex: 0 0 42px !important;
        max-width: 42px !important;
        min-width: 42px !important;
        padding: 0 !important;
        border-right: none !important;
        overflow: visible !important;
        max-height: none !important;
    }
    [data-testid="stMarkdown"]:has(#home-chatbar-anchor) + [data-testid="stHorizontalBlock"] > :first-child .stButton > button {
        width: 36px !important;
        height: 36px !important;
        min-height: 36px !important;
        min-width: 36px !important;
        padding: 0 !important;
        border-radius: 50% !important;
        background: #F3F4F6 !important;
        border: 1px solid #E5E7EB !important;
        color: #6B7280 !important;
        font-size: 18px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        transition: all 0.15s !important;
        margin: 0 !important;
    }
    [data-testid="stMarkdown"]:has(#home-chatbar-anchor) + [data-testid="stHorizontalBlock"] > :first-child .stButton > button:hover {
        background: #E5E7EB !important;
        color: #374151 !important;
    }
    /* 右列（输入框）：无边框，透明 */
    [data-testid="stMarkdown"]:has(#home-chatbar-anchor) + [data-testid="stHorizontalBlock"] > :last-child {
        flex: 1 !important;
        padding: 0 !important;
        border-right: none !important;
        overflow: visible !important;
        max-height: none !important;
        min-width: 0 !important;
    }
    [data-testid="stMarkdown"]:has(#home-chatbar-anchor) + [data-testid="stHorizontalBlock"] > :last-child [data-testid="stTextInput"] > label {
        display: none !important;
    }
    [data-testid="stMarkdown"]:has(#home-chatbar-anchor) + [data-testid="stHorizontalBlock"] > :last-child [data-testid="stTextInput"] > div {
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
        padding: 0 !important;
    }
    [data-testid="stMarkdown"]:has(#home-chatbar-anchor) + [data-testid="stHorizontalBlock"] > :last-child input {
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
        font-size: 16px !important;
        height: 48px !important;
        padding: 0 16px 0 8px !important;
        color: var(--text-primary) !important;
    }
    [data-testid="stMarkdown"]:has(#home-chatbar-anchor) + [data-testid="stHorizontalBlock"] > :last-child input:focus {
        border: none !important;
        box-shadow: none !important;
        outline: none !important;
    }

    /* 文件上传区域 — 居中 */
    .block-container [data-testid="stFileUploader"] {
        max-width: 680px !important;
        margin: 8px auto 0 !important;
    }

    /* 快捷示例按钮 */
    .home-quick-label + [data-testid="stHorizontalBlock"] .stButton > button,
    .home-quick-label ~ [data-testid="stHorizontalBlock"] .stButton > button {
        font-size: 13px !important;
        padding: 6px 12px !important;
        min-height: 34px !important;
        border-radius: 8px !important;
        background: #F9FAFB !important;
        border: 1px solid #E5E7EB !important;
        color: #374151 !important;
        width: 100% !important;
    }
    .home-quick-label + [data-testid="stHorizontalBlock"] .stButton > button:hover,
    .home-quick-label ~ [data-testid="stHorizontalBlock"] .stButton > button:hover {
        background: #F3F4F6 !important;
        border-color: #D1D5DB !important;
    }
    /* 快捷示例行居中 */
    .home-quick-label + [data-testid="stHorizontalBlock"],
    .home-quick-label ~ [data-testid="stHorizontalBlock"] {
        max-width: 680px !important;
        margin-left: auto !important;
        margin-right: auto !important;
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

    /* ================================================================
       Workspace Footer — 固定在页面底部
       ================================================================ */
    .workspace-footer {
        position: fixed;
        bottom: 0;
        left: var(--sidebar-width);
        right: 0;
        display: flex;
        justify-content: center;
        align-items: center;
        gap: 8px;
        padding: 6px 0;
        border-top: 1px solid #E5E7EB;
        font-size: 12px;
        color: #9CA3AF;
        background: #FAFAFA;
        z-index: 998;
    }
    </style>
    """

def inject_styles():
    """Inject CSS into Streamlit app."""
    st.markdown(get_css(), unsafe_allow_html=True)
