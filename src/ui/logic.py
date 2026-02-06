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

def get_orchestrator(on_event: Optional[Any] = None) -> Orchestrator:
    """Get or create singleton Orchestrator instance."""
    global _ORCHESTRATOR
    if _ORCHESTRATOR is None:
        # Check session state for mode
        mode_str = st.session_state.get("mode", "standalone")
        mode = OrchestratorMode.STANDALONE if mode_str == "standalone" else OrchestratorMode.COORDINATED
        _ORCHESTRATOR = Orchestrator(mode=mode, on_event=on_event)
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
    
    # 1. Define Trace Callback
    import uuid
    current_step_id = "step_" + uuid.uuid4().hex[:4]
    
    def trace_callback(event_type: str, name: str, detail: str = ""):
        nonlocal current_step_id
        if event_type == "tool_start":
            current_step_id = "step_" + uuid.uuid4().hex[:4]
        from src.ui.state import add_trace_event
        add_trace_event(current_step_id, event_type, name, detail)

    # 2. Add assistant message placeholder
    msg_id = add_message(
        role="assistant", 
        content="正在思考中...", 
        agent="orchestrator", 
        status="streaming"
    )
    
    # 3. Asynchronous Execution Container (Thread Safe)
    class OrchestratorThread(threading.Thread):
        def __init__(self, user_input, mode_str, callback):
            super().__init__()
            self.user_input = user_input
            self.mode_str = mode_str
            self.callback = callback
            self.result = None
            self.error = None
            self.done = False

        def run(self):
            try:
                orchestrator = get_orchestrator(on_event=self.callback)
                # Ensure mode is synced (Using captured value)
                current_mode = OrchestratorMode.STANDALONE if self.mode_str == "standalone" else OrchestratorMode.COORDINATED
                if orchestrator.mode != current_mode:
                    orchestrator.switch_mode(current_mode)
                
                self.callback("progress", "Orchestrator", "Handling user input...")
                self.result = orchestrator.run(self.user_input)
            except Exception as e:
                self.error = e
            finally:
                self.done = True

    # 4. Start Thread with captured mode
    captured_mode = st.session_state.get("mode", "standalone")
    thread = OrchestratorThread(user_input, captured_mode, trace_callback)
    thread.start()
    
    # 5. Polling Loop to avoid UI Blur
    # Streamlit blurs the UI while a script is running. 
    # To keep it responsive, we use short sleeps and periodic reruns IF needed,
    # OR we just let the thread run and wait in a controlled way.
    # Note: Streamlit 1.12.0 doesn't have st.empty block for async as easily,
    # but we can use a small wait loop.
    
    while not thread.done:
        if st.session_state.stop_requested:
            # Handle stop logic if possible (thread termination is hard in Python)
            break
        time.sleep(0.5)
        # We don't rerun here to avoid flicker; the thread updates shared memory via callback
        # (Though st.session_state updates in a thread might not be visible until next rerun)
    
    try:
        if thread.error:
            raise thread.error
        
        response = thread.result or "No response generated."
        
        # 6. Update complete message
        if st.session_state.current_session:
            for msg in st.session_state.current_session["messages"]:
                if msg["id"] == msg_id:
                    msg["content"] = response
                    msg["status"] = "complete"
                    msg["agent"] = "tutor"
                    break
        
        trace_callback("progress", "Orchestrator", "Finished.")
        
    except Exception as e:
        if st.session_state.current_session:
            for msg in st.session_state.current_session["messages"]:
                if msg["id"] == msg_id:
                    msg["content"] = f"Error: {str(e)}"
                    msg["status"] = "error"
                    msg["error"] = str(e)
                    break
        st.error(f"Error: {e}")
    
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
        content = file.read()
        set_kb_status("parsing", source=file.name)
        
        # Simulate processing time or make clear it's sync
        result = orchestrator.process_file(content, file.name)
        
        set_kb_status("ready", count=100) # Mock count for now
        add_message("system", result, agent="validator")
        
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
            "choices": ["func", "def", "function", "define"],
            "answer_index": 1,
            "explanation": "在 Python 中，使用 `def` 关键字来定义函数。"
        },
        {
            "qid": "q2",
            "question": "以下哪个数据结构是不可变的？",
            "choices": ["List", "Dictionary", "Tuple", "Set"],
            "answer_index": 2,
            "explanation": "Tuple（元组）一旦创建就不能修改，是不可变序列。"
        },
        {
            "qid": "q3",
            "question": "如何获取列表 `my_list` 的长度？",
            "choices": ["my_list.length()", "length(my_list)", "len(my_list)", "my_list.size()"],
            "answer_index": 2,
            "explanation": "内置函数 `len()` 用于获取序列（如列表、字符串）的长度。"
        },
        {
            "qid": "q4",
            "question": "RAG 系统中的 'R' 代表什么？",
            "choices": ["Read", "Retrieve", "Reason", "Rank"],
            "answer_index": 1,
            "explanation": "RAG 代表 Retrieval-Augmented Generation（检索增强生成）。"
        },
        {
            "qid": "q5",
            "question": "Streamlit 的主要用途是什么？",
            "choices": ["游戏开发", "Web 应用快速开发", "嵌入式系统", "移动应用"],
            "answer_index": 1,
            "explanation": "Streamlit 是一个开源 Python 库，用于快速构建和共享数据 Web 应用。"
        }
    ]
    
    if st.session_state.current_session:
        st.session_state.current_session["quiz"]["questions"] = mock_questions
        st.session_state.current_session["quiz"]["score"] = None
        st.session_state.current_session["quiz"]["wrong_questions"] = []
        
        save_session_data(st.session_state.current_session_id, st.session_state.current_session)
        st.experimental_rerun()
