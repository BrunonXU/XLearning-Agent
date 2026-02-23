"""
XLearning Agent - UI State Management
=====================================
Handles: Session State Schema, JSON Persistence (Atomic Writes), KB State Machine
"""

import json
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List, Any

import streamlit as st

# ============================================================================
# Constants
# ============================================================================

DATA_DIR = Path("data")
INDEX_FILE = DATA_DIR / "index.json"
SESSIONS_DIR = DATA_DIR / "sessions"

# Ensure directories exist
DATA_DIR.mkdir(exist_ok=True)
SESSIONS_DIR.mkdir(exist_ok=True)

# ============================================================================
# I18N (Simple Dict Mapping)
# ============================================================================

TEXTS = {
    "zh": {
        "app_title": "XLearning",
        "new_chat": "+ 新对话",
        "mode": "模式",
        "standalone": "独立模式",
        "orchestrated": "协同模式",
        "language": "语言",
        "show_trace": "显示 Trace",
        "import_pdf": "上传 PDF",
        "import_github": "GitHub URL",
        "kb_status": "知识库",
        "kb_idle": "空闲",
        "kb_parsing": "解析中...",
        "kb_chunking": "分块中...",
        "kb_ready": "就绪",
        "kb_error": "错误",
        "recents": "最近对话",
        "welcome_title": "你好，准备好学习了吗？",
        "welcome_subtitle": "选择一个开始方式：",
        "action_pdf": "📄 分析 PDF",
        "action_github": "🔗 分析 GitHub 仓库",
        "action_plan": "🎓 创建学习计划",
        "action_chat": "💬 直接开始对话",
        "chat_placeholder": "输入消息...",
        "stop": "停止",
        "earlier_messages": "更早的消息",
        "evidence": "📚 证据来源",
        "tools": "🔧 工具调用",
        "quiz_tab": "测验",
        "report_tab": "报告",
        "trace_tab": "Trace",
        "chat_tab": "对话",
    },
    "en": {
        "app_title": "XLearning",
        "new_chat": "+ New Chat",
        "mode": "Mode",
        "standalone": "Standalone",
        "orchestrated": "Orchestrated",
        "language": "Language",
        "show_trace": "Show Trace",
        "import_pdf": "Upload PDF",
        "import_github": "GitHub URL",
        "kb_status": "Knowledge Base",
        "kb_idle": "Idle",
        "kb_parsing": "Parsing...",
        "kb_chunking": "Chunking...",
        "kb_ready": "Ready",
        "kb_error": "Error",
        "recents": "Recents",
        "welcome_title": "Hello, ready to learn?",
        "welcome_subtitle": "Choose how to start:",
        "action_pdf": "📄 Analyze PDF",
        "action_github": "🔗 Analyze GitHub Repo",
        "action_plan": "🎓 Create Study Plan",
        "action_chat": "💬 Just Chat",
        "chat_placeholder": "Type a message...",
        "stop": "Stop",
        "earlier_messages": "Earlier messages",
        "evidence": "📚 Evidence",
        "tools": "🔧 Tools",
        "quiz_tab": "Quiz",
        "report_tab": "Report",
        "trace_tab": "Trace",
        "chat_tab": "Chat",
    }
}

def t(key: str) -> str:
    """Get translated text for current language."""
    lang = st.session_state.get("lang", "zh")
    return TEXTS.get(lang, TEXTS["zh"]).get(key, key)

# ============================================================================
# Atomic JSON I/O
# ============================================================================

def _atomic_write(path: Path, data: Any) -> None:
    """
    Write JSON atomically: tmp file -> rename.
    Includes retry logic for Windows file locking ([WinError 5]).
    """
    tmp_path = path.with_suffix(f".{uuid.uuid4().hex[:6]}.tmp")
    try:
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        max_retries = 5
        for i in range(max_retries):
            try:
                if path.exists():
                    os.replace(tmp_path, path)
                else:
                    os.rename(tmp_path, path)
                return
            except OSError:
                if i == max_retries - 1:
                    raise
                import time
                time.sleep(0.1)
    except Exception as e:
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception:
            print(f"Failed to save {path}: {e}")
            pass
    finally:
        if tmp_path.exists():
            try:
                os.remove(tmp_path)
            except:
                pass

def _read_json(path: Path, default: Any = None) -> Any:
    """Read JSON file, return default if not exists."""
    if not path.exists():
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return default

# ============================================================================
# Session Index Management
# ============================================================================

def load_session_index() -> List[Dict]:
    return _read_json(INDEX_FILE, [])

def save_session_index(index: List[Dict]) -> None:
    _atomic_write(INDEX_FILE, index)

def get_session_path(session_id: str) -> Path:
    return SESSIONS_DIR / f"{session_id}.json"

def load_session_data(session_id: str) -> Optional[Dict]:
    path = get_session_path(session_id)
    return _read_json(path, None)

def save_session_data(session_id: str, data: Dict) -> None:
    path = get_session_path(session_id)
    _atomic_write(path, data)

# ============================================================================
# Session State Initialization
# ============================================================================

def init_session_state() -> None:
    """Initialize all session_state keys with defaults."""
    if "lang" not in st.session_state:
        st.session_state.lang = "zh"
    if "show_trace" not in st.session_state:
        st.session_state.show_trace = False
    if "dev_mode" not in st.session_state:
        st.session_state.dev_mode = False
    if "ui_mode" not in st.session_state:
        st.session_state.ui_mode = "guided"
    if "current_session_id" not in st.session_state:
        st.session_state.current_session_id = None
    # New 3-tab system: Plan, Study, Quiz
    if "active_tab" not in st.session_state:
        st.session_state.active_tab = "Plan"
    if "kb_status" not in st.session_state:
        st.session_state.kb_status = "idle"
    if "kb_info" not in st.session_state:
        st.session_state.kb_info = {
            "count": 0, "ts": None, "source": None, "last_error": None
        }
    if "is_processing" not in st.session_state:
        st.session_state.is_processing = False
    if "stop_requested" not in st.session_state:
        st.session_state.stop_requested = False
    if "session_index" not in st.session_state:
        st.session_state.session_index = load_session_index()
    if "current_session" not in st.session_state:
        st.session_state.current_session = None

# ============================================================================
# Session CRUD Operations
# ============================================================================

def create_new_session(title: str = "New Chat") -> str:
    session_id = str(uuid.uuid4())[:8]
    now = datetime.now().isoformat()
    meta = {
        "id": session_id, "title": title,
        "created_at": now, "updated_at": now,
        "kb_summary": None, "last_preview": ""
    }
    st.session_state.session_index.insert(0, meta)
    save_session_index(st.session_state.session_index)
    session_data = {
        "current_stage": "Plan",
        "has_input": False, "plan": None, "kb_count": 0,
        "study_progress": 0, "quiz_attempts": 0,
        "messages": [], "trace": [],
        "quiz": {"questions": [], "answers": {}, "wrong_questions": [], "score": None},
        "report": {"generated": False, "content": "", "ts": None},
        "_day_completed": {},
    }
    save_session_data(session_id, session_data)
    st.session_state.current_session_id = session_id
    st.session_state.current_session = session_data
    st.session_state.active_tab = "Plan"
    return session_id

def switch_session(session_id: str) -> None:
    st.session_state.current_session_id = session_id
    st.session_state.current_session = load_session_data(session_id)

def delete_session(session_id: str) -> None:
    """Delete a session by ID."""
    path = get_session_path(session_id)
    if path.exists():
        try:
            os.remove(path)
        except OSError:
            pass
    st.session_state.session_index = [
        m for m in st.session_state.session_index if m["id"] != session_id
    ]
    save_session_index(st.session_state.session_index)
    if st.session_state.current_session_id == session_id:
        st.session_state.current_session_id = None
        st.session_state.current_session = None


def rename_session(session_id: str, new_title: str) -> None:
    """Rename a session by ID."""
    new_title = new_title.strip()
    if not new_title:
        return
    for meta in st.session_state.session_index:
        if meta["id"] == session_id:
            meta["title"] = new_title
            meta["updated_at"] = datetime.now().isoformat()
            break
    save_session_index(st.session_state.session_index)


def clear_all_sessions() -> None:
    """清除所有对话记录和缓存数据（含 ChromaDB 向量库）。"""
    import shutil
    # 1. 删除所有 session JSON 文件
    if SESSIONS_DIR.exists():
        for f in SESSIONS_DIR.glob("*.json"):
            try:
                os.remove(f)
            except OSError:
                pass
    # 2. 清空 index
    save_session_index([])
    # 3. 清理 ChromaDB 数据
    chroma_dir = DATA_DIR / "chroma"
    if chroma_dir.exists():
        try:
            shutil.rmtree(chroma_dir)
            chroma_dir.mkdir(exist_ok=True)
        except OSError:
            pass
    # 4. 重置 session state
    st.session_state.session_index = []
    st.session_state.current_session_id = None
    st.session_state.current_session = None
    st.session_state.active_tab = "Plan"
    st.session_state.kb_status = "idle"
    st.session_state.kb_info = {"count": 0, "ts": None, "source": None, "last_error": None}
    # 5. 重置全局 Orchestrator（避免残留 RAG 引用）
    try:
        from src.ui.logic import _ORCHESTRATOR
        import src.ui.logic as logic_module
        if logic_module._ORCHESTRATOR is not None:
            logic_module._ORCHESTRATOR.reset()
            logic_module._ORCHESTRATOR = None
    except Exception:
        pass

def get_current_messages() -> List[Dict]:
    if st.session_state.current_session:
        return st.session_state.current_session.get("messages", [])
    return []


def add_message(role: str, content: str, agent: str = None,
                citations: List = None, parent_step_id: str = None,
                status: str = "complete") -> str:
    if not st.session_state.current_session:
        return None
    msg_id = f"msg_{uuid.uuid4().hex[:6]}"
    msg = {
        "id": msg_id, "role": role, "agent": agent,
        "content": content, "status": status,
        "parent_step_id": parent_step_id, "error": None,
        "citations": citations or [], "ts": datetime.now().isoformat()
    }
    st.session_state.current_session["messages"].append(msg)
    for meta in st.session_state.session_index:
        if meta["id"] == st.session_state.current_session_id:
            meta["last_preview"] = content[:50] + "..." if len(content) > 50 else content
            meta["updated_at"] = datetime.now().isoformat()
            break
    save_session_data(st.session_state.current_session_id, st.session_state.current_session)
    save_session_index(st.session_state.session_index)
    return msg_id

def add_trace_event(step_id: str, event_type: str, name: str, detail: str = None) -> None:
    if not st.session_state.current_session:
        return
    event = {
        "step_id": step_id, "type": event_type, "name": name,
        "detail": detail, "ts": datetime.now().isoformat()
    }
    st.session_state.current_session["trace"].append(event)
    save_session_data(st.session_state.current_session_id, st.session_state.current_session)

def clear_session_trace() -> None:
    if not st.session_state.current_session:
        return
    st.session_state.current_session["trace"] = []
    save_session_data(st.session_state.current_session_id, st.session_state.current_session)

# ============================================================================
# KB State Machine
# ============================================================================

def set_kb_status(status: str, source: str = None, count: int = None, error: str = None) -> None:
    st.session_state.kb_status = status
    if source is not None:
        st.session_state.kb_info["source"] = source
    if count is not None:
        st.session_state.kb_info["count"] = count
    if error is not None:
        st.session_state.kb_info["last_error"] = error
    if status == "ready":
        st.session_state.kb_info["ts"] = datetime.now().isoformat()
        st.session_state.kb_info["last_error"] = None

# ============================================================================
# Stage Logic (Simplified 3-tab: Plan, Study, Quiz)
# ============================================================================

def calculate_stage_logic(session: Dict) -> Dict:
    """Calculate stage status for the simplified 3-tab stepper."""
    if not session:
        return {}

    has_input = session.get("has_input", False)
    plan_exists = session.get("plan") is not None
    kb_count = session.get("kb_count", 0)
    study_progress = session.get("study_progress", 0)
    quiz_attempts = session.get("quiz_attempts", 0)
    has_report = session.get("report", {}).get("generated", False)

    stages = {
        "Plan": {
            "label": "规划",
            "icon": "📋",
            "ready": True,
            "done": plan_exists or has_input,
        },
        "Study": {
            "label": "学习",
            "icon": "📖",
            "ready": True,
            "done": study_progress > 0,
        },
        "Quiz": {
            "label": "测验",
            "icon": "📝",
            "ready": True,
            "done": quiz_attempts > 0,
        },
    }

    return {
        "stages": stages,
        "current_stage": session.get("current_stage", "Plan"),
        "kb_ready": kb_count > 0,
    }
