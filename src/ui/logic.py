"""
XLearning Agent - UI Logic Bridge
=================================
Connects UI events to the Backend Orchestrator.
Handles: Agent Stream, Tools Events, Exception Management.
"""

import time
import threading
from typing import Generator, Optional

import streamlit as st
from src.agents.orchestrator import Orchestrator, OrchestratorMode
from src.ui.state import add_message, add_trace_event, set_kb_status

# Global Orchestrator instance (lazy loaded)
_ORCHESTRATOR = None

def get_orchestrator() -> Orchestrator:
    """Get or create singleton Orchestrator instance."""
    global _ORCHESTRATOR
    if _ORCHESTRATOR is None:
        # Check session state for mode
        mode_str = st.session_state.get("mode", "standalone")
        mode = OrchestratorMode.STANDALONE if mode_str == "standalone" else OrchestratorMode.COORDINATED
        _ORCHESTRATOR = Orchestrator(mode=mode)
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
    
    # Add user message immediately
    # (Already added by renderer usually, but good to ensure)
    # add_message("user", user_input) 
    
    # 1. Initialize Orchestrator
    orchestrator = get_orchestrator()
    
    # 2. Update Mode (if changed in UI)
    current_mode = OrchestratorMode.STANDALONE if st.session_state.mode == "standalone" else OrchestratorMode.COORDINATED
    if orchestrator.mode != current_mode:
        orchestrator.switch_mode(current_mode)

    # 3. Create a placeholder for streaming response
    msg_id = add_message(
        role="assistant", 
        content="Thinking...", 
        agent="orchestrator", 
        status="streaming"
    )
    
    try:
        # 4. Run Orchestrator with MOCK TRACE SIMULATION
        add_trace_event("orch_start", "progress", "Orchestrator Started")
        
        # --- SIMULATION START ---
        import uuid
        import time
        import random
        
        # Step 1: Planning
        step1 = "step_" + uuid.uuid4().hex[:4]
        add_trace_event(step1, "tool_start", "PlannerAgent", "Analyzing user intent...")
        time.sleep(0.8)
        add_trace_event(step1, "tool_end", "PlannerAgent", "Intent detected: Knowledge Acquisition")
        
        # Step 2: Retrieval
        step2 = "step_" + uuid.uuid4().hex[:4]
        add_trace_event(step2, "tool_start", "TutorAgent", "Searching Knowledge Base...")
        time.sleep(1.2)
        add_trace_event(step2, "tool_end", "TutorAgent", f"Retrieved {random.randint(2,5)} relevant chunks")
        
        # Step 3: Verification (Optional random)
        if random.random() > 0.5:
            step3 = "step_" + uuid.uuid4().hex[:4]
            add_trace_event(step3, "tool_start", "ValidatorAgent", "Fact-checking response...")
            time.sleep(0.6)
            add_trace_event(step3, "tool_end", "ValidatorAgent", "Confidence Score: 0.95")
        # --- SIMULATION END ---

        response = orchestrator.run(user_input)
        
        # 5. Update complete message
        # In a real streaming setup, we would update chunk by chunk.
        # Here we just update the final content.
        
        # Manually update the message in state (hacky but works for P1)
        if st.session_state.current_session:
            for msg in st.session_state.current_session["messages"]:
                if msg["id"] == msg_id:
                    msg["content"] = response
                    msg["status"] = "complete"
                    msg["agent"] = "tutor" # Default to Tutor for now
                    break
        
        add_trace_event("orch_end", "tool_end", "Orchestrator Finished")
        
    except Exception as e:
        # Handle Error
        if st.session_state.current_session:
            for msg in st.session_state.current_session["messages"]:
                if msg["id"] == msg_id:
                    msg["content"] = f"Error: {str(e)}"
                    msg["status"] = "error"
                    msg["error"] = str(e)
                    break
        st.error(f"Processing Error: {e}")
    
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
