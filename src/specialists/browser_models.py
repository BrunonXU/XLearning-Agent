"""
浏览器 Agent 内部数据模型

仅在浏览器搜索模块内部使用，不暴露给外部调用者。
"""

from typing import Dict, Any, List
from pydantic import BaseModel, Field


class RawSearchResult(BaseModel):
    """浏览器采集的原始搜索结果"""
    title: str
    url: str
    platform: str
    resource_type: str
    description: str = ""
    engagement_metrics: Dict[str, Any] = Field(default_factory=dict)
    comments: List[str] = Field(default_factory=list)
    content_snippet: str = ""
    top_comments: List[Dict[str, Any]] = Field(default_factory=list)  # 高赞评论 [{text, likes, author}]
    image_urls: List[str] = Field(default_factory=list)  # 笔记图片 URL 列表
    deduplicated_comment_count: int = 0  # 去重后的评论数量，用于替代 API 返回的原始 comments_count 参与互动分计算


class ResourceDetail(BaseModel):
    """详情页提取的数据"""
    content_snippet: str = ""
    likes: int = 0
    favorites: int = 0
    comments_count: int = 0
    comments: List[str] = Field(default_factory=list)
    top_comments: List[Dict[str, Any]] = Field(default_factory=list)  # 高赞评论 [{text, likes, author}]
    extra_metrics: Dict[str, Any] = Field(default_factory=dict)
    image_urls: List[str] = Field(default_factory=list)  # 笔记图片 URL 列表
    image_descriptions: List[str] = Field(default_factory=list)  # [TODO] 多模态 LLM 图片内容描述


class ScoredResult(BaseModel):
    """带评分的搜索结果"""
    raw: RawSearchResult
    quality_score: float = 0.0
    recommendation_reason: str = ""
    # 新增字段：AI 摘要与提取内容
    content_summary: str = ""         # AI 内容摘要（≤150 字）
    comment_summary: str = ""         # 评论结论摘要（≤100 字）
    extracted_content: str = ""       # 提取的正文内容（用于缓存）
    # 结构化知识提取
    key_points: List[str] = Field(default_factory=list)       # 核心观点（3-5 条）
    key_facts: List[str] = Field(default_factory=list)        # 关键数据/事实
    methodology: List[str] = Field(default_factory=list)      # 方法论/步骤
    # 可信度子维度评估（各 0-10）
    credibility: Dict[str, Any] = Field(default_factory=dict)
    # 格式: { timeliness: 8, authority: 7, accuracy: 9, objectivity: 6,
    #          timeliness_note: "...", authority_note: "...", accuracy_note: "...", objectivity_note: "..." }

