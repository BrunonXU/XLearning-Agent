"""
XLearning-Agent - AI 智能学习助手

Streamlit 应用入口

运行方式：
    streamlit run app.py

TODO (Day 10-11):
- 完善 UI 交互
- 添加文件上传
- 实现流式输出
"""

import streamlit as st
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 页面配置
st.set_page_config(
    page_title="XLearning Agent",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 初始化 session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "domain" not in st.session_state:
    st.session_state.domain = ""
if "orchestrator" not in st.session_state:
    st.session_state.orchestrator = None


def init_orchestrator(domain: str):
    """初始化 Orchestrator"""
    from src.agents import Orchestrator
    
    orch = Orchestrator(domain=domain)
    orch.set_domain(domain)
    st.session_state.orchestrator = orch
    return orch


def main():
    """主函数"""
    # 侧边栏
    with st.sidebar:
        st.markdown("## 🎓 XLearning Agent")
        st.markdown("*AI 智能学习助手*")
        st.markdown("---")
        
        # 领域输入
        domain = st.text_input(
            "📚 学习领域",
            value=st.session_state.domain,
            placeholder="例如：LangChain、Transformer",
        )
        
        if domain and domain != st.session_state.domain:
            st.session_state.domain = domain
            st.session_state.orchestrator = None
            st.session_state.messages = []
        
        st.markdown("---")
        
        # 模式选择
        mode = st.radio(
            "🔄 运行模式",
            ["单独模式", "协调模式"],
            help="单独模式：精细控制；协调模式：一键完成",
        )
        
        st.markdown("---")
        
        # 快捷操作
        st.markdown("### ⚡ 快捷操作")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📋 生成计划", use_container_width=True):
                st.session_state.action = "plan"
        with col2:
            if st.button("📝 开始测验", use_container_width=True):
                st.session_state.action = "quiz"
        
        if st.button("📊 查看进度", use_container_width=True):
            st.session_state.action = "report"
        
        st.markdown("---")
        
        # 文件上传
        st.markdown("### 📁 上传资料")
        uploaded_files = st.file_uploader(
            "支持 PDF、Markdown",
            type=["pdf", "md", "txt"],
            accept_multiple_files=True,
            label_visibility="collapsed",
        )
        
        if uploaded_files:
            st.success(f"已上传 {len(uploaded_files)} 个文件")
        
        st.markdown("---")
        
        # 设置
        with st.expander("⚙️ 设置"):
            use_rag = st.checkbox("启用 RAG", value=True)
            use_stream = st.checkbox("流式输出", value=False, disabled=True)
    
    # 主界面
    st.title("🎓 XLearning Agent")
    st.markdown("*你的 AI 学习助手*")
    
    if not domain:
        # 欢迎界面
        st.markdown("---")
        st.markdown("""
        ### 👋 欢迎使用 XLearning Agent！
        
        这是一个基于 **LangChain + RAG + Multi-Agent** 的智能学习助手。
        
        #### 🚀 快速开始
        
        1. 在左侧输入你想学习的领域（如 "LangChain"）
        2. 可以上传 PDF 论文或 Markdown 资料
        3. 开始与 AI 助手互动学习！
        
        #### ✨ 核心功能
        
        - 📋 **智能规划** - 自动生成个性化学习计划
        - 🎓 **互动教学** - 随时提问，获取解答
        - 📝 **Quiz 测验** - 验证学习效果
        - 📊 **进度追踪** - 查看学习进度报告
        
        #### 💡 提示
        
        输入 GitHub URL 或上传 PDF，AI 会自动分析并生成学习计划！
        """)
        return
    
    # 显示聊天历史
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # 处理快捷操作
    if "action" in st.session_state:
        action = st.session_state.pop("action")
        if action == "plan":
            user_input = f"请帮我制定 {domain} 的学习计划"
        elif action == "quiz":
            user_input = f"开始 {domain} 的测验"
        elif action == "report":
            user_input = "查看学习进度报告"
        
        # 添加用户消息
        st.session_state.messages.append({"role": "user", "content": user_input})
        
        # 处理请求
        with st.spinner("思考中..."):
            if not st.session_state.orchestrator:
                init_orchestrator(domain)
            
            try:
                response = st.session_state.orchestrator.run(user_input)
            except Exception as e:
                response = f"❌ 发生错误: {str(e)}\n\n请确保已正确配置 API Key。"
        
        # 添加助手回复
        st.session_state.messages.append({"role": "assistant", "content": response})
        st.rerun()
    
    # 用户输入
    if user_input := st.chat_input("输入你的问题..."):
        # 添加用户消息
        st.session_state.messages.append({"role": "user", "content": user_input})
        
        with st.chat_message("user"):
            st.markdown(user_input)
        
        # 处理请求
        with st.chat_message("assistant"):
            with st.spinner("思考中..."):
                if not st.session_state.orchestrator:
                    init_orchestrator(domain)
                
                try:
                    response = st.session_state.orchestrator.run(user_input)
                except Exception as e:
                    response = f"❌ 发生错误: {str(e)}\n\n请确保已正确配置 API Key。"
                
                st.markdown(response)
        
        # 保存助手回复
        st.session_state.messages.append({"role": "assistant", "content": response})


if __name__ == "__main__":
    main()
