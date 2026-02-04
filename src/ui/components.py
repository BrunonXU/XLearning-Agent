"""
Streamlit UI 组件

可复用的 UI 组件，用于构建界面

TODO (Day 10-11):
- 完善各组件实现
- 添加更多交互功能
"""

from typing import List, Dict, Any, Optional
import streamlit as st

from src.core.models import LearningPlan, Quiz, ProgressReport


def render_chat_message(role: str, content: str):
    """
    渲染聊天消息
    
    Args:
        role: 角色（user/assistant）
        content: 消息内容
    """
    with st.chat_message(role):
        st.markdown(content)


def render_plan(plan: LearningPlan):
    """
    渲染学习计划
    
    Args:
        plan: LearningPlan 对象
    """
    st.markdown(f"## 📋 {plan.domain} 学习计划")
    
    # 基本信息
    col1, col2 = st.columns(2)
    with col1:
        st.metric("目标", plan.goal)
    with col2:
        st.metric("预计时长", plan.duration)
    
    # 前置知识
    if plan.prerequisites:
        with st.expander("📚 前置知识", expanded=False):
            for prereq in plan.prerequisites:
                st.markdown(f"- {prereq}")
    
    # 学习阶段
    st.markdown("### 学习阶段")
    for i, phase in enumerate(plan.phases, 1):
        status = "✅" if phase.completed else "⬜"
        with st.expander(f"{status} 阶段 {i}: {phase.name} ({phase.duration})", expanded=(i == 1)):
            for topic in phase.topics:
                st.markdown(f"- {topic}")
            if phase.resources:
                st.markdown("**推荐资源:**")
                for resource in phase.resources:
                    st.markdown(f"- {resource}")


def render_quiz(quiz: Quiz, current_index: int = 0):
    """
    渲染测验题目
    
    Args:
        quiz: Quiz 对象
        current_index: 当前题目索引
    """
    if not quiz.questions:
        st.warning("没有题目")
        return
    
    # 进度条
    progress = (current_index + 1) / len(quiz.questions)
    st.progress(progress, text=f"题目 {current_index + 1}/{len(quiz.questions)}")
    
    # 当前题目
    question = quiz.questions[current_index]
    
    st.markdown(f"### {question.question}")
    
    # 选项
    if question.options:
        selected = st.radio(
            "选择答案",
            question.options,
            key=f"quiz_q_{current_index}",
            label_visibility="collapsed",
        )
        return selected
    else:
        answer = st.text_input(
            "输入答案",
            key=f"quiz_q_{current_index}",
            label_visibility="collapsed",
        )
        return answer


def render_progress(report: ProgressReport):
    """
    渲染进度报告
    
    Args:
        report: ProgressReport 对象
    """
    st.markdown(f"## 📊 {report.domain} 学习进度")
    
    # 统计指标
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("会话数", report.total_sessions)
    with col2:
        st.metric("Quiz 次数", report.quiz_attempts)
    with col3:
        st.metric("平均正确率", f"{report.average_accuracy:.1%}")
    
    # 已掌握知识点
    if report.mastered_topics:
        st.markdown("### ✅ 已掌握")
        cols = st.columns(3)
        for i, topic in enumerate(report.mastered_topics):
            with cols[i % 3]:
                st.success(topic)
    
    # 薄弱知识点
    if report.weak_topics:
        st.markdown("### ⚠️ 需加强")
        cols = st.columns(3)
        for i, topic in enumerate(report.weak_topics):
            with cols[i % 3]:
                st.warning(topic)
    
    # 建议
    if report.suggestions:
        st.markdown("### 💡 建议")
        for suggestion in report.suggestions:
            st.info(suggestion)


def render_mode_selector():
    """
    渲染模式选择器
    
    Returns:
        选择的模式
    """
    return st.radio(
        "选择运行模式",
        ["单独模式", "协调模式"],
        horizontal=True,
        help="单独模式：精细控制每个步骤；协调模式：一键完成全流程",
    )


def render_file_uploader():
    """
    渲染文件上传组件
    
    Returns:
        上传的文件列表
    """
    return st.file_uploader(
        "上传学习资料",
        type=["pdf", "md", "txt"],
        accept_multiple_files=True,
        help="支持 PDF、Markdown、文本文件",
    )


def render_sidebar():
    """
    渲染侧边栏
    """
    with st.sidebar:
        st.markdown("## 🎓 XLearning Agent")
        st.markdown("---")
        
        # 当前领域
        st.markdown("### 📚 当前学习领域")
        domain = st.text_input(
            "输入学习领域",
            value="",
            placeholder="例如：LangChain",
            label_visibility="collapsed",
        )
        
        st.markdown("---")
        
        # 操作按钮
        if st.button("🆕 新建学习计划", use_container_width=True):
            st.session_state["action"] = "new_plan"
        
        if st.button("📝 开始测验", use_container_width=True):
            st.session_state["action"] = "start_quiz"
        
        if st.button("📊 查看进度", use_container_width=True):
            st.session_state["action"] = "view_progress"
        
        st.markdown("---")
        
        # 设置
        with st.expander("⚙️ 设置"):
            st.checkbox("启用 RAG 检索", value=True, key="use_rag")
            st.checkbox("流式输出", value=False, key="use_stream")
        
        return domain
