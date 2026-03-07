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
            "你是一位资深学习策略顾问。你的职责是分析学习者的背景、目标、已有材料和学习困惑，"
            "制定个性化的宏观学习路线图。你擅长构建知识体系、识别学习瓶颈、推荐高质量学习资源。\n"
            "你的输出是战略层面的指导——回答「学什么、按什么顺序学、怎么判断学会了」，"
            "而不是每日任务分解（那是学习计划的职责）。"
        ),
        generation_instruction=(
            # 基础指令，会被 _build_study_guide_instruction() 动态替换
            "请基于以下上下文，生成一份个性化的宏观学习路线图。"
        ),
        output_format=(
            "请使用 Markdown 大纲格式输出，包含清晰的标题层级。\n"
            "必须包含以下章节：学习路线图（分阶段，每阶段含里程碑）、知识体系、补充资源推荐。\n"
            "如果从对话历史中发现了用户的困惑点，在相关知识点旁用 ⚠️ 标注。\n"
            "不要输出 JSON 格式。"
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
        # 5a. Episodic Memory 摘要（从 DB 读取最新摘要）
        episodic_summary = ""
        if plan_id:
            try:
                from backend import database as _db
                latest_summary = _db.get_latest_conversation_summary(plan_id)
                if latest_summary:
                    text = latest_summary.get("summaryText", "")
                    if len(text) > 1000:
                        text = text[:1000] + "（摘要已截断）"
                    episodic_summary = text
            except Exception:
                pass  # 摘要获取失败不影响 Studio 生成

        user_prompt = self._assemble(
            template, rag_context, chat_history, progress_text, profile_text,
            content_type=content_type,
            all_days=all_days,
            current_day_number=current_day_number,
            episodic_summary=episodic_summary,
        )
        
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
        content_type: str = "",
        all_days: list[dict] | None = None,
        current_day_number: int | None = None,
        episodic_summary: str = "",
    ) -> str:
        """Compose final user_prompt from sections separated by ---."""
        sections: list[str] = []

        # 0. Learner profile (highest priority context)
        if profile_text:
            sections.append(f"[学习者画像]\n{profile_text}")

        # 0.5 Episodic Memory 摘要（画像之后、材料之前）
        if episodic_summary:
            sections.append(f"[对话记忆摘要]\n{episodic_summary}")

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

        # 4. Tool-specific generation instruction（study-guide 用动态拼接）
        if content_type == "study-guide":
            dynamic_instruction = self._build_study_guide_instruction(
                all_days=all_days or [],
                rag_context=rag_context,
                profile_text=profile_text,
                chat_history=chat_history,
                current_day_number=current_day_number,
            )
            sections.append(f"[工具专属生成指令]\n{dynamic_instruction}")
        else:
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

    def _build_study_guide_instruction(
        self,
        all_days: list[dict],
        rag_context: str,
        profile_text: str,
        chat_history: list[dict],
        current_day_number: int | None,
    ) -> str:
        """动态拼接 study-guide 的 generation_instruction。

        根据上下文丰富程度（材料/画像/进度）拼出明确的场景指令，
        LLM 不需要自己做条件判断。
        """
        parts: list[str] = []

        parts.append("请基于以下上下文，生成一份个性化的宏观学习路线图。")

        # --- 核心原则 ---
        parts.append("\n## 核心原则\n")

        # 材料角色
        if rag_context:
            parts.append(
                "1. **材料为骨架**：路线图必须围绕提供的学习材料展开，"
                "材料覆盖的知识点是学习范围的核心。不要脱离材料自由发挥无关内容。"
            )
        else:
            parts.append(
                "1. **无材料模式**：当前没有学习材料，请基于学习者画像或对话主题"
                "生成通用路线图。在开头明确提示「建议上传学习材料以获得更精准的路线图」。"
            )

        # 聊天历史角色
        principle_num = 2
        if chat_history:
            parts.append(
                f"{principle_num}. **聊天历史为线索**：从对话历史中提取用户提过的问题、困惑点、"
                "感兴趣的方向，在路线图相关知识点旁用 ⚠️ 标注，并给出针对性建议。"
            )
            principle_num += 1

        # 画像角色
        if profile_text:
            parts.append(
                f"{principle_num}. **画像为约束**：根据学习者的目的、水平、"
                "可用时间调整路线图的深度、广度和节奏。"
            )
        else:
            parts.append(
                f"{principle_num}. **无画像模式**：当前没有学习者画像，"
                "生成通用深度的路线图。在开头提示「建议填写学习者画像"
                "（学习目的、当前水平、可用时间）以获得个性化定制」。"
            )

        # --- 场景判断（Python 层已判断，直接给 LLM 明确指令）---
        completed_days = [d for d in all_days if d.get("completed")]
        total_days = len(all_days)

        if total_days > 0 and len(completed_days) > 0:
            parts.append(
                f"\n## 当前场景：迭代更新（已完成 {len(completed_days)}/{total_days} 天）\n"
                "这是一次路线图更新，不是从零开始。\n"
                "- 对已完成内容做简要回顾和掌握度评估\n"
                "- 重点展开未完成部分\n"
                "- 根据学习过程中暴露的问题调整后续路线"
            )
        else:
            parts.append(
                "\n## 当前场景：首次生成\n"
                "生成完整的从零开始路线图。"
            )

        # 当前天数重点
        if current_day_number is not None:
            current_day = _find_day(all_days, current_day_number)
            if current_day and current_day.get("title"):
                parts.append(
                    f"\n当前学习进度在 Day {current_day_number}：{current_day['title']}，"
                    "请重点覆盖该主题相关的知识点。"
                )

        # --- 路线图结构要求 ---
        parts.append(
            "\n## 路线图结构要求\n"
            "路线图必须包含以下阶段（根据材料内容调整具体名称）：\n"
            "- **入门基础**：前置知识和核心概念入门\n"
            "- **核心深入**：材料的主体内容，系统性掌握\n"
            "- **进阶应用**：综合运用、项目实践或高级主题\n"
            "每个阶段必须有一个**里程碑**：明确描述「学完这个阶段后，你应该能做到什么」。"
        )

        # --- 补充资源推荐 ---
        parts.append(
            "\n## 补充资源推荐\n"
            "在路线图末尾推荐 3-5 个高质量学习资源，优先推荐：\n"
            "- 官方文档（如 Python 官方教程、React 官方文档）\n"
            "- 经典书籍（如《CSAPP》《SICP》《设计模式》等领域公认经典）\n"
            "- 知名系统性教程（如 freeCodeCamp、MIT OCW、Coursera 热门课程）\n"
            "- 权威技术博客或系列文章（如 MDN Web Docs、Real Python）\n"
            "只推荐你确信真实存在的资源，不要编造链接或虚构书名。"
        )

        return "\n".join(parts)

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

    def _build_study_guide_instruction(
        self,
        all_days: list[dict],
        rag_context: str,
        profile_text: str,
        chat_history: list[dict],
        current_day_number: int | None,
    ) -> str:
        """动态拼接 study-guide 的 generation_instruction。

        根据上下文丰富程度（材料/画像/进度）拼出明确的场景指令，
        LLM 不需要自己做条件判断。
        """
        parts: list[str] = []

        parts.append("请基于以下上下文，生成一份个性化的宏观学习路线图。")

        # --- 核心原则 ---
        parts.append("\n## 核心原则\n")

        # 材料角色
        if rag_context:
            parts.append(
                "1. **材料为骨架**：路线图必须围绕提供的学习材料展开，"
                "材料覆盖的知识点是学习范围的核心。不要脱离材料自由发挥无关内容。"
            )
        else:
            parts.append(
                "1. **无材料模式**：当前没有学习材料，请基于学习者画像或对话主题"
                "生成通用路线图。在开头明确提示「建议上传学习材料以获得更精准的路线图」。"
            )

        # 聊天历史角色
        if chat_history:
            parts.append(
                "2. **聊天历史为线索**：从对话历史中提取用户提过的问题、困惑点、"
                "感兴趣的方向，在路线图相关知识点旁用 ⚠️ 标注，并给出针对性建议。"
            )

        # 画像角色
        if profile_text:
            parts.append(
                f"{'3' if chat_history else '2'}. **画像为约束**：根据学习者的目的、水平、"
                "可用时间调整路线图的深度、广度和节奏。"
            )
        else:
            parts.append(
                f"{'3' if chat_history else '2'}. **无画像模式**：当前没有学习者画像，"
                "生成通用深度的路线图。在开头提示「建议填写学习者画像"
                "（学习目的、当前水平、可用时间）以获得个性化定制」。"
            )

        # --- 场景判断（Python 层已判断，直接给 LLM 明确指令）---
        completed_days = [d for d in all_days if d.get("completed")]
        total_days = len(all_days)

        if total_days > 0 and len(completed_days) > 0:
            # 迭代更新模式
            parts.append(
                f"\n## 当前场景：迭代更新（已完成 {len(completed_days)}/{total_days} 天）\n"
                "这是一次路线图更新，不是从零开始。\n"
                "- 对已完成内容做简要回顾和掌握度评估\n"
                "- 重点展开未完成部分\n"
                "- 根据学习过程中暴露的问题调整后续路线"
            )
        else:
            # 首次生成模式
            parts.append(
                "\n## 当前场景：首次生成\n"
                "生成完整的从零开始路线图。"
            )

        # 当前天数重点
        if current_day_number is not None:
            current_day = _find_day(all_days, current_day_number)
            if current_day and current_day.get("title"):
                parts.append(
                    f"\n当前学习进度在 Day {current_day_number}：{current_day['title']}，"
                    "请重点覆盖该主题相关的知识点。"
                )

        # --- 路线图结构要求 ---
        parts.append(
            "\n## 路线图结构要求\n"
            "路线图必须包含以下阶段（根据材料内容调整具体名称）：\n"
            "- **入门基础**：前置知识和核心概念入门\n"
            "- **核心深入**：材料的主体内容，系统性掌握\n"
            "- **进阶应用**：综合运用、项目实践或高级主题\n"
            "每个阶段必须有一个**里程碑**：明确描述「学完这个阶段后，你应该能做到什么」。"
        )

        # --- 补充资源推荐 ---
        parts.append(
            "\n## 补充资源推荐\n"
            "在路线图末尾推荐 3-5 个高质量学习资源，优先推荐：\n"
            "- 官方文档（如 Python 官方教程、React 官方文档）\n"
            "- 经典书籍（如《CSAPP》《SICP》《设计模式》等领域公认经典）\n"
            "- 知名系统性教程（如 freeCodeCamp、MIT OCW、Coursera 热门课程）\n"
            "- 权威技术博客或系列文章（如 MDN Web Docs、Real Python）\n"
            "只推荐你确信真实存在的资源，不要编造链接或虚构书名。"
        )

        return "\n".join(parts)


