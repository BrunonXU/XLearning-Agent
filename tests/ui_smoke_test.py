"""
UI Smoke Test
=============
This script runs all UI components in isolation to verify they render without errors.
Run this before notifying the user of UI changes.

Usage:
    streamlit run tests/ui_smoke_test.py --server.port 8640
"""

import streamlit as st
import sys
import os
from datetime import datetime

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.ui.state import init_session_state
# MOCK SESSION STATE
st.session_state.lang = "zh"
st.session_state.mode = "standalone"
st.session_state.show_trace = True
st.session_state.current_session_id = "test_session"
st.session_state.kb_status = "ready"
st.session_state.kb_info = {"source": "test.pdf", "count": 10, "ts": "2023-01-01 12:00:00"}
st.session_state.is_processing = False

# Mock Data
st.session_state.current_session = {
    "title": "Smoke Test Session",
    "messages": [
        {"id": "1", "role": "user", "content": "Hello"},
        {"id": "2", "role": "assistant", "agent": "tutor", "content": "Hi there!", "status": "complete"},
        {"id": "3", "role": "assistant", "agent": "planner", "content": "Planning...", "status": "streaming"}
    ],
    "trace": [
        {"step_id": "s1", "type": "tool_start", "name": "Tool A", "ts": "2023-01-01 12:00:01"},
        {"step_id": "s1", "type": "tool_end", "name": "Tool A", "ts": "2023-01-01 12:00:02"}
    ],
    "quiz": {
        "questions": [
            {"qid": "q1", "question": "Test Q?", "choices": ["A", "B"], "answer_index": 0}
        ],
        "answers": {},
        "wrong_questions": [],
        "score": None
    },
    "report": {
        "generated": True,
        "content": "# Test Report\nContent"
    }
}
st.session_state.session_index = [
    {"id": "test_session", "title": "Test Session", "created_at": "...", "updated_at": "..."}
]

import src.ui.layout as layout
import src.ui.renderer as renderer

st.title("🧪 UI Smoke Test")
st.markdown("Rendering all components to check for TypeErrors or Layout issues.")

st.divider()

st.header("1. Sidebar")
try:
    layout.render_sidebar()
    st.success("✅ Sidebar Rendered")
except Exception as e:
    st.error(f"❌ Sidebar Failed: {e}")

st.divider()

st.header("2. Welcome Panel")
try:
    layout.render_welcome_panel()
    st.success("✅ Welcome Panel Rendered")
except Exception as e:
    st.error(f"❌ Welcome Panel Failed: {e}")

st.divider()

st.header("3. Chat Tab")
try:
    renderer.render_chat_tab()
    st.success("✅ Chat Tab Rendered")
except Exception as e:
    st.error(f"❌ Chat Tab Failed: {e}")

st.divider()

st.header("4. Trace Tab")
try:
    renderer.render_trace_tab()
    st.success("✅ Trace Tab Rendered")
except Exception as e:
    st.error(f"❌ Trace Tab Failed: {e}")

st.divider()

st.header("5. Quiz Tab")
try:
    renderer.render_quiz_tab()
    st.success("✅ Quiz Tab Rendered")
except Exception as e:
    st.error(f"❌ Quiz Tab Failed: {e}")
