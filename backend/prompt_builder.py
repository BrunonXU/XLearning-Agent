"""
PromptBuilder — 为每个 Studio 工具类型构建富上下文 prompt。

PromptBuilder 拥有 prompt 构建的全部所有权：
- 自己调 rag_engine.build_context() 做 RAG 检索
- 自己从 database.get_messages() 拿历史并截断
- 自己把 allDays 进度数据格式化注入
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from langsmith import traceable

from backend import database

logger = logging.getLogger(__name__)


@dataclass
class PromptTemplate:
    role_instruction: str       # system_prompt (role persona)
    generation_instruction: str # tool-specific generation instructions
    output_format: str          # output format instructions


def _find_day(all_days: list[dict], day_number: int | None) -> dict | None:
    """Find a day dict by dayNumber."""
    if day_number is None:
        return None
    for d in all_days:
        if d.get("dayNumber") == day_number:
            return d
    return None


# ---------------------------------------------------------------------------
# Prompt templates for all 7 tool types
# ---------------------------------------------------------------------------

_TEMPLATES: dict[str, PromptTemplate] = {
    "study-guide": PromptTemplate(
        role_instruction=(
            "你是一个学习策略顾问。分析学习者的背景、目标和材料，"
            "给出个性化的宏观学习路线图、知识体系结构和补充材料推荐。"
        ),
        generation_instruction=(
            "请基于以下材料和学习进度，生成一份宏观学习路线图。\n"
            "如果提供了学习者画像，必须根据学习者的目的、水平、可用时间来个性化定制内容：\n"
            "- 根据学习目的调整路线图的侧重方向\n"
            "- 根据当前水平调整内容深度和起点\n"
            "- 根据学习周期和每日可用时间调整节奏和范围\n"
            "重点包含：学习路线图、知识体系、补充材料推荐。\n"
            "定位为战略层面，回答「学什么、怎么学」，而非每日任务分解。\n"
            "对已完成的天数做简要回顾，对未完成的天数做详细展开。\n"
            "如果存在当前学习天数，重点覆盖当前天数对应主题的知识点。"
        ),
        output_format=(
            "请使用 Markdown 大纲格式输出，包含清晰的标题层级。\n"
            "必须包含以下关键词对应的章节：学习路线图、知识体系、补充材料推荐。"
        ),
    ),
    "learning-plan": PromptTemplate(
        role_instruction=(
            "你是一个学习计划生成器。根据学习者画像、材料和进度，"
            "生成按天拆分的个性化详细学习计划，每天包含具体任务、验证标准和知识点。"
        ),
        generation_instruction=(
            "请基于以下材料和学习进度，生成一份按天拆分的详细学习计划。\n"
            "如果提供了学习者画像，必须据此个性化定制：\n"
            "- 根据学习周期确定总天数\n"
            "- 根据每日可用时间确定每天任务量\n"
            "- 根据当前水平调整任务难度和前置知识铺垫\n"
            "- 根据学习目的确定重点模块和优先级\n"
            "如果已有学习规划（allDays），请基于剩余未完成内容重新规划。\n"
            "如果没有 RAG 材料内容，请生成通用学习计划并建议用户上传材料。\n"
            "每天包含具体任务、验证标准和知识点。"
        ),
        output_format=(
            "请严格输出 JSON 格式，结构如下：\n"
            '{"days": [{"dayNumber": 1, "title": "...", '
            '"tasks": [{"id": "t1", "type": "reading", "title": "..."}], '
            '"learningObjectives": "...", "methodology": "...", '
            '"verificationCriteria": "...", '
            '"knowledgePoints": ["...", "..."], '
            '"tomorrowPreview": "..."}]}\n'
            "不要输出 JSON 以外的任何内容。"
        ),
    ),
    "flashcards": PromptTemplate(
        role_instruction=(
            "你是一个闪卡生成器。基于学习材料和用户提过的问题，"
            "生成适合快速记忆/回忆的问答对。"
        ),
        generation_instruction=(
            "请基于以下材料和学习进度，生成 10-15 张闪卡（问答对）。\n"
            "优先为当前天数和最近已完成天数的主题生成闪卡。\n"
            "如果对话历史中有用户提过的问题，也将相关概念纳入闪卡。"
        ),
        output_format=(
            "每张卡片格式：\nQ: 问题\nA: 答案\n\n"
            "卡片之间用 --- 分隔。\n"
            "覆盖核心概念、定义、原理等关键知识点。"
        ),
    ),
    "quiz": PromptTemplate(
        role_instruction=(
            "你是一个考试出题专家。基于已学内容出正式测验题，"
            "包含多种题型、评分标准和错题解析。"
        ),
        generation_instruction=(
            "请基于以下材料和学习进度，生成一份正式测验。\n"
            "基于已完成天数的主题出题，覆盖已学知识点。\n"
            "如果所有天数均未完成，则基于材料整体内容生成基础测验。"
        ),
        output_format=(
            "请包含以下题型：单选题、多选题、判断题、简答题。\n"
            "每道题附上评分标准、正确答案和错题解析。\n"
            "用 Markdown 格式输出，题目编号清晰。"
        ),
    ),
    "progress-report": PromptTemplate(
        role_instruction=(
            "你是一个学习数据分析师。基于学习进度数据，"
            "输出结构化 JSON 分析报告，包含知识图谱、薄弱环节和下一步建议。"
        ),
        generation_instruction=(
            "请基于以下学习进度数据，进行纯数据分析。\n"
            "分析 allDays 的完成状态、各天主题覆盖情况。\n"
            "不需要参考学习材料，仅基于进度数据分析。"
        ),
        output_format=(
            "请严格输出 JSON 格式，结构如下：\n"
            '{"summary": {"completedDays": 0, "totalDays": 0, "percentage": 0}, '
            '"knowledgeGraph": [{"node": "...", "connections": ["..."]}], '
            '"timeline": [{"day": 1, "title": "...", "status": "...", "score": 0}], '
            '"weakPoints": ["..."], '
            '"nextSteps": ["..."]}\n'
            "不要输出 JSON 以外的任何内容。"
        ),
    ),
    "mind-map": PromptTemplate(
        role_instruction=(
            "你是一个知识结构化专家。将学习内容组织为 Markdown 标题层级结构，"
            "适合渲染为思维导图。"
        ),
        generation_instruction=(
            "请基于以下材料和学习进度，生成一份知识结构思维导图。\n"
            "按学习天数和主题组织知识层级。\n"
            "如果存在当前学习天数，重点展开当前天数对应主题。"
        ),
        output_format=(
            "请使用 Markdown 标题层级格式输出（#/##/###/-），适合 markmap.js 渲染。\n"
            "不要使用 JSON 格式。\n"
            "用标题层级表达知识的层次关系和从属关系。"
        ),
    ),
    "day-summary": PromptTemplate(
        role_instruction=(
            "你是一个学习总结专家。总结今日学习内容，"
            "分析与之前知识的关联，给出复习建议和明日预告。"
        ),
        generation_instruction=(
            "请基于以下学习进度和材料，总结当天的学习内容。\n"
            "包含当天学习的知识点回顾。\n"
            "分析当天知识与之前已完成天数知识的关联。\n"
            "给出复习建议和明日学习预告。"
        ),
        output_format=(
            "请使用 Markdown 格式输出，包含以下章节：\n"
            "## 知识回顾\n## 关联分析\n## 复习建议\n## 明日预告"
        ),
    ),
}


# ---------------------------------------------------------------------------
# PromptBuilder class
# ---------------------------------------------------------------------------

class PromptBuilder:
    """为每个 Studio 工具类型构建富上下文 prompt。

    PromptBuilder 拥有 prompt 构建的全部所有权：
    - 自己调 rag_engine.build_context() 做 RAG 检索
    - 自己从 database.get_messages() 拿历史并截断
    - 自己把 allDays 进度数据格式化注入
    """

    _templates = _TEMPLATES

    def __init__(self, rag_engine=None):
        self.rag_engine = rag_engine

    @traceable(name="prompt_builder.build")
    def build(self, content_type: str, learning_context) -> tuple[str, str]:
        """构建完整 prompt 和 system_prompt，可直接发给 LLM。

        Args:
            content_type: Tool type (e.g. "study-guide", "learning-plan").
            learning_context: Object with planId, allDays, currentDayNumber, learnerProfile attrs.

        Returns:
            (user_prompt, system_prompt) tuple.
        """
        template = self._templates[content_type]

        # Safely extract fields from learning_context (duck-typed)
        plan_id = getattr(learning_context, "planId", "") or ""
        all_days = getattr(learning_context, "allDays", None) or []
        current_day_number = getattr(learning_context, "currentDayNumber", None)
        learner_profile = getattr(learning_context, "learnerProfile", None)

        # 1. RAG retrieval with targeted query
        rag_context = self._retrieve_rag(content_type, learning_context)
        # 2. Truncated chat history (last 3 rounds)
        chat_history = self._get_truncated_history(plan_id)
        # 3. Formatted progress text
        progress_text = self._format_progress(all_days, current_day_number)
        # 4. Formatted learner profile
        profile_text = self._format_learner_profile(learner_profile)
        # 5. Assemble user_prompt (without role_instruction)
        user_prompt = self._assemble(template, rag_context, chat_history, progress_text, profile_text)
        
        # 6. role_instruction as system_prompt with current time
        from datetime import datetime
        now = datetime.now()
        weekdays = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
        time_str = f"{now.strftime('%Y年%m月%d日 %H:%M:%S')} {weekdays[now.weekday()]}"
        system_prompt = f"【系统提示：当前真实时间是 {time_str}】\n\n{template.role_instruction}"
        
        return (user_prompt, system_prompt)

    def _retrieve_rag(self, content_type: str, ctx) -> str:
        """根据工具类型构造针对性 RAG 查询词并检索。

        progress-report 不做 RAG 检索。
        """
        if not self.rag_engine or content_type == "progress-report":
            return ""
        query = self._build_rag_query(content_type, ctx)
        if not query:
            return ""
        try:
            return self.rag_engine.build_context(query, k=5)
        except Exception as e:
            logger.warning("[PromptBuilder] RAG retrieval failed: %s", e)
            return ""

    def _get_truncated_history(self, plan_id: str) -> list[dict]:
        """从数据库获取消息并截断到最近 3 轮（6 条）。"""
        if not plan_id:
            return []
        try:
            messages = database.get_messages(plan_id)
            return messages[-6:]
        except Exception as e:
            logger.warning("[PromptBuilder] Failed to get messages: %s", e)
            return []

    def _format_progress(self, all_days: list[dict], current_day_number: int | None) -> str:
        """将 allDays 格式化为可注入 prompt 的文本。"""
        if not all_days:
            return ""
        lines = []
        for day in all_days:
            day_num = day.get("dayNumber", "?")
            title = day.get("title", "未命名")
            completed = day.get("completed", False)
            status = "✅ 已完成" if completed else "⬜ 未完成"
            marker = " ← 当前" if day_num == current_day_number else ""
            lines.append(f"Day {day_num}: {title} [{status}]{marker}")

            # Include task details if available
            tasks = day.get("tasks", [])
            for task in tasks:
                task_title = task.get("title", "")
                task_done = "✅" if task.get("completed") else "⬜"
                if task_title:
                    lines.append(f"  - {task_done} {task_title}")

        return "\n".join(lines)

    def _assemble(
        self,
        template: PromptTemplate,
        rag_context: str,
        chat_history: list[dict],
        progress_text: str,
        profile_text: str = "",
    ) -> str:
        """Compose final user_prompt from sections separated by ---."""
        sections: list[str] = []

        # 0. Learner profile (highest priority context)
        if profile_text:
            sections.append(f"[学习者画像]\n{profile_text}")

        # 1. RAG context (skip for progress-report — already handled by empty rag_context)
        if rag_context:
            sections.append(f"[材料上下文：RAG 检索结果]\n{rag_context}")

        # 2. Learning progress
        if progress_text:
            sections.append(f"[学习进度上下文]\n{progress_text}")

        # 3. Chat history (last 3 rounds)
        if chat_history:
            history_lines = []
            for msg in chat_history:
                role = msg.get("role", "unknown")
                content = msg.get("content", "")
                history_lines.append(f"{role}: {content}")
            sections.append(f"[对话历史上下文：最近 3 轮]\n" + "\n".join(history_lines))

        # 4. Tool-specific generation instruction
        sections.append(f"[工具专属生成指令]\n{template.generation_instruction}")

        # 5. Output format instruction
        sections.append(f"[输出格式指令]\n{template.output_format}")

        return "\n---\n".join(sections)

    def _format_learner_profile(self, profile) -> str:
        """将学习者画像格式化为可注入 prompt 的文本。"""
        if not profile:
            return ""
        lines = []
        goal = getattr(profile, "goal", "") or ""
        duration = getattr(profile, "duration", "") or ""
        level = getattr(profile, "level", "") or ""
        background = getattr(profile, "background", "") or ""
        daily_hours = getattr(profile, "dailyHours", "") or getattr(profile, "daily_hours", "") or ""

        if goal:
            lines.append(f"学习目的：{goal}")
        if duration:
            lines.append(f"学习周期：{duration}")
        if level:
            lines.append(f"当前水平：{level}")
        if background:
            lines.append(f"个人背景：{background}")
        if daily_hours:
            lines.append(f"每日可用时间：{daily_hours}")

        return "\n".join(lines) if lines else ""

    def _build_rag_query(self, content_type: str, ctx) -> str:
        """根据工具类型和学习上下文构造 RAG 查询词。"""
        all_days = getattr(ctx, "allDays", None) or []
        current = getattr(ctx, "currentDayNumber", None)

        if content_type == "study-guide":
            titles = [d.get("title", "") for d in all_days if d.get("title")]
            return (" ".join(titles) + " 知识体系 学习路线") if titles else "学习指南 知识体系 学习路线"

        elif content_type == "learning-plan":
            titles = [d.get("title", "") for d in all_days if d.get("title")]
            return " ".join(titles) if titles else "学习计划 核心概念"

        elif content_type == "flashcards":
            topics: list[str] = []
            day = _find_day(all_days, current)
            if day and day.get("title"):
                topics.append(day["title"])
            completed = [d for d in all_days if d.get("completed")]
            for d in completed[-2:]:
                if d.get("title"):
                    topics.append(d["title"])
            return " ".join(topics) if topics else "闪卡 知识点"

        elif content_type == "quiz":
            completed = [d.get("title", "") for d in all_days if d.get("completed") and d.get("title")]
            return " ".join(completed) if completed else "测验 知识点"

        elif content_type == "mind-map":
            titles = [d.get("title", "") for d in all_days if d.get("title")]
            return (" ".join(titles) + " 知识结构 概念关系") if titles else "思维导图 知识结构"

        elif content_type == "day-summary":
            topics = []
            day = _find_day(all_days, current)
            if day and day.get("title"):
                topics.append(f"Day {current}: {day['title']}")
            completed = [d for d in all_days if d.get("completed")]
            for d in completed[-3:]:
                if d.get("title"):
                    topics.append(d["title"])
            return " ".join(topics) if topics else "知识总结"

        return ""
