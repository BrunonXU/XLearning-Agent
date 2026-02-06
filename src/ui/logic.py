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

def handle_chat_input(user_input: str) -> None:
    """
    Process user input via Orchestrator.
    This function should be called from the UI thread.
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
    # In legacy UI, we might need to add a temporary message or use st.empty()
    # For now, we'll create a "pending" message and update it
    msg_id = add_message(
        role="assistant", 
        content="Thinking...", 
        agent="orchestrator", 
        status="streaming"
    )
    
    try:
        # 4. Run Orchestrator (Blocking Call for now, TODO: Make async/streaming)
        # Since the backend is synchronous, we simulate streaming or just wait
        add_trace_event("orch_start", "progress", "Orchestrator Started")
        
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
