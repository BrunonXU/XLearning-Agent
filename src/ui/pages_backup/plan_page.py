"""
学习计划页面 - 重构版本 (匹配 Mockup 设计，避免嵌套 expander)
"""

import streamlit as st
from src.ui.components import (
    render_progress_bar,
    render_code_block,
    render_orange_button
)


def render_plan_page(orchestrator):
    """渲染学习计划页面 - 匹配 Mockup 中的 "Learning Roadmap" 布局"""
    
    # 从 session state 获取当前学习领域
    domain = st.session_state.get("domain", "Python Data Science")
    
    # 页面标题
    st.markdown(f"""
    <div style="margin-bottom: 24px;">
        <h1 style="color: #1F2937; font-weight: 700; margin-bottom: 8px;">
            🌟 Learning Roadmap for {domain}
        </h1>
    </div>
    """, unsafe_allow_html=True)
    
    # 用户问题卡片 (模拟 Mockup 中的橙色左边框引用)
    st.markdown("""
    <div style="
        border-left: 4px solid #F97316;
        padding: 12px 16px;
        background-color: #FFFBEB;
        margin-bottom: 20px;
        border-radius: 0 8px 8px 0;
    ">
        <p style="margin: 0; color: #92400E;">
            Can you create a study plan for a beginner to learn Python for data science in 4 weeks? Focus on practical skills.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Agent 回复区域 (使用卡片样式而非 expander)
    st.markdown("""
    <div style="
        background-color: #F9FAFB;
        border: 1px solid #E5E7EB;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 20px;
    ">
        <div style="display: flex; align-items: center; margin-bottom: 12px;">
            <span style="font-size: 20px; margin-right: 8px;">🤖</span>
            <h3 style="margin: 0; color: #1F2937; font-weight: 600;">XLearning Agent's Plan</h3>
        </div>
        <p style="color: #4B5563;">Here is a structured 4-week plan, focusing on hands-on practice.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Week 1 - 展开的 (不嵌套)
    with st.expander("📅 Week 1: Python Basics & NumPy", expanded=True):
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.markdown("""
            1. Variables, Data Types, Loops (6 hours)
            2. Functions & Modules (4 hours)
            3. Introduction to NumPy for Numerical Computing (4 hours)
            """)
        
        with col2:
            render_progress_bar("", 0.25)
            render_progress_bar("", 0.10)
            render_progress_bar("", 0.0)
        
        # 代码示例
        render_code_block("""import numpy as np
a = np.array([1, 2, 3])
print(a)""")
        
        # 橙色按钮
        if render_orange_button("Start Week 1 Quiz", "quiz_week1"):
            st.session_state.current_page = "quiz"
            st.experimental_rerun()
    
    # Week 2 - 折叠的
    with st.expander("📅 Week 2: Pandas for Data Manipulation", expanded=False):
        st.markdown("""
        1. DataFrames & Series (4 hours)
        2. Data Cleaning & Preprocessing (4 hours)
        3. Merging & Grouping Data (4 hours)
        """)
    
    # Week 3 - 折叠的
    with st.expander("📅 Week 3: Matplotlib & Seaborn for Visualization", expanded=False):
        st.markdown("""
        1. Basic Plotting with Matplotlib (4 hours)
        2. Statistical Visualization with Seaborn (4 hours)
        3. Creating Interactive Dashboards (4 hours)
        """)
    
    # Week 4 - 折叠的
    with st.expander("📅 Week 4: Mini Project & Review", expanded=False):
        st.markdown("""
        1. End-to-End Data Analysis Project (8 hours)
        2. Review & Q&A Session (4 hours)
        """)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # 用户追问 (模拟 Mockup 中的第二个对话)
    st.markdown("""
    <div style="
        border-left: 4px solid #F97316;
        padding: 12px 16px;
        background-color: #FFFBEB;
        margin: 20px 0;
        border-radius: 0 8px 8px 0;
    ">
        <p style="margin: 0; color: #92400E;">
            What is the difference between a list and a tuple in Python?
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Agent 回复 (使用卡片样式而非嵌套 expander)
    st.markdown("""
    <div style="
        background-color: #F9FAFB;
        border: 1px solid #E5E7EB;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 20px;
    ">
        <div style="display: flex; align-items: center; margin-bottom: 12px;">
            <span style="font-size: 20px; margin-right: 8px;">🤖</span>
            <h3 style="margin: 0; color: #1F2937; font-weight: 600;">Learning Agent's Explanation</h3>
        </div>
        <p style="color: #4B5563;">Great question! They are both used to store collections of items, but with key differences:</p>
    </div>
    """, unsafe_allow_html=True)
    
    # 表格
    st.markdown("""
    | Feature | List | Tuple |
    |---------|------|-------|
    | **Mutability** | Lists are mutable (can change) | Tuples are immutable (cannot change) |
    | **Syntax** | Uses `[ ]` | Uses `( )` |
    | **Performance** | Slightly slower | Slightly faster |
    """)
    
    # 代码示例
    render_code_block("""my_list = [1, 2, 3]
my_tuple = (1, 2, 3)
my_list[0] = 10  # Works
my_tuple[0] = 10  # Error""")
