"""
Planner Agent - 规划 Agent

职责：
1. 识别用户输入类型（领域描述/GitHub URL/PDF）
2. 调用相应的分析工具
3. 生成个性化学习计划

使用 ReAct 模式：Thought → Action → Observation → ... → Finish

设计亮点：
1. 输入类型自动识别 - URL/PDF/文本
2. 集成 RepoAnalyzer 和 PDFAnalyzer
3. 结构化输出 LearningPlan

面试话术：
> "PlannerAgent 能自动识别输入类型。如果是 GitHub URL，
>  调用 RepoAnalyzer 分析仓库结构；如果是 PDF，用 PDFAnalyzer 提取内容。
>  然后用 LLM 生成结构化的学习计划。"
"""

from typing import Optional, Dict, Any
import re

from .base import BaseAgent
from src.core.models import LearningPlan, LearningPhase, LearningGoal
from src.specialists.repo_analyzer import RepoAnalyzer
from src.specialists.pdf_analyzer import PDFAnalyzer, PDFContent


class PlannerAgent(BaseAgent):
    """
    规划 Agent
    
    负责分析用户输入并生成学习计划
    """
    
    name = "PlannerAgent"
    description = "分析学习资料，生成个性化学习计划"
    
    system_prompt = """你是一个专业的学习规划师。

你的任务是：
1. 分析用户想要学习的内容
2. 评估内容的复杂度和前置知识要求
3. 制定一个结构化的学习计划

学习计划应该包括：
- 清晰的学习目标
- 分阶段的学习路径
- 每个阶段的具体知识点
- 预计学习时长
- 推荐的学习资源

请用 Markdown 格式输出学习计划。"""
    
    def run(
        self,
        input_data: str,
        goal: str = "能熟练使用",
        **kwargs
    ) -> LearningPlan:
        """
        生成学习计划
        
        Args:
            input_data: 用户输入（领域描述、GitHub URL 或 PDF 内容）
            goal: 学习目标
            
        Returns:
            LearningPlan 对象
        """
        self._emit_event("tool_start", self.name, f"Detecting input type for: {input_data[:50]}...")
        
        # 1. 识别输入类型
        input_type = self._detect_input_type(input_data)
        self._emit_event("progress", self.name, f"Input detected as: {input_type}")
        
        # 2. 根据类型处理
        if input_type == "github_url":
            self._emit_event("progress", self.name, "Analyzing GitHub repository...")
            domain, context = self._process_github_url(input_data)
        elif input_type == "pdf_content":
            self._emit_event("progress", self.name, "Processing PDF content...")
            domain, context = self._process_pdf_content(input_data)
        else:
            domain = input_data
            context = input_data
            self._emit_event("progress", self.name, "Processing text description...")
        
        # 3. 生成计划
        prompt = f"""请为以下学习内容制定学习计划：

**学习主题**: {domain}
**学习目标**: {goal}

**背景信息**:
{context[:3000]}

请生成一个详细的学习计划，包括：
1. 前置知识要求
2. 学习阶段划分（3-5个阶段）
3. 每个阶段的具体知识点
4. 推荐资源

用 Markdown 格式输出。"""
        
        self._emit_event("progress", self.name, "Generating structured learning plan via LLM...")
        plan_text = self._call_llm(prompt)
        
        # 4. 解析为结构化对象
        plan = self._parse_plan(domain, goal, plan_text)
        
        # 5. 保存原始 Markdown 到 plan 对象（用于展示）
        plan.raw_markdown = plan_text
        
        self._emit_event("tool_end", self.name, f"Plan generated for {domain}")
        return plan
    
    def _process_github_url(self, url: str) -> tuple:
        """
        处理 GitHub URL
        
        面试话术：
        > "遇到 GitHub URL，我先用 RepoAnalyzer 获取仓库信息，
        >  包括 README、项目结构等，作为生成学习计划的上下文。"
        """
        try:
            analyzer = RepoAnalyzer()
            repo_info = analyzer.analyze(url)
            
            domain = repo_info.get("name", self._extract_domain_from_url(url))
            
            # 构建上下文
            context_parts = [
                f"项目名称: {repo_info.get('name', 'Unknown')}",
                f"描述: {repo_info.get('description', '无描述')}",
                f"主要语言: {repo_info.get('language', '未知')}",
            ]
            
            if repo_info.get("readme"):
                context_parts.append(f"\nREADME 内容:\n{repo_info['readme'][:2000]}")
            
            context = "\n".join(context_parts)
            
        except Exception as e:
            # 降级处理
            domain = self._extract_domain_from_url(url)
            context = f"GitHub 项目: {url}\n(无法获取详细信息: {str(e)})"
        
        return domain, context
    
    def _process_pdf_content(self, content: str) -> tuple:
        """
        处理 PDF 内容
        
        注意：这里接收的是已经提取的文本内容
        如果是 bytes，应该先用 PDFAnalyzer.analyze_from_bytes()
        """
        # 尝试从内容中提取标题
        lines = content.strip().split("\n")
        title = lines[0][:50] if lines else "PDF 文档"
        
        # 截取内容作为上下文
        context = content[:3000]
        
        return title, context
    
    def _detect_input_type(self, input_data: str) -> str:
        """检测输入类型"""
        if re.match(r'https?://github\.com/', input_data):
            return "github_url"
        elif len(input_data) > 1000:
            return "pdf_content"
        else:
            return "domain_description"
    
    def _extract_domain_from_url(self, url: str) -> str:
        """从 GitHub URL 提取项目名"""
        match = re.search(r'github\.com/[\w-]+/([\w-]+)', url)
        if match:
            return match.group(1)
        return "Unknown Project"
    
    def _parse_plan(self, domain: str, goal: str, plan_text: str) -> LearningPlan:
        """
        解析 LLM 输出为结构化 LearningPlan
        
        这是简化版实现，后续可以用更复杂的解析逻辑
        """
        # 简单地创建一个基础计划结构
        # 实际应用中应该解析 plan_text
        return LearningPlan(
            domain=domain,
            goal=goal,
            goal_level=LearningGoal.USE,
            duration="2 周",
            phases=[
                LearningPhase(
                    name="基础概念",
                    duration="3 天",
                    topics=["核心概念", "基础语法", "基本使用"],
                ),
                LearningPhase(
                    name="进阶学习",
                    duration="4 天",
                    topics=["高级特性", "最佳实践", "常见模式"],
                ),
                LearningPhase(
                    name="实战应用",
                    duration="4 天",
                    topics=["项目实践", "问题解决", "性能优化"],
                ),
                LearningPhase(
                    name="总结巩固",
                    duration="3 天",
                    topics=["知识回顾", "查漏补缺", "项目展示"],
                ),
            ],
            prerequisites=["基础编程知识"],
        )
