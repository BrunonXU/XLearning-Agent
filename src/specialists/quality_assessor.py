"""
QualityAssessor - LLM 质量评估器

使用 LLM 对提取的正文和评论进行内容质量评估，
单次调用同时生成评分、推荐理由、内容摘要、评论结论。

降级策略：
- 正文 < 50 字：直接使用原文作为摘要
- 正文提取失败：基于标题+描述+互动数据降级评估，推荐理由标注"正文未提取"
- LLM 调用失败：启发式降级（正文前 150 字、评论结论置空、互动数据估算评分）
"""

import json
import logging
import re
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple

from src.specialists.browser_models import RawSearchResult, ScoredResult

logger = logging.getLogger(__name__)


def _safe_num(v) -> float:
    """安全转换为数值。"""
    if v is None:
        return 0.0
    try:
        return float(v)
    except (ValueError, TypeError):
        return 0.0


@dataclass
class AssessmentResult:
    """LLM 质量评估结果"""
    quality_score: float = 0.0          # 1-10 分
    recommendation_reason: str = ""     # ≤50 字推荐理由
    content_summary: str = ""           # ≤150 字内容摘要
    comment_summary: str = ""           # ≤100 字评论结论摘要


class QualityAssessor:
    """LLM 质量评估器"""

    def __init__(self, llm_provider=None):
        """
        初始化 QualityAssessor。

        Args:
            llm_provider: LLM Provider 实例（具有 simple_chat 方法），
                          为 None 时所有评估走启发式降级。
        """
        self._llm = llm_provider

    # ------------------------------------------------------------------
    # 公开接口
    # ------------------------------------------------------------------

    async def assess_batch(
        self,
        items: List[Tuple[RawSearchResult, str, List[Dict]]],
    ) -> List[ScoredResult]:
        """
        批量评估：将多条结果打包为一个 prompt 进行单次 LLM 调用。

        Args:
            items: [(raw_result, extracted_content, top_comments), ...]
                   extracted_content 为提取的正文文本
                   top_comments 为高赞评论列表 [{text, likes, author}, ...]
        Returns:
            评估后的 ScoredResult 列表（含摘要、评论结论等扩展字段）
        """
        if not items:
            return []

        # 尝试 LLM 批量评估
        if self._llm is not None:
            try:
                prompt = self._build_batch_prompt(items)
                response = self._llm.simple_chat(
                    prompt,
                    system_prompt=(
                        "你是一个学习资源评估专家，服务于一个智能学习规划平台。"
                        "平台的用户是想学习某个领域知识的人，系统帮他们搜索高质量资源并制定学习规划。"
                        "你的任务是从学习者视角评估资源，提取对学习者真正有用的知识点和可操作建议。"
                        "忽略作者自我介绍、引流话术、关注点赞等无关内容。"
                        "严格按照指定的 JSON 格式输出。"
                    ),
                )
                results = self._parse_batch_response(response, items)
                if results is not None:
                    return results
            except Exception as e:
                logger.warning(f"LLM batch assessment failed: {e}")

        # LLM 失败 → 启发式降级
        return self._batch_heuristic_fallback(items)

    async def assess_single_fallback(
        self, raw: RawSearchResult
    ) -> ScoredResult:
        """
        降级评估：正文提取失败时，基于标题、描述和互动数据评估。
        推荐理由中标注"正文未提取"。
        """
        assessment = self._heuristic_fallback(raw)
        assessment.recommendation_reason = (
            f"正文未提取；{assessment.recommendation_reason}"
            if assessment.recommendation_reason
            else "正文未提取"
        )
        return ScoredResult(
            raw=raw,
            quality_score=assessment.quality_score,
            recommendation_reason=assessment.recommendation_reason,
            content_summary=assessment.content_summary,
            comment_summary=assessment.comment_summary,
            extracted_content="",
        )

    # ------------------------------------------------------------------
    # Prompt 构建
    # ------------------------------------------------------------------

    def _build_batch_prompt(
        self,
        items: List[Tuple[RawSearchResult, str, List[Dict]]],
    ) -> str:
        """
        构建批量评估 prompt。

        对于正文 < 50 字的条目，直接使用原文作为摘要，
        prompt 中仅要求生成评分、推荐理由和评论结论。
        """
        entries: List[str] = []
        for idx, (raw, content, comments) in enumerate(items):
            short_content = len(content) < 50
            comments_text = self._format_comments(comments)

            entry_lines = [
                f"### 条目 {idx + 1}",
                f"- 标题: {raw.title}",
                f"- 平台: {raw.platform}",
                f"- 描述: {raw.description[:200] if raw.description else '无'}",
            ]

            if short_content:
                entry_lines.append(f"- 正文（短文，直接作为摘要）: {content}")
                entry_lines.append("- 注意: 正文较短，无需生成 content_summary，将直接使用原文")
            else:
                entry_lines.append(f"- 正文（前 1500 字）: {content[:1500]}")

            entry_lines.append(f"- 评论区精选:\n{comments_text}")

            # 互动数据
            m = raw.engagement_metrics
            likes = m.get("likes", 0)
            collected = m.get("collected", 0)
            comments_count = m.get("comments_count", 0)
            entry_lines.append(f"- 互动数据: 点赞 {likes}, 收藏 {collected}, 评论 {comments_count}")

            entries.append("\n".join(entry_lines))

        items_block = "\n\n".join(entries)

        prompt = f"""请逐条评估以下 {len(items)} 条学习资源的质量，从学习者视角提取有用信息。

{items_block}

请严格按以下 JSON 格式输出，不要输出其他内容：
```json
[
  {{
    "quality_score": 7.5,
    "recommendation_reason": "推荐理由（≤50字，说明对学习者的价值）",
    "content_summary": "信息整理（≤400字）",
    "comment_summary": "评论结论摘要（≤100字，总结评论区对学习者有价值的观点）"
  }}
]
```

content_summary 要求（最重要的字段，在前端显示为"信息整理"）：
- 目标：让学习者不看原文就能知道"这篇资源能帮我学到什么"
- 完全忽略作者自我介绍、引流话术、"点赞关注"等废话，只提取知识干货
- 字数要求：尽量详细，最多400字，宁可多写也不要遗漏关键信息
- 格式要求：
  1. 第一行：一句话说明这篇资源的核心价值（对学习者来说）
  2. 后续用「→」分隔列出具体的知识点、学习路线、工具推荐、或可操作建议
  3. 如果提到了具体的项目/工具/链接，必须列出名称
- 不同类型资源的提取重点：
  - 学习路线/攻略类：提取完整路线步骤和推荐资源名称
  - 教程类：列出教的核心技术点和前置知识
  - 经验分享类：提取关键结论和可操作建议
  - 项目介绍类：列出技术栈、核心功能、适合什么水平的学习者
  - 论文/深度文章类：提取核心论点和方法论
- 示例（学习路线类）：「AI应用开发学习路线（面向校招） → 前提：扎实后端基本功 → 入门LLM：llm_interview_note前两章 → 实战项目：字节deer-flow + LangGraph框架 → 必学协议：MCP和AG-UI → RAG：rag-from-scratch开源项目 → 提示词工程：LangGPT → 微调：了解概念即可，推荐deeplearning.ai短课」
- 若条目标注"正文较短"则填空字符串

数组长度必须等于 {len(items)}，顺序与条目一一对应。
quality_score 范围 1-10，整数或一位小数。"""

        return prompt

    # ------------------------------------------------------------------
    # 响应解析
    # ------------------------------------------------------------------

    def _parse_batch_response(
        self,
        response: str,
        items: List[Tuple[RawSearchResult, str, List[Dict]]],
    ) -> Optional[List[ScoredResult]]:
        """解析 LLM 批量评估响应，返回 None 表示解析失败。"""
        try:
            clean = response.strip()
            if clean.startswith("```"):
                clean = re.sub(r"^```(?:json)?\s*", "", clean)
                clean = re.sub(r"\s*```$", "", clean)

            # 尝试提取 JSON 数组
            arr_match = re.search(r"\[[\s\S]*\]", clean)
            if arr_match:
                data = json.loads(arr_match.group())
            else:
                data = json.loads(clean)

            if not isinstance(data, list) or len(data) != len(items):
                logger.warning(
                    f"LLM response array length mismatch: "
                    f"expected {len(items)}, got {len(data) if isinstance(data, list) else 'non-list'}"
                )
                return None

            results: List[ScoredResult] = []
            for idx, (raw, content, _comments) in enumerate(items):
                entry = data[idx] if isinstance(data[idx], dict) else {}
                score = max(1.0, min(10.0, float(entry.get("quality_score", 5.0))))
                reason = str(entry.get("recommendation_reason", ""))[:50]

                # 短正文：直接使用原文作为摘要
                if len(content) < 50:
                    summary = content
                else:
                    summary = str(entry.get("content_summary", ""))[:400]

                comment_summary = str(entry.get("comment_summary", ""))[:100]

                results.append(ScoredResult(
                    raw=raw,
                    quality_score=score,
                    recommendation_reason=reason,
                    content_summary=summary,
                    comment_summary=comment_summary,
                    extracted_content=content,
                ))

            return results

        except (json.JSONDecodeError, ValueError, TypeError) as e:
            logger.warning(f"Failed to parse LLM batch response: {e}")
            return None

    # ------------------------------------------------------------------
    # 降级策略
    # ------------------------------------------------------------------

    def _heuristic_fallback(self, raw: RawSearchResult) -> AssessmentResult:
        """
        LLM 调用失败时的启发式降级：
        - 内容摘要 = 正文前 150 字（取 content_snippet 或 description）
        - 评论结论 = 空
        - 质量评分 = 基于互动数据估算
        """
        # 内容摘要：取可用文本的前 150 字
        text = raw.content_snippet or raw.description or ""
        content_summary = text[:150]

        # 互动数据估算评分 (1-10)
        quality_score = self._estimate_score_from_engagement(raw)

        # 推荐理由
        reason = self._build_fallback_reason(raw)

        return AssessmentResult(
            quality_score=quality_score,
            recommendation_reason=reason,
            content_summary=content_summary,
            comment_summary="",
        )

    def _batch_heuristic_fallback(
        self,
        items: List[Tuple[RawSearchResult, str, List[Dict]]],
    ) -> List[ScoredResult]:
        """批量启发式降级。"""
        results: List[ScoredResult] = []
        for raw, content, _comments in items:
            # 内容摘要：优先使用提取的正文
            if len(content) < 50:
                summary = content
            else:
                summary = content[:150]

            score = self._estimate_score_from_engagement(raw)
            reason = self._build_fallback_reason(raw)

            results.append(ScoredResult(
                raw=raw,
                quality_score=score,
                recommendation_reason=reason,
                content_summary=summary,
                comment_summary="",
                extracted_content=content,
            ))
        return results

    # ------------------------------------------------------------------
    # 辅助方法
    # ------------------------------------------------------------------

    def _estimate_score_from_engagement(self, raw: RawSearchResult) -> float:
        """基于互动数据估算质量评分 (1-10)。"""
        m = raw.engagement_metrics
        likes = _safe_num(m.get("likes", 0))
        collected = _safe_num(m.get("collected", 0))
        comments_count = _safe_num(m.get("comments_count", 0))

        # 加权互动分
        engagement = comments_count * 3 + collected * 2 + likes
        # sigmoid 映射到 1-10
        if engagement > 0:
            score = 1 + 9 * (engagement / (engagement + 500))
        else:
            score = 1.0

        return round(min(10.0, max(1.0, score)), 1)

    def _build_fallback_reason(self, raw: RawSearchResult) -> str:
        """构建降级推荐理由。"""
        m = raw.engagement_metrics
        parts: List[str] = []
        likes = _safe_num(m.get("likes", 0))
        collected = _safe_num(m.get("collected", 0))
        comments_count = _safe_num(m.get("comments_count", 0))

        if likes or collected or comments_count:
            parts.append(f"👍{int(likes)} ⭐{int(collected)} 💬{int(comments_count)}")

        if raw.content_snippet:
            parts.append("有内容摘要")

        return "；".join(parts) if parts else "数据不足"

    @staticmethod
    def _format_comments(comments: List[Dict]) -> str:
        """格式化评论列表为文本。"""
        if not comments:
            return "  无评论数据"
        lines: List[str] = []
        for c in comments[:10]:
            text = c.get("text", "")
            c_likes = c.get("likes", 0)
            author = c.get("author", "匿名")
            lines.append(f"  [{c_likes}赞] {author}: {text[:100]}")
        return "\n".join(lines)
