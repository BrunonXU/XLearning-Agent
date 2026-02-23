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
    
    # ===== 卡死恢复：如果 is_processing 超过 90 秒，强制解锁 =====
    import time as _time
    if st.session_state.get("is_processing", False):
        started_at = st.session_state.get("_processing_started_at", 0)
        if started_at and (_time.time() - started_at > 90):
            print("[WARN] is_processing stuck for >90s, force unlocking...")
            st.session_state.is_processing = False
            # 把卡住的 streaming 消息标记为 error
            if st.session_state.current_session:
                for msg in st.session_state.current_session.get("messages", []):
                    if msg.get("status") == "streaming":
                        msg["status"] = "error"
                        msg["content"] = "⚠️ 请求超时，请重试。"
                from src.ui.state import save_session_data
                save_session_data(st.session_state.current_session_id, st.session_state.current_session)
            st.session_state.pending_chat_query = None
            st.session_state.pending_msg_id = None
            if should_rerun:
                st.experimental_rerun()
            return
    
    if "pending_chat_query" not in st.session_state or not st.session_state.pending_chat_query:
        return

    user_input = st.session_state.pending_chat_query
    msg_id = st.session_state.pending_msg_id
    
    # 记录处理开始时间（用于卡死检测）
    st.session_state._processing_started_at = _time.time()
    
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

        # 防止跨会话污染：切换到新 session 时重置 Orchestrator 状态机与意图缓存
        # 但保留当前 session 已建立的 domain 和 rag_engine（PDF 上传时已设置）
        current_sid = st.session_state.get("current_session_id")
        bound_sid = getattr(orchestrator, "_bound_session_id", None)
        if current_sid and bound_sid != current_sid:
            # 保存当前 domain/rag_engine（可能是 handle_file_upload 刚设置的）
            prev_domain = orchestrator.domain
            prev_rag = orchestrator.rag_engine
            prev_tutor_rag = orchestrator.tutor.rag_engine
            prev_fm = orchestrator.file_manager
            prev_doc_meta = orchestrator.tutor.doc_meta
            
            orchestrator.reset()
            orchestrator._intent_cache = {}
            orchestrator._bound_session_id = current_sid
            
            # 恢复同一 session 内已建立的 domain/rag（PDF 上传发生在同一 session）
            if prev_domain and prev_rag:
                orchestrator.domain = prev_domain
                orchestrator.rag_engine = prev_rag
                orchestrator.tutor.set_rag_engine(prev_tutor_rag or prev_rag)
                orchestrator.file_manager = prev_fm
                orchestrator.tutor.set_doc_meta(prev_doc_meta)
                trace_callback("progress", "Orchestrator", f"新会话已绑定，保留已有知识库: {prev_domain}")
            else:
                # 尝试从 session data 恢复 domain（用户从历史记录切换回来时）
                saved_domain = None
                saved_doc_meta = None
                if st.session_state.current_session:
                    saved_domain = st.session_state.current_session.get("_orch_domain")
                    saved_doc_meta = st.session_state.current_session.get("_doc_meta")
                if saved_domain:
                    orchestrator.set_domain(saved_domain)
                    if saved_doc_meta:
                        orchestrator.tutor.set_doc_meta(saved_doc_meta)
                    trace_callback("progress", "Orchestrator", f"从会话数据恢复知识库: {saved_domain}")
                else:
                    trace_callback("progress", "Orchestrator", "检测到新会话，已重置状态机与意图缓存。")
        
        # Default to coordinated for now as it handles classification
        mode_str = "coordinated"
        current_mode = OrchestratorMode.STANDALONE if mode_str == "standalone" else OrchestratorMode.COORDINATED
        if orchestrator.mode != current_mode:
            orchestrator.switch_mode(current_mode)
        
        trace_callback("progress", "Orchestrator", "正在处理您的输入...")
        
        # Extract history (last 20 messages, tutor internally handles compression)
        history = []
        if st.session_state.current_session:
            all_msgs = st.session_state.current_session.get("messages", [])
            # Exclude the very last placeholder message that is currently "正在思考中..."
            raw_history = all_msgs[:-2] if len(all_msgs) >= 2 else []
            for m in raw_history[-20:]:
                if m.get("role") in ("user", "assistant"):
                    history.append({"role": m["role"], "content": m["content"]})

        # 5. Execute via unified stream entry:
        # orchestrator.stream() 内部会对问答走流式，对计划/测验/报告自动退化为一次性输出。
        print(f"[DEBUG] Processing input length {len(user_input)} with history length {len(history)}...")
        trace_callback("progress", "Orchestrator", "正在生成回答...")

        accumulated = ""
        chunk_count = 0
        stream_timeout = 60  # 单次流式输出最长 60 秒
        stream_start = _time.time()
        for chunk in orchestrator.stream(user_input, history=history):
            chunk_count += 1
            accumulated += chunk
            if st.session_state.current_session:
                for msg in st.session_state.current_session["messages"]:
                    if msg["id"] == msg_id:
                        msg["content"] = accumulated
                        msg["status"] = "streaming"
                        msg["agent"] = "tutor"
                        break
            # 超时保护
            if _time.time() - stream_start > stream_timeout:
                accumulated += "\n\n⚠️ 响应时间过长，已截断。"
                break
        response = accumulated

        if chunk_count > 1:
            trace_callback("progress", "TutorAgent", f"流式输出完成（chunks={chunk_count}）")
        
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
        
        # 7. Update Session Logic State — 智能检测响应类型，同步 session 状态
        session = st.session_state.current_session
        if session:
            session["has_input"] = True
            
            # 检测是否生成了学习计划
            if "学习计划" in response or "📋" in response or "阶段" in response:
                session["plan"] = {"status": "generated"}
                # 缓存最新计划内容到 session，供右侧面板直接读取
                session["_cached_plan_md"] = response
            
            # 检测是否进入学习阶段
            if session.get("plan"):
                session["study_progress"] = max(session.get("study_progress", 0), 1)
            
            # 检测是否触发了 Quiz（Chat 中输入"测验"等关键词）
            if "开始测验" in response or "📝 **开始测验" in response:
                # Orchestrator 通过 TutorAgent.start_quiz() 返回了测验内容
                # 尝试从 Orchestrator 的 Tutor 获取当前 quiz 数据并同步到 session
                try:
                    tutor = orchestrator.tutor
                    if tutor.current_quiz and tutor.current_quiz.questions:
                        ui_questions = []
                        for i, q in enumerate(tutor.current_quiz.questions):
                            ui_questions.append({
                                "qid": f"q{i+1}",
                                "question": q.question,
                                "options": q.options if q.options else ["A", "B", "C", "D"],
                                "correct_answer": q.correct_answer,
                                "explanation": q.explanation,
                                "topic": q.topic,
                            })
                        session["quiz"]["questions"] = ui_questions
                        session["quiz"]["score"] = None
                        session["quiz"]["wrong_questions"] = []
                        session["quiz"]["answers"] = {}
                        session["quiz_attempts"] = session.get("quiz_attempts", 0) + 1
                except Exception:
                    pass  # Quiz 同步失败不影响主流程

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
        st.session_state._processing_started_at = 0
        from src.ui.state import save_session_data
        save_session_data(st.session_state.current_session_id, st.session_state.current_session)
        
        if should_rerun:
            st.experimental_rerun()

def handle_file_upload(file) -> None:
    """Handle file upload via Orchestrator (PDF / MD / TXT / DOCX)."""
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
                    # 持久化 domain 信息，以便跨 rerun 恢复 RAG 连接
                    if orchestrator.domain:
                        st.session_state.current_session["_orch_domain"] = orchestrator.domain
                    # 持久化文档元信息，以便跨 rerun 恢复 tutor 的文档感知
                    if orchestrator.tutor.doc_meta:
                        st.session_state.current_session["_doc_meta"] = orchestrator.tutor.doc_meta
                
                add_message("system", result.get("message"), agent="validator")
            else:
                set_kb_status("error", error=result.get("message"))
                add_message("system", result.get("message"), agent="system", status="error")
        
    except Exception as e:
        set_kb_status("error", error=str(e))
        st.error(f"Upload failed: {e}")

def handle_generate_quiz() -> None:
    """
    生成测验 — 调用真实后端 Orchestrator → ValidatorAgent。
    
    将 ValidatorAgent 生成的 Quiz 对象转换为 UI session 格式，
    确保 Quiz Tab 和 Chat 入口使用同一份数据。
    """
    from src.ui.state import save_session_data, add_trace_event
    import uuid
    
    if not st.session_state.current_session:
        return
    
    st.session_state.is_processing = True
    
    try:
        # 1. 获取 Orchestrator
        def trace_callback(event_type, name, detail=""):
            step_id = "quiz_" + uuid.uuid4().hex[:4]
            add_trace_event(step_id, event_type, name, detail)
        
        orchestrator = get_orchestrator(on_event=trace_callback)
        
        # 从 session 恢复 domain（Orchestrator 可能因 rerun 丢失状态）
        quiz_topic = orchestrator.domain or ""
        if not quiz_topic and st.session_state.current_session:
            quiz_topic = st.session_state.current_session.get("_orch_domain", "")
            doc_meta = st.session_state.current_session.get("_doc_meta")
            if doc_meta:
                quiz_topic = doc_meta.get("title", quiz_topic)
            # 同时恢复 orchestrator 的 domain 和 RAG
            if quiz_topic and not orchestrator.domain:
                orchestrator.set_domain(quiz_topic)
                if doc_meta:
                    orchestrator.tutor.set_doc_meta(doc_meta)
        if not quiz_topic:
            quiz_topic = "学习测验"
        
        # 2. 获取 RAG 内容作为出题参考
        content = ""
        if orchestrator.rag_engine:
            content = orchestrator.rag_engine.build_context(
                quiz_topic, k=3
            )
        
        # 3. 调用 ValidatorAgent 生成真实 Quiz
        quiz = orchestrator.validator.generate_quiz(
            topic=quiz_topic,
            content=content,
            num_questions=5,
        )
        
        # 4. 转换为 UI session 格式
        ui_questions = []
        for i, q in enumerate(quiz.questions):
            ui_questions.append({
                "qid": f"q{i+1}",
                "question": q.question,
                "options": q.options if q.options else ["A", "B", "C", "D"],
                "correct_answer": q.correct_answer,
                "explanation": q.explanation,
                "topic": q.topic,
            })
        
        # 5. 写入 session（Quiz Tab 和 Chat 共享这份数据）
        st.session_state.current_session["quiz_attempts"] = (
            st.session_state.current_session.get("quiz_attempts", 0) + 1
        )
        st.session_state.current_session["quiz"]["questions"] = ui_questions
        st.session_state.current_session["quiz"]["score"] = None
        st.session_state.current_session["quiz"]["wrong_questions"] = []
        st.session_state.current_session["quiz"]["answers"] = {}
        
        # 6. 同时在聊天中显示 quiz 开始提示
        quiz_msg = f"📝 **测验已生成：{quiz.topic}**\n\n共 {len(ui_questions)} 道题目，请切换到测验面板作答。"
        add_message("assistant", quiz_msg, agent="validator")
        
        save_session_data(st.session_state.current_session_id, st.session_state.current_session)
        
    except Exception as e:
        import traceback
        add_message("assistant", f"⚠️ 测验生成失败: {str(e)}", agent="validator", status="error")
        print(f"[Quiz Generation Error] {traceback.format_exc()}")
    
    finally:
        st.session_state.is_processing = False
        st.experimental_rerun()


def handle_generate_report() -> None:
    """
    生成学习进度报告 — 调用真实后端 Orchestrator → ValidatorAgent。
    
    将 ProgressReport 写入 session，供 Report Tab 展示和下载。
    """
    from src.ui.state import save_session_data, add_trace_event
    import uuid
    
    if not st.session_state.current_session:
        return
    
    st.session_state.is_processing = True
    
    try:
        # 1. 获取 Orchestrator
        def trace_callback(event_type, name, detail=""):
            step_id = "report_" + uuid.uuid4().hex[:4]
            add_trace_event(step_id, event_type, name, detail)
        
        orchestrator = get_orchestrator(on_event=trace_callback)
        
        # 从 session 恢复 domain
        report_domain = orchestrator.domain or ""
        if not report_domain and st.session_state.current_session:
            report_domain = st.session_state.current_session.get("_orch_domain", "")
            doc_meta = st.session_state.current_session.get("_doc_meta")
            if doc_meta:
                report_domain = doc_meta.get("title", report_domain)
        if not report_domain:
            report_domain = "学习报告"
        
        # 2. 调用 ValidatorAgent 生成报告
        report = orchestrator.validator.generate_report(
            domain=report_domain,
            file_manager=orchestrator.file_manager,
        )
        
        # 3. 写入 session
        report_md = report.to_markdown()
        st.session_state.current_session["report"] = {
            "generated": True,
            "content": report_md,
            "ts": __import__("datetime").datetime.now().isoformat(),
        }
        
        # 4. 聊天中也显示报告生成提示
        add_message("assistant", f"📊 **学习进度报告已生成！**\n\n{report_md}", agent="validator")
        
        save_session_data(st.session_state.current_session_id, st.session_state.current_session)
        
    except Exception as e:
        import traceback
        add_message("assistant", f"⚠️ 报告生成失败: {str(e)}", agent="validator", status="error")
        print(f"[Report Generation Error] {traceback.format_exc()}")
    
    finally:
        st.session_state.is_processing = False
        st.experimental_rerun()
