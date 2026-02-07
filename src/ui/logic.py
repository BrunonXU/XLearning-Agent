"""
XLearning Agent - UI Logic Bridge
=================================
Connects UI events to the Backend Orchestrator.
Handles: Agent Stream, Tools Events, Exception Management.
"""

import time
import threading
from typing import Generator, Optional, Any

import streamlit as st
from src.agents.orchestrator import Orchestrator, OrchestratorMode
from src.ui.state import add_message, add_trace_event, set_kb_status

# Global Orchestrator instance (lazy loaded)
_ORCHESTRATOR = None

def get_orchestrator(on_event: Optional[Any] = None, mode: Optional[str] = None) -> Orchestrator:
    """Get or create singleton Orchestrator instance."""
    global _ORCHESTRATOR
    if _ORCHESTRATOR is None:
        # User Feedback: Mode should be determined by Intent, not manual toggle.
        # Defaulting to COORDINATED which includes Intent Classification.
        _ORCHESTRATOR = Orchestrator(mode=OrchestratorMode.COORDINATED, on_event=on_event)
    else:
        # Update callback if provided
        if on_event:
            _ORCHESTRATOR.on_event = on_event
            _ORCHESTRATOR.planner.on_event = on_event
            _ORCHESTRATOR.tutor.on_event = on_event
            _ORCHESTRATOR.validator.on_event = on_event
            
    return _ORCHESTRATOR

def handle_chat_input(user_input: str, should_rerun: bool = True) -> None:
    """
    Process user input via Orchestrator.
    This function should be called from the UI thread.
    Args:
        user_input: The text to process.
        should_rerun: Whether to trigger a rerun at the end (set False if inside a callback).
    """
    if not user_input.strip():
        return

    st.session_state.is_processing = True
    st.session_state.stop_requested = False
    
    # 0. Clear previous trace for a clean view
    from src.ui.state import clear_session_trace
    clear_session_trace()
    
    # 1. Add User Message immediately
    add_message(role="user", content=user_input)
    
    # 2. Add assistant message placeholder
    msg_id = add_message(
        role="assistant", 
        content="正在思考中...", 
        agent="orchestrator", 
        status="streaming"
    )

    # 3. Trigger immediate rerun to show the messages in UI
    # We set a flag so that on the NEXT run, we start the processing.
    st.session_state.pending_chat_query = user_input
    st.session_state.pending_msg_id = msg_id
    
    if should_rerun:
        st.experimental_rerun()

def process_pending_chat(should_rerun: bool = True):
    """Process a query that was added to history but is waiting for LLM."""
    if "pending_chat_query" not in st.session_state or not st.session_state.pending_chat_query:
        return

    user_input = st.session_state.pending_chat_query
    msg_id = st.session_state.pending_msg_id
    
    # Reset pending flags
    st.session_state.pending_chat_query = None
    st.session_state.pending_msg_id = None

    # Define Trace Callback
    import uuid
    current_step_id_container = {"id": "initial"}

    def trace_callback(event_type: str, name: str, detail: str = ""):
        if event_type == "tool_start":
            current_step_id_container["id"] = "step_" + uuid.uuid4().hex[:4]
        from src.ui.state import add_trace_event
        add_trace_event(current_step_id_container["id"], event_type, name, detail)

    # Synchronous Processing (more stable in Streamlit 1.12.0)
    import traceback
    
    print(f"[DEBUG] Starting synchronous processing loop for: {user_input[:20]}...")
    
    # REPLACED WITH NON-BLOCKING UI:
    # The "Thinking..." message is already in the message list with status="streaming".
    try:
        # 4. Get or create orchestrator
        print("[DEBUG] Getting Orchestrator instance...")
        orchestrator = get_orchestrator(on_event=trace_callback)
        
        # Default to coordinated for now as it handles classification
        mode_str = "coordinated"
        current_mode = OrchestratorMode.STANDALONE if mode_str == "standalone" else OrchestratorMode.COORDINATED
        if orchestrator.mode != current_mode:
            orchestrator.switch_mode(current_mode)
        
        trace_callback("progress", "Orchestrator", "正在处理您的输入...")
        
        # Extract history (last 10 messages, including user message that was just added)
        history = []
        if st.session_state.current_session:
            all_msgs = st.session_state.current_session.get("messages", [])
            # Exclude the very last placeholder message that is currently "正在思考中..."
            raw_history = all_msgs[:-2] if len(all_msgs) >= 2 else []
            for m in raw_history[-10:]:
                history.append({"role": m["role"], "content": m["content"]})

        # 5. Execute Run
        print(f"[DEBUG] Calling orchestrator.run with input length {len(user_input)} and history length {len(history)}...")
        response = orchestrator.run(user_input, history=history)
        
        print(f"[DEBUG] Response received (length: {len(response) if response else 0})")
        
        if not response:
            response = "未生成任何回复，请检查后台日志或 API Key 设置。"
            
        # 6. Update complete message
        if st.session_state.current_session:
            for msg in st.session_state.current_session["messages"]:
                if msg["id"] == msg_id:
                    msg["content"] = response
                    msg["status"] = "complete"
                    msg["agent"] = "tutor"
                    break
        
        trace_callback("progress", "Orchestrator", "处理完成。")
        
        # 7. Update Session Logic State
        session = st.session_state.current_session
        if session:
            session["has_input"] = True
            # Detection of plan generation
            if "计划" in response or "📋" in response:
                session["plan"] = {"status": "generated"}
            if "开始学习" in response or "学习" in user_input:
                if session.get("plan"):
                    session["study_progress"] = max(session.get("study_progress", 0), 1)

    except Exception as e:
        err_trace = traceback.format_exc()
        if st.session_state.current_session:
            for msg in st.session_state.current_session["messages"]:
                if msg["id"] == msg_id:
                    msg["content"] = f"⚠️ 处理失败: {str(e)}"
                    msg["status"] = "error"
                    msg["error"] = err_trace
                    break
        st.error(f"Execution Error: {e}")
        print(f"[UI Logic Error] {err_trace}")
    
    finally:
        st.session_state.is_processing = False
        from src.ui.state import save_session_data
        save_session_data(st.session_state.current_session_id, st.session_state.current_session)
        
        if should_rerun:
            st.experimental_rerun()

def handle_file_upload(file) -> None:
    """Handle PDF upload via Orchestrator."""
    orchestrator = get_orchestrator()
    try:
        with st.spinner(f"正在深入分析 {file.name} 并构建专属知识库，这可能需要几十秒..."):
            content = file.read()
            set_kb_status("parsing", source=file.name)
            
            # Call Orchestrator
            result = orchestrator.process_file(content, file.name)
            
            if result.get("success", False):
                count = result.get("chunks", 0)
                set_kb_status("ready", count=count)
                
                # Sync logic state
                if st.session_state.current_session:
                    st.session_state.current_session["kb_count"] = count
                    st.session_state.current_session["has_input"] = True
                
                add_message("system", result.get("message"), agent="validator")
            else:
                set_kb_status("error", error=result.get("message"))
                add_message("system", result.get("message"), agent="system", status="error")
        
    except Exception as e:
        set_kb_status("error", error=str(e))
        st.error(f"Upload failed: {e}")

def handle_generate_quiz() -> None:
    """Generate a mock quiz for demonstration."""
    from src.ui.state import save_session_data
    
    # Mock Quiz Data
    mock_questions = [
        {
            "qid": "q1",
            "question": "Python 中用于定义函数的关键字是？",
            "options": ["func", "def", "function", "define"],
            "correct_answer": "B",
            "explanation": "在 Python 中，使用 `def` 关键字来定义函数。"
        },
        {
            "qid": "q2",
            "question": "以下哪个数据结构是不可变的？",
            "options": ["List", "Dictionary", "Tuple", "Set"],
            "correct_answer": "C",
            "explanation": "Tuple（元组）一旦创建就不能修改，是不可变序列。"
        },
        {
            "qid": "q3",
            "question": "如何获取列表 `my_list` 的长度？",
            "options": ["my_list.length()", "length(my_list)", "len(my_list)", "my_list.size()"],
            "correct_answer": "C",
            "explanation": "内置函数 `len()` 用于获取序列（如列表、字符串）的长度。"
        },
        {
            "qid": "q4",
            "question": "RAG 系统中的 'R' 代表什么？",
            "options": ["Read", "Retrieve", "Reason", "Rank"],
            "correct_answer": "B",
            "explanation": "RAG 代表 Retrieval-Augmented Generation（检索增强生成）。"
        },
        {
            "qid": "q5",
            "question": "Streamlit 的主要用途是什么？",
            "options": ["游戏开发", "Web 应用快速开发", "嵌入式系统", "移动应用"],
            "correct_answer": "B",
            "explanation": "Streamlit 是一个开源 Python 库，用于快速构建和共享数据 Web 应用。"
        }
    ]
    
    if st.session_state.current_session:
        st.session_state.current_session["quiz_attempts"] = st.session_state.current_session.get("quiz_attempts", 0) + 1
        st.session_state.current_session["quiz"]["questions"] = mock_questions
        st.session_state.current_session["quiz"]["score"] = None
        st.session_state.current_session["quiz"]["wrong_questions"] = []
        
        save_session_data(st.session_state.current_session_id, st.session_state.current_session)
        st.experimental_rerun()
