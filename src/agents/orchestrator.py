"""
Orchestrator - 协调器

职责：
1. 意图识别（用户想做什么）
2. 模式选择（单独/协调）
3. Agent 调度
4. 状态管理

双模式设计：
- 单独模式：用户精细控制每个 Agent
- 协调模式：自动编排完整流程

借鉴来源：melxy1997-ColumnWriter 的 Orchestrator 设计

TODO (Day 7):
- 实现完整的双模式逻辑
- 接入 LangSmith 追踪
- [可选] 用 LangGraph 重写
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
    ):
        """
        初始化协调器
        
        Args:
            mode: 运行模式
            domain: 学习领域
        """
        self.mode = mode
        self.domain = domain
        self.state = OrchestratorState.IDLE
        
        # 初始化 Agents
        self.planner = PlannerAgent()
        self.tutor = TutorAgent()
        self.validator = ValidatorAgent()
        
        # 文件管理器（领域确定后初始化）
        self.file_manager: Optional[FileManager] = None
        
        # RAG 引擎
        self.rag_engine: Optional[RAGEngine] = None
        
        # 会话状态
        self.session_state: Optional[SessionState] = None
    
    def set_domain(self, domain: str):
        """设置学习领域"""
        self.domain = domain
        self.file_manager = FileManager(domain)
        self.rag_engine = RAGEngine(collection_name=f"knowledge_{domain}")
        self.tutor.set_rag_engine(self.rag_engine)
        
        # 初始化会话状态
        self.session_state = SessionState(domain=domain)
    
    def run(
        self,
        user_input: str,
        **kwargs
    ) -> str:
        """
        处理用户输入
        
        Args:
            user_input: 用户输入
            **kwargs: 其他参数
            
        Returns:
            响应内容
        """
        if self.mode == OrchestratorMode.COORDINATED:
            return self._run_coordinated(user_input, **kwargs)
        else:
            return self._run_standalone(user_input, **kwargs)
    
    def _run_standalone(self, user_input: str, **kwargs) -> str:
        """
        单独模式：根据意图调用对应 Agent
        """
        intent = self._detect_intent(user_input)
        
        if intent == "create_plan":
            return self._handle_create_plan(user_input)
        elif intent == "ask_question":
            return self._handle_ask_question(user_input)
        elif intent == "start_quiz":
            return self._handle_start_quiz(user_input)
        elif intent == "get_report":
            return self._handle_get_report()
        else:
            # 默认当作问答处理
            return self._handle_ask_question(user_input)
    
    def _run_coordinated(self, user_input: str, **kwargs) -> str:
        """
        协调模式：自动执行完整流程
        
        流程：规划 → 学习 → 验证 → 总结
        """
        responses = []
        
        # 1. 规划阶段
        if self.state == OrchestratorState.IDLE:
            self.state = OrchestratorState.PLANNING
            responses.append("📋 **阶段 1: 生成学习计划**\n")
            plan_response = self._handle_create_plan(user_input)
            responses.append(plan_response)
            responses.append("\n---\n")
        
        # 2. 学习阶段
        if self.state == OrchestratorState.PLANNING:
            self.state = OrchestratorState.LEARNING
            responses.append("🎓 **阶段 2: 开始学习**\n")
            responses.append("学习计划已生成，你可以开始提问或开始测验。\n")
            responses.append("\n---\n")
        
        # 3. 验证阶段
        if self.state == OrchestratorState.LEARNING:
            self.state = OrchestratorState.VALIDATING
            responses.append("✅ **阶段 3: 知识验证**\n")
            quiz_response = self._handle_start_quiz(user_input)
            responses.append(quiz_response)
            responses.append("\n---\n")
        
        # 4. 完成
        self.state = OrchestratorState.COMPLETED
        responses.append("📊 **流程完成！**\n")
        responses.append("你可以查看进度报告，或继续学习。")
        
        return "\n".join(responses)
    
    def _detect_intent(self, user_input: str) -> str:
        """
        意图识别
        
        简化版：基于关键词匹配
        TODO: 可以用 LLM 进行更智能的意图识别
        """
        input_lower = user_input.lower()
        
        if any(kw in input_lower for kw in ["计划", "plan", "学习", "开始"]):
            return "create_plan"
        elif any(kw in input_lower for kw in ["测验", "quiz", "测试", "考试"]):
            return "start_quiz"
        elif any(kw in input_lower for kw in ["报告", "进度", "report", "progress"]):
            return "get_report"
        else:
            return "ask_question"
    
    def _handle_create_plan(self, user_input: str) -> str:
        """处理创建计划请求"""
        if not self.domain:
            self.set_domain(user_input[:50])  # 用输入的前 50 字符作为领域名
        
        plan = self.planner.run(user_input)
        
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
    
    def _handle_ask_question(self, user_input: str) -> str:
        """处理问答请求"""
        return self.tutor.run(user_input, mode=SessionMode.FREE)
    
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
