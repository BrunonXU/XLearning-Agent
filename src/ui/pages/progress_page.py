"""
进度追踪页面 - 重构版本 (匹配 Mockup 设计)
"""

import streamlit as st
from src.ui.components import render_progress_bar


def render_progress_page(orchestrator):
    """渲染进度页面"""
    
    st.markdown("""
    <h1 style="color: #1F2937; font-weight: 700;">📊 学习进度</h1>
    <p style="color: #6B7280;">持续追踪你的成长。</p>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Top Level Stats - 4 Columns
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div style="background: #F9FAFB; padding: 16px; border-radius: 12px; text-align: center;">
            <div style="font-size: 28px; font-weight: 700; color: #F97316;">12.5h</div>
            <div style="color: #6B7280; font-size: 14px;">总学习时长</div>
            <div style="color: #10B981; font-size: 12px;">+2.5h</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div style="background: #F9FAFB; padding: 16px; border-radius: 12px; text-align: center;">
            <div style="font-size: 28px; font-weight: 700; color: #F97316;">8/20</div>
            <div style="color: #6B7280; font-size: 14px;">掌握知识点</div>
            <div style="color: #10B981; font-size: 12px;">40%</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div style="background: #F9FAFB; padding: 16px; border-radius: 12px; text-align: center;">
            <div style="font-size: 28px; font-weight: 700; color: #F97316;">85%</div>
            <div style="color: #6B7280; font-size: 14px;">测验平均分</div>
            <div style="color: #10B981; font-size: 12px;">+5%</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
        <div style="background: #F9FAFB; padding: 16px; border-radius: 12px; text-align: center;">
            <div style="font-size: 28px; font-weight: 700; color: #F97316;">🔥 3</div>
            <div style="color: #6B7280; font-size: 14px;">连续打卡</div>
            <div style="color: #10B981; font-size: 12px;">天</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Charts Section
    col_left, col_right = st.columns([2, 1])
    
    with col_left:
        st.markdown("""
        <div style="background: #F9FAFB; padding: 20px; border-radius: 12px;">
            <h3 style="color: #1F2937; margin-bottom: 16px;">📈 活动概览</h3>
        </div>
        """, unsafe_allow_html=True)
        
        # Simple chart using Streamlit's native chart
        import pandas as pd
        import numpy as np
        
        chart_data = pd.DataFrame(
            np.random.randn(7, 2) + [10, 5],
            columns=['学习时长', '测验得分'],
            index=["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
        )
        st.line_chart(chart_data)
    
    with col_right:
        st.markdown("""
        <div style="background: #F9FAFB; padding: 20px; border-radius: 12px;">
            <h3 style="color: #1F2937; margin-bottom: 16px;">💪 优势领域</h3>
        </div>
        """, unsafe_allow_html=True)
        
        render_progress_bar("Python 语法", 0.9)
        render_progress_bar("数据结构", 0.75)
        render_progress_bar("Pandas", 0.6)
        render_progress_bar("机器学习", 0.4)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Recent Activity
    st.markdown("""
    <div style="background: #F9FAFB; padding: 20px; border-radius: 12px;">
        <h3 style="color: #1F2937; margin-bottom: 16px;">🕒 最近动态</h3>
        <div style="color: #4B5563;">
            <p>✅ <strong>完成测验:</strong> Python 列表 (得分: 90%) - <em>2 小时前</em></p>
            <p>📖 <strong>阅读材料:</strong> "理解列表推导式" - <em>3 小时前</em></p>
            <p>🎯 <strong>设定目标:</strong> 本周五前学会 Pandas - <em>昨天</em></p>
        </div>
    </div>
    """, unsafe_allow_html=True)
