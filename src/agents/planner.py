"""
Planner Agent - 规划 Agent

职责：
1. 识别用户输入类型（领域描述/GitHub URL/PDF）
2. 调用相应的分析工具
3. 生成个性化学习计划

使用 ReAct 模式：Thought → Action → Observation → ... → Finish

TODO (Day 4):
- 实现完整的 ReAct 循环
- 集成 RepoAnalyzer 和 PDFAnalyzer
- 接入 LangSmith 追踪
"""

from typing import Optional, Dict, Any
import re

from .base import BaseAgent
from src.core.models import LearningPlan, LearningPhase, LearningGoal


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
        # 1. 识别输入类型
        input_type = self._detect_input_type(input_data)
        
        # 2. 根据类型处理
        if input_type == "github_url":
            # TODO: 调用 RepoAnalyzer
            domain = self._extract_domain_from_url(input_data)
            context = f"GitHub 项目: {input_data}"
        elif input_type == "pdf_content":
            # TODO: 调用 PDFAnalyzer
            domain = "PDF 文档"
            context = input_data[:2000]  # 截取前 2000 字符
        else:
            domain = input_data
            context = input_data
        
        # 3. 生成计划
        prompt = f"""请为以下学习内容制定学习计划：

**学习主题**: {domain}
**学习目标**: {goal}

**背景信息**:
{context}

请生成一个详细的学习计划，包括：
1. 前置知识要求
2. 学习阶段划分（3-5个阶段）
3. 每个阶段的具体知识点
4. 推荐资源

用 Markdown 格式输出。"""
        
        plan_text = self._call_llm(prompt)
        
        # 4. 解析为结构化对象（简化版，后续可改进）
        plan = self._parse_plan(domain, goal, plan_text)
        
        return plan
    
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
