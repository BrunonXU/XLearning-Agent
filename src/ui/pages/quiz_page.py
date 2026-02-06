"""
知识测验页面 - 重构版本 (匹配 Mockup 设计)
"""

import streamlit as st
from src.ui.components import render_orange_button


def render_quiz_page(orchestrator):
    """渲染测验页面"""
    
    st.markdown("""
    <h1 style="color: #1F2937; font-weight: 700;">🧠 知识自测</h1>
    <p style="color: #6B7280;">验证你的学习成果。</p>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Quiz State
    if "quiz_active" not in st.session_state:
        st.session_state.quiz_active = False
    if "quiz_answer" not in st.session_state:
        st.session_state.quiz_answer = None
    
    if not st.session_state.quiz_active:
        # Start Quiz Card
        st.markdown("""
        <div style="
            background-color: #F9FAFB;
            border: 1px solid #E5E7EB;
            border-radius: 12px;
            padding: 24px;
            text-align: center;
        ">
            <h3 style="color: #1F2937;">准备好挑战自己了吗？</h3>
            <p style="color: #6B7280;">当前关注点: <strong>Python 基础</strong></p>
            <p style="color: #9CA3AF; font-size: 14px;">预计耗时: 5 分钟 • 5 道题目</p>
        </div>
        """, unsafe_allow_html=True)
        
        if render_orange_button("🚀 开始测验", "start_quiz"):
            st.session_state.quiz_active = True
            st.experimental_rerun()
    else:
        # Active Quiz
        st.markdown("""
        <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px;">
            <span style="color: #6B7280;">第 2 / 5 题</span>
        </div>
        """, unsafe_allow_html=True)
        
        # Progress bar
        st.progress(0.4)
        
        # Question Card
        st.markdown("""
        <div style="
            background-color: #F9FAFB;
            border: 1px solid #E5E7EB;
            border-radius: 12px;
            padding: 24px;
            margin: 16px 0;
        ">
            <h3 style="color: #1F2937; margin-bottom: 16px;">❓ Python 中 List 和 Tuple 的主要区别是什么？</h3>
        </div>
        """, unsafe_allow_html=True)
        
        # Options
        options = [
            "List 是可变的，Tuple 是不可变的",
            "List 是不可变的，Tuple 是可变的",
            "它们没有区别",
            "Tuple 只能包含数字"
        ]
        
        selected = st.radio("选择答案:", options, key="quiz_q2")
        
        # Navigation Buttons
        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            if st.button("⬅️ 上一题"):
                st.info("这是第一题")
        with col3:
            if render_orange_button("下一题 ➡️", "next_question"):
                if selected == options[0]:
                    st.success("✅ 正确！List 是可变的，Tuple 是不可变的。")
                else:
                    st.error("❌ 错误。正确答案是：List 是可变的，Tuple 是不可变的。")
