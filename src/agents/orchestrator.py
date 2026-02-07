"""
Orchestrator - 协调器

职责：
1. 意图识别（用户想做什么）
2. 模式选择（单独/协调）
3. Agent 调度
4. 状态管理

双模式设计：
- 单独模式（Standalone）：用户精细控制每个 Agent
- 协调模式（Coordinated）：自动编排完整流程

设计亮点：
1. 意图识别 - 关键词匹配（可扩展为 LLM 识别）
2. 状态机 - IDLE → PLANNING → LEARNING → VALIDATING → COMPLETED
3. Agent 调度 - 解耦调度层和业务逻辑

面试话术：
> "Orchestrator 是整个系统的调度中心。它实现了两种模式：
>  单独模式适合想精细控制的用户，协调模式自动完成全流程。
>  核心思想是'谁来做'和'怎么做'分离，调度层只负责路由。"
"""

from typing import Optional, Dict, Any, List
from enum import Enum

from .base import BaseAgent
from .planner import PlannerAgent
from .tutor import TutorAgent
from .validator import ValidatorAgent
from src.core.file_manager import FileManager
from src.core.models import SessionState, SessionMode
from src.rag import RAGEngine


class OrchestratorMode(str, Enum):
    """协调器模式"""
    STANDALONE = "standalone"  # 单独模式
    COORDINATED = "coordinated"  # 协调模式


class OrchestratorState(str, Enum):
    """协调器状态"""
    IDLE = "idle"              # 空闲
    PLANNING = "planning"      # 规划中
    LEARNING = "learning"      # 学习中
    VALIDATING = "validating"  # 验证中
    COMPLETED = "completed"    # 已完成


class Orchestrator:
    """
    协调器
    
    统一入口，管理整个学习流程
    
    面试话术：
    > "Orchestrator 实现了两种模式：单独模式适合想精细控制的用户，
    >  协调模式适合想一键完成全流程的用户。核心思想是把'谁来做'
    >  和'怎么做'分离，协调层只负责调度，不关心具体业务逻辑。"
    """
    
    def __init__(
        self,
        mode: OrchestratorMode = OrchestratorMode.STANDALONE,
        domain: Optional[str] = None,
        on_event: Optional[Any] = None,
    ):
        """
        初始化协调器
        
        Args:
            mode: 运行模式
            domain: 学习领域
            on_event: 事件回调 (event_type, name, detail)
        """
        self.mode = mode
        self.domain = domain
        self.state = OrchestratorState.IDLE
        self.on_event = on_event
        
        # 初始化 Agents 并注入回调
        self.planner = PlannerAgent(on_event=on_event)
        self.tutor = TutorAgent(on_event=on_event)
        self.validator = ValidatorAgent(on_event=on_event)
        
        # 文件管理器（领域确定后初始化）
        self.file_manager: Optional[FileManager] = None
        
        # RAG 引擎
        self.rag_engine: Optional[RAGEngine] = None
        
        # 会话状态
        self.session_state: Optional[SessionState] = None
    
    def set_domain(self, domain: str):
        """设置学习领域"""
        import re
        
        # Sanitize domain for filesystem safety (remove invalid chars)
        safe_domain = re.sub(r'[<>:"/\\|?*]', '', domain).strip()
        if not safe_domain:
            safe_domain = "default_domain"
            
        self.domain = safe_domain
        self.file_manager = FileManager(self.domain)
        
        # 清理 collection 名称（只保留英文、数字、下划线、点、横线）
        safe_name = re.sub(r'[^a-zA-Z0-9._-]', '', domain.replace(' ', '_'))
        if not safe_name:
            safe_name = "default"
        # 确保不以下划线开头/结尾
        safe_name = safe_name.strip('_.-')
        if len(safe_name) < 3:
            safe_name = "kb" + safe_name
        
        self.rag_engine = RAGEngine(collection_name=f"knowledge_{safe_name}")
        self.tutor.set_rag_engine(self.rag_engine)
        
        # 初始化会话状态
        self.session_state = SessionState(domain=domain)
    
    def _emit_event(self, event_type: str, name: str, detail: str = ""):
        """发射追踪事件"""
        if self.on_event:
            self.on_event(event_type, name, detail)

    def process_file(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        """
        处理上传的文件
        
        面试话术：
        > "process_file 是统一的文件处理入口。不管用户上传 PDF 还是其他文件，
        >  都会自动识别类型、提取内容、存入 RAG。"
        
        Args:
            file_content: 文件二进制内容
            filename: 文件名
            
        Returns:
            处理结果字典
        """
        from src.specialists.pdf_analyzer import PDFAnalyzer
        
        self._emit_event("tool_start", "FileProcessor", f"Analyzing {filename}...")
        
        if filename.lower().endswith(".pdf"):
            analyzer = PDFAnalyzer()
            pdf_content = analyzer.analyze_from_bytes(file_content, filename)
            
            chunk_count = 0
            # 导入 RAG
            if self.rag_engine is None:
                # Auto-initialize domain/RAG if not set
                print(f"[Orchestrator] Auto-setting domain to: {pdf_content.title}")
                self.set_domain(pdf_content.title or "default_domain")

            if self.rag_engine:
                ids = analyzer.import_to_rag(pdf_content, self.rag_engine)
                chunk_count = len(ids)
            
            self._emit_event("tool_end", "FileProcessor", f"Successfully indexed {pdf_content.title} ({chunk_count} chunks)")
            
            return {
                "success": True,
                "message": f"✅ 已处理 PDF: {pdf_content.title}\n- 共 {pdf_content.total_pages} 页\n- 已生成 {chunk_count} 个知识切片",
                "title": pdf_content.title,
                "pages": pdf_content.total_pages,
                "chunks": chunk_count
            }
        else:
            self._emit_event("tool_end", "FileProcessor", f"Unsupported file type: {filename}")
            # 其他文件类型暂不支持
            return {
                "success": False,
                "message": f"⚠️ 暂不支持 {filename} 的文件类型",
                "chunks": 0
            }

    def run(
        self,
        user_input: str,
        history: Optional[List[Dict[str, str]]] = None,
        **kwargs
    ) -> str:
        """
        处理用户输入
        """
        mode_cn = "自动协调" if self.mode == OrchestratorMode.COORDINATED else "独立"
        self._emit_event("progress", "Orchestrator", f"正在以 {mode_cn} 模式启动")
        if self.mode == OrchestratorMode.COORDINATED:
            return self._run_coordinated(user_input, history=history, **kwargs)
        else:
            return self._run_standalone(user_input, history=history, **kwargs)

    def _run_standalone(self, user_input: str, history: Optional[List[Dict[str, str]]] = None, **kwargs) -> str:
        """
        单独模式：根据意图调用对应 Agent
        """
        intent = self._detect_intent(user_input)
        self._emit_event("progress", "IntentDetection", f"识别到的意图: {intent}")
        
        if intent == "create_plan":
            return self._handle_create_plan(user_input)
        elif intent == "ask_question":
            return self._handle_ask_question(user_input, history=history)
        elif intent == "start_quiz":
            return self._handle_start_quiz(user_input)
        elif intent == "get_report":
            return self._handle_get_report()
        else:
            # 默认当作问答处理
            return self._handle_ask_question(user_input, history=history)
    
    def _run_coordinated(self, user_input: str, history: Optional[List[Dict[str, str]]] = None, **kwargs) -> str:
        """
        协调模式：自动执行完整流程，同时响应用户意图
        """
        intent = self._detect_intent(user_input)
        self._emit_event("progress", "IntentDetection", f"协调模式意图识别: {intent}")

        # 如果用户明确提到“重新开始”或者切换了话题（简单检测）
        if any(kw in user_input for kw in ["重新开始", "换个话题", "新课程"]):
            self.state = OrchestratorState.IDLE
            self._emit_event("progress", "Orchestrator", "已重置流程状态")

        # 1. 如果处于初始状态，且意图是学习或问答，先触发规划
        if self.state == OrchestratorState.IDLE:
            self.state = OrchestratorState.PLANNING
            self._emit_event("progress", "Orchestrator", "进入规划阶段")
            plan_msg = self._handle_create_plan(user_input)
            
            # 如果意图只是问个简单问题，规划完直接进入学习并回答
            self.state = OrchestratorState.LEARNING
            if intent == "ask_question":
                answer = self._handle_ask_question(user_input, history=history)
                return f"📋 **我已为您制定了学习计划：**\n\n{plan_msg}\n\n---\n\n🎓 **针对您的问题，我的解答如下：**\n\n{answer}"
            return plan_msg

        # 2. 如果已经在学习中，根据意图路由
        if intent == "start_quiz":
            self.state = OrchestratorState.VALIDATING
            return self._handle_start_quiz(user_input)
        elif intent == "get_report":
            return self._handle_get_report()
        elif intent == "create_plan" and self.state != OrchestratorState.PLANNING:
            return self._handle_create_plan(user_input)
        else:
            # 默认：在当前背景下进行辅导
            return self._handle_ask_question(user_input, history=history)
    
    def _detect_intent(self, user_input: str) -> str:
        """
        意图识别
        
        简化版：基于关键词匹配（注意优先级，先检查更具体的）
        TODO: 可以用 LLM 进行更智能的意图识别
        
        面试话术：
        > "意图识别是 Orchestrator 的入口。我用关键词匹配做初版，
        >  按优先级检查：测验 > 报告 > 创建计划 > 问答。后续可以升级为 LLM 分类。"
        """
        input_lower = user_input.lower()
        
        # 优先级：测验 > 报告 > 创建计划 > 问答
        if any(kw in input_lower for kw in ["测验", "quiz", "测试", "考试"]):
            return "start_quiz"
        elif any(kw in input_lower for kw in ["报告", "进度", "report", "progress"]):
            return "get_report"
        elif any(kw in input_lower for kw in ["计划", "plan", "学习"]):
            return "create_plan"
        else:
            return "ask_question"
    
    def _handle_create_plan(self, user_input: str) -> str:
        """处理创建计划请求"""
        if not self.domain:
            self.set_domain(user_input[:50])  # 用输入的前 50 字符作为领域名
        
        # 0. 尝试从 RAG 获取上下文
        rag_context = ""
        if self.rag_engine:
            # 简单策略：如果用户输入很短（如"生成计划"），则获取 RAG 中的全库摘要
            # 如果用户输入具体（如"学习 Transformer"），则检索相关
            if len(user_input) < 20: 
                # 模拟全库摘要：获取任意一些切片
                rag_context = self.rag_engine.build_context("summary overview", k=5)
            else:
                rag_context = self.rag_engine.build_context(user_input, k=5)
                
        # 1. 构造输入给 Planner
        # 如果有 RAG 上下文，将其附在输入后
        planner_input = user_input
        if rag_context:
            planner_input = f"用户目标: {user_input}\n\n参考资料内容:\n{rag_context}"

        plan = self.planner.run(planner_input)
        
        # 保存计划
        if self.file_manager:
            self.file_manager.save_plan(plan.to_markdown())
        
        # 导入 RAG
        if self.rag_engine:
            self.rag_engine.add_document(
                plan.to_markdown(),
                metadata={"source": "learning_plan", "type": "plan"}
            )
        
        return f"✅ 学习计划已生成！\n\n{plan.to_markdown()}"
    
    def _handle_ask_question(self, user_input: str, history: Optional[List[Dict[str, str]]] = None) -> str:
        """处理问答请求"""
        return self.tutor.run(user_input, mode=SessionMode.FREE, history=history)
    
    def _handle_start_quiz(self, user_input: str) -> str:
        """处理开始测验请求"""
        # 获取 RAG 内容作为参考
        content = ""
        if self.rag_engine:
            content = self.rag_engine.build_context(user_input, k=3)
        
        quiz = self.validator.generate_quiz(
            topic=self.domain or "学习测验",
            content=content,
            num_questions=5,
        )
        
        return self.tutor.start_quiz(quiz)
    
    def _handle_get_report(self) -> str:
        """处理获取报告请求"""
        report = self.validator.generate_report(
            domain=self.domain or "Unknown",
            file_manager=self.file_manager,
        )
        return report.to_markdown()
    
    def switch_mode(self, mode: OrchestratorMode):
        """切换模式"""
        self.mode = mode
        self.state = OrchestratorState.IDLE
    
    def reset(self):
        """重置状态"""
        self.state = OrchestratorState.IDLE
        self.session_state = None
