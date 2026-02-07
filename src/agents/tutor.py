"""
Tutor Agent - 教学 Agent

职责：
1. Free 模式：自由对话，回答学习问题
2. Quiz 模式：进行测验互动
3. 集成 RAG 检索，基于用户资料回答

TODO (Day 5):
- 实现完整的对话管理
- 集成 RAG 检索
- 实现流式输出
"""

from typing import Optional, List, Dict, Any, Generator

from .base import BaseAgent
from src.core.models import SessionMode, Quiz, Question
from src.rag import RAGEngine


class TutorAgent(BaseAgent):
    """
    教学 Agent
    
    负责与用户互动学习
    """
    
    name = "TutorAgent"
    description = "互动教学，回答问题，进行测验"
    
    system_prompt = """你是一个专业的 AI 学习导师。

你的教学风格是：
- 耐心、友好、鼓励式教学
- 用简单易懂的语言解释复杂概念
- 善用类比和实例
- 循序渐进，由浅入深
- 鼓励学生思考，而不是直接给答案

当回答问题时：
1. 先确认理解学生的问题
2. 给出清晰的解释
3. 必要时提供示例
4. 检查学生是否理解
5. 鼓励提出更多问题

如果有相关的学习资料作为参考，请基于这些资料回答，并在适当时引用来源。"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.rag_engine: Optional[RAGEngine] = None
        self.current_mode = SessionMode.FREE
        self.current_quiz: Optional[Quiz] = None
        self.quiz_progress = 0
    
    def set_rag_engine(self, rag_engine: RAGEngine):
        """设置 RAG 引擎"""
        self.rag_engine = rag_engine
    
    def run(
        self,
        user_input: str,
        mode: SessionMode = SessionMode.FREE,
        history: Optional[List[Dict[str, str]]] = None,
        use_rag: bool = True,
        **kwargs
    ) -> str:
        """
        处理用户输入
        
        Args:
            user_input: 用户输入
            mode: 会话模式（FREE/QUIZ）
            history: 对话历史
            use_rag: 是否使用 RAG 检索
            
        Returns:
            回复内容
        """
        self.current_mode = mode
        
        if mode == SessionMode.QUIZ:
            return self._handle_quiz_mode(user_input)
        else:
            return self._handle_free_mode(user_input, history, use_rag)
    
    def _handle_free_mode(
        self,
        user_input: str,
        history: Optional[List[Dict[str, str]]] = None,
        use_rag: bool = True,
    ) -> str:
        """处理自由对话模式"""
        # 构建上下文
        context = ""
        if use_rag and self.rag_engine:
            self._emit_event("tool_start", self.name, f"Retrieving context for: {user_input[:50]}...")
            
            # --- 增强检索对于泛指词的命中 ---
            query = user_input
            if any(kw in user_input for kw in ["paper", "document", "this", "论文", "文档", "这"]):
                # 如果用户指代不明，尝试通过附加关键词扩大检索范围
                query += " summary introduction overview abstract"
            
            # 使用稍大的 k 值确保能检索到上下文
            context = self.rag_engine.build_context(query, k=5)
            
            self._emit_event("progress", self.name, f"Retrieved {len(context)//100 if context else 0} context chunks")
            self._emit_event("tool_end", self.name, "Context retrieval complete")
        
        # 构建 prompt
        if context:
            prompt = f"""参考以下学习资料回答问题：

{context}

---

学生问题：{user_input}

请基于以上资料回答，如果资料中没有相关信息，可以结合你的知识补充。"""
        else:
            prompt = f"学生问题：{user_input}"
        
        # 调用 LLM
        self._emit_event("progress", self.name, "Generating tutor response...")
        response = self._call_llm(prompt)
        self._emit_event("progress", self.name, "Response generated.")
        
        return response
    
    def _handle_quiz_mode(self, user_input: str) -> str:
        """处理测验模式"""
        if self.current_quiz is None:
            return "当前没有进行中的测验。请先开始一个新测验。"
        
        if self.quiz_progress >= len(self.current_quiz.questions):
            return "测验已完成！请查看测验结果。"
        
        # 获取当前题目
        current_question = self.current_quiz.questions[self.quiz_progress]
        
        # 检查答案
        is_correct = user_input.strip().upper() == current_question.correct_answer.strip().upper()
        
        # 构建反馈
        if is_correct:
            feedback = "✅ 回答正确！\n\n"
        else:
            feedback = f"❌ 回答错误。正确答案是：{current_question.correct_answer}\n\n"
        
        if current_question.explanation:
            feedback += f"💡 解析：{current_question.explanation}\n\n"
        
        # 进入下一题
        self.quiz_progress += 1
        
        if self.quiz_progress < len(self.current_quiz.questions):
            next_question = self.current_quiz.questions[self.quiz_progress]
            feedback += f"---\n\n**题目 {self.quiz_progress + 1}**: {next_question.question}\n\n"
            if next_question.options:
                for i, opt in enumerate(next_question.options):
                    feedback += f"{chr(65+i)}. {opt}\n"
        else:
            feedback += "🎉 测验完成！"
        
        return feedback
    
    def start_quiz(self, quiz: Quiz) -> str:
        """开始测验"""
        self.current_quiz = quiz
        self.quiz_progress = 0
        self.current_mode = SessionMode.QUIZ
        
        if not quiz.questions:
            return "测验题目为空。"
        
        # 返回第一题
        first_question = quiz.questions[0]
        response = f"📝 **开始测验：{quiz.topic}**\n\n"
        response += f"共 {len(quiz.questions)} 道题目\n\n"
        response += f"---\n\n**题目 1**: {first_question.question}\n\n"
        
        if first_question.options:
            for i, opt in enumerate(first_question.options):
                response += f"{chr(65+i)}. {opt}\n"
        
        return response
    
    def stream_response(
        self,
        user_input: str,
        history: Optional[List[Dict[str, str]]] = None,
        use_rag: bool = True,
    ) -> Generator[str, None, None]:
        """
        流式输出回复
        
        TODO: 实现流式输出
        """
        # 暂时用非流式实现
        response = self.run(user_input, history=history, use_rag=use_rag)
        yield response
    
    def answer(
        self,
        question: str,
        rag_engine: Optional[RAGEngine] = None,
        k: int = 3,
    ) -> str:
        """
        RAG 增强问答（便捷方法）
        
        这是 TutorAgent 最常用的方法，整合了 RAG 检索和 LLM 问答。
        
        Args:
            question: 用户问题
            rag_engine: RAG 引擎（可选，使用已设置的）
            k: 检索结果数量
            
        Returns:
            回答内容
            
        面试话术：
        > "answer() 是 TutorAgent 的核心方法。先从 RAG 检索相关内容，
        >  然后把内容注入 Prompt 让 LLM 回答。这样既能利用 LLM 推理，
        >  又能基于用户资料给出个性化回答。"
        
        使用示例：
            tutor = TutorAgent()
            tutor.set_rag_engine(rag_engine)
            answer = tutor.answer("什么是 Self-Attention?")
        """
        # 使用传入的或已设置的 RAG 引擎
        engine = rag_engine or self.rag_engine
        
        if engine:
            self.rag_engine = engine
        
        return self.run(question, use_rag=(engine is not None))

