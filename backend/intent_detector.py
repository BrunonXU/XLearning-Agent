"""
IntentDetector — 从聊天消息中检测 Studio 工具触发意图

通过关键词子串匹配检测用户是否想要重新生成某个 Studio 工具的内容。
"""

TRIGGER_KEYWORDS: dict[str, list[str]] = {
    "learning-plan": ["更新学习计划", "重新生成计划", "调整计划", "新计划"],
    "study-guide": ["更新学习指南", "重新生成指南", "刷新指南"],
    "flashcards": ["重新生成闪卡", "更新闪卡", "刷新闪卡", "新闪卡"],
    "quiz": ["重新生成测验", "刷新测验", "出新题", "再出一套题"],
    "mind-map": ["更新思维导图", "重新生成导图", "刷新导图"],
}


def detect_studio_trigger(message: str) -> tuple[bool, str | None]:
    """检测消息中是否包含 Studio 工具触发关键词。

    Returns:
        (是否触发, 工具类型) — 未触发时返回 (False, None)
    """
    for tool_type, keywords in TRIGGER_KEYWORDS.items():
        if any(kw in message for kw in keywords):
            return (True, tool_type)
    return (False, None)
