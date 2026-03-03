# Design Document

## Overview

本设计文档描述搜索模块重构的技术方案，覆盖 9 个需求：清理死代码、统一意图检测、简化调用链路、保持功能完整性、清理导入、平台选择器 UI、弹性搜索量策略、统一排名策略、新增 B站支持。

核心设计原则：
- 单一职责：搜索触发只在 Orchestrator，搜索执行只在 SearchOrchestrator
- 配置驱动：平台配置、搜索量、排名权重均通过配置管理
- 向后兼容：`search(query, platforms)` 接口签名不变

## Architecture

### 重构后的调用链路

```
用户输入 + 平台选择
    ↓
Orchestrator（意图识别 → search_resource）
    ↓ 直接调用，不经 TutorAgent
ResourceSearcher.search(query, platforms, search_depth)
    ↓
SearchOrchestrator.search_all_platforms(query, platforms, per_platform_limit, top_k)
    ↓ 并发
┌─────────────────────────────────────────────────┐
│ BrowserAgent (小红书: Playwright + API 拦截)     │
│ BiliBiliSearcher (B站: httpx API 直连)          │
│ BrowserAgent (YouTube: Playwright CSS 提取)      │
│ BrowserAgent (Google: Playwright CSS 提取)       │
└─────────────────────────────────────────────────┘
    ↓ 汇入 Candidate_Pool
QualityScorer（各平台独立评分 → 归一化 → 统一排序）
    ↓
top 10 → SearchResult[] → Orchestrator → TutorAgent 生成回复
```

### 文件变更清单

| 文件 | 变更类型 | 说明 |
|------|---------|------|
| `src/specialists/resource_searcher.py` | 重写 | 删除 Old_ResourceSearcher，BrowserResourceSearcher 重命名为 ResourceSearcher，新增 search_depth 参数 |
| `src/specialists/search_orchestrator.py` | 修改 | 新增 per_platform_limit 参数，弹性搜索量逻辑 |
| `src/specialists/quality_scorer.py` | 修改 | 新增各平台独立评分策略 + 归一化 |
| `src/specialists/platform_configs.py` | 修改 | 新增 bilibili 配置，新增 platform_category 和 scoring_weights 字段 |
| `src/specialists/bilibili_searcher.py` | 新增 | B站 API 搜索实现 |
| `src/specialists/browser_models.py` | 修改 | RawSearchResult 新增 deduplicated_comment_count 字段 |
| `src/agents/orchestrator.py` | 修改 | 简化搜索路由，直接调 ResourceSearcher，接收 platforms 参数 |
| `src/agents/tutor.py` | 修改 | 移除 _try_resource_search，新增接收外部搜索结果的方法 |
| `src/core/search_keywords.py` | 新增 | 统一的搜索关键词列表 |
| `src/ui/renderer.py` | 修改 | _render_chat_input 新增平台选择器 |
| `src/ui/layout.py` | 修改 | render_home_view 新增平台选择器 |

## Components

### 1. 统一搜索关键词模块 (`src/core/search_keywords.py`)

新增文件，集中维护搜索意图关键词：

```python
# src/core/search_keywords.py
SEARCH_KEYWORDS: list[str] = [
    "搜索资源", "找资源", "推荐资源", "search resource",
    "搜索更多资源", "找学习资源", "推荐学习资源",
    "有什么资源", "资源推荐", "有哪些资源", "学习资源",
    "find resource", "recommend", "搜索更多",
]

def is_search_intent(user_input: str) -> bool:
    """检测用户输入是否包含搜索意图关键词。"""
    input_lower = user_input.lower()
    return any(kw in input_lower for kw in SEARCH_KEYWORDS)
```

Orchestrator 和 TutorAgent 均引用此模块，不再各自维护关键词列表。

### 2. 平台配置扩展 (`src/specialists/platform_configs.py`)

扩展 PlatformConfig，新增分类和评分权重：

```python
@dataclass
class PlatformConfig:
    # ... 现有字段 ...
    platform_category: str = "article"  # "note" | "article" | "video"
    scoring_weights: Dict[str, float] = field(default_factory=dict)
    # 例如小红书: {"comments": 5, "collected": 2, "likes": 1}
    # B站: {"views": 1, "danmaku": 3, "collected": 2, "likes": 1}
    use_api_search: bool = False  # True 表示用 API 而非浏览器
    default_search_count: int = 10  # 默认搜索条数
    focused_search_count: int = 60  # 聚焦搜索条数
```

新增 bilibili 配置：

```python
_bilibili_config = PlatformConfig(
    name="bilibili",
    search_url_template="https://search.bilibili.com/all?keyword={query}",
    result_selector="",  # 不使用 CSS 提取
    title_selector="",
    link_selector="",
    description_selector="",
    resource_type="video",
    detail_selectors=DetailSelectors(),
    use_api_search=True,  # 使用 API
    platform_category="video",
    scoring_weights={"views": 1, "danmaku": 3, "collected": 2, "likes": 1},
    default_search_count=10,
    focused_search_count=60,
)
```

更新 PLATFORM_CONFIGS 字典，新增 bilibili，移除 stackoverflow（不在用户要求的 4 平台中，但保留配置以备扩展）。

### 3. B站搜索器 (`src/specialists/bilibili_searcher.py`)

独立模块，使用 httpx 调用 B站搜索 API：

```python
class BiliBiliSearcher:
    """B站视频搜索（httpx API 直连）"""
    
    API_URL = "https://api.bilibili.com/x/web-interface/search/type"
    TIMEOUT = 8  # 秒
    
    async def search(self, query: str, limit: int = 10) -> List[RawSearchResult]:
        """搜索 B站视频，返回 RawSearchResult 列表。"""
        # 调用 API，提取 title, bvid, play, danmaku, favorites, like
        # 失败时返回降级搜索链接
```

### 4. 弹性搜索量逻辑 (`SearchOrchestrator`)

修改 `search_all_platforms` 方法签名：

```python
async def search_all_platforms(
    self,
    query: str,
    platforms: List[str],
    per_platform_limit: Optional[int] = None,  # 新增：每平台搜索条数
    top_k: int = 10,
) -> List[SearchResult]:
```

搜索量计算逻辑：

```python
def _calculate_per_platform_limit(
    self, platforms: List[str], user_selected: bool
) -> int:
    """计算每平台搜索条数。
    
    - 未选平台（默认全搜）：每平台 10 条
    - 选了 1 个平台：该平台 60 条
    - 选了多个平台：40 条均分
    """
    if not user_selected:
        return 10
    if len(platforms) == 1:
        return 60
    return max(10, 40 // len(platforms))
```

### 5. 统一排名策略 (`QualityScorer`)

新增各平台独立评分方法和归一化：

```python
class QualityScorer:
    def _platform_score(self, result: RawSearchResult) -> float:
        """根据平台类型计算原始互动分。"""
        config = PLATFORM_CONFIGS.get(result.platform)
        if not config or not config.scoring_weights:
            return self._heuristic_score_value(result)
        
        metrics = result.engagement_metrics
        score = 0.0
        for metric_key, weight in config.scoring_weights.items():
            score += _safe_num(metrics.get(metric_key, 0)) * weight
        return score
    
    def _normalize_scores(self, scored: List[ScoredResult]) -> List[ScoredResult]:
        """将各平台评分归一化到 [0, 1]。"""
        if not scored:
            return scored
        max_score = max(s.quality_score for s in scored)
        if max_score > 0:
            for s in scored:
                s.quality_score = s.quality_score / max_score
        return scored
```

小红书评论去重修正：在 `SearchOrchestrator._search_single_platform` 中，抓完详情后用去重评论数替换 `comments_count`：

```python
# 小红书详情抓取后
if config.name == "xiaohongshu":
    for note in results:
        if note.top_comments:
            note.engagement_metrics["comments_count"] = len(note.top_comments)
```

### 6. 简化 Orchestrator 搜索路由

```python
# orchestrator.py
def _handle_search_resource(
    self, user_input: str,
    history: Optional[List[Dict[str, str]]] = None,
    platforms: Optional[List[str]] = None,
) -> str:
    """直接调用 ResourceSearcher，不再绕道 TutorAgent。"""
    try:
        results = self._resource_searcher.search(
            user_input,
            platforms=platforms,
            user_selected=platforms is not None,
        )
        # 存入 session state
        self._store_search_results(results, user_input)
        # 传给 TutorAgent 生成带资源推荐的回复
        return self.tutor.run_with_resources(user_input, results, history=history)
    except Exception as e:
        logger.warning(f"搜索失败: {e}")
        return self._handle_ask_question(user_input, history=history)
```

### 7. TutorAgent 改造

移除 `_try_resource_search` 方法，新增 `run_with_resources`：

```python
# tutor.py
def run_with_resources(
    self,
    user_input: str,
    search_results: List[SearchResult],
    history: Optional[List[Dict[str, str]]] = None,
) -> str:
    """处理带搜索结果的用户输入，生成包含资源推荐的回复。"""
    prompt = self._build_free_mode_prompt(user_input, history=history, use_rag=True)
    response = self._call_llm(prompt)
    
    if search_results:
        resource_text = "\n\n🔍 推荐资源：\n"
        for r in search_results:
            resource_text += f"- [{r.title}]({r.url}) ({r.platform})\n"
        response += resource_text
    
    return response
```

### 8. 平台选择器 UI

在 `_render_chat_input` 和 `render_home_view` 中新增平台选择器：

```python
# renderer.py - _render_chat_input 中新增
PLATFORM_OPTIONS = {
    "社区笔记": [("📕 小红书", "xiaohongshu")],
    "网页文章": [("🌐 Google", "google")],
    "视频": [("▶️ YouTube", "youtube"), ("📺 B站", "bilibili")],
}

def _render_platform_selector():
    """渲染平台选择器（可折叠的 chip/tag 多选）。"""
    if "selected_platforms" not in st.session_state:
        st.session_state.selected_platforms = []
    
    with st.expander("🔍 选择搜索平台（可选）", expanded=False):
        selected = []
        for category, platforms in PLATFORM_OPTIONS.items():
            st.caption(category)
            cols = st.columns(len(platforms))
            for i, (label, key) in enumerate(platforms):
                with cols[i]:
                    if st.checkbox(label, key=f"platform_{key}",
                                   value=key in st.session_state.selected_platforms):
                        selected.append(key)
        st.session_state.selected_platforms = selected
```

选中的平台通过 `st.session_state.selected_platforms` 传递给 Orchestrator。

### 9. ResourceSearcher 接口更新

```python
# resource_searcher.py（重命名后）
class ResourceSearcher:
    """统一资源搜索器（原 BrowserResourceSearcher）"""
    
    PLATFORMS = ["xiaohongshu", "google", "youtube", "bilibili"]
    DEFAULT_TOP_K = 10
    
    def search(
        self,
        query: str,
        platforms: Optional[List[str]] = None,
        user_selected: bool = False,
    ) -> List[SearchResult]:
        """搜索学习资源。
        
        Args:
            query: 搜索关键词
            platforms: 指定平台列表，None 表示全部
            user_selected: 用户是否主动选择了平台（影响搜索深度）
        """
        target_platforms = platforms if platforms else self.PLATFORMS
        per_platform_limit = self._calculate_limit(target_platforms, user_selected)
        
        return asyncio.run(
            self._orchestrator.search_all_platforms(
                query, target_platforms,
                per_platform_limit=per_platform_limit,
                top_k=self.DEFAULT_TOP_K,
            )
        )
    
    def _calculate_limit(self, platforms: List[str], user_selected: bool) -> int:
        if not user_selected:
            return 10
        if len(platforms) == 1:
            return 60
        return max(10, 40 // len(platforms))
```

## Data Models

### RawSearchResult 扩展

```python
class RawSearchResult(BaseModel):
    # ... 现有字段 ...
    deduplicated_comment_count: int = 0  # 去重后评论数
```

### SearchResult 扩展（无变更）

SearchResult 模型保持不变，`quality_score` 字段已存在。

## Correctness Properties

### Property 1: 搜索量策略正确性
- 未选平台时，每平台搜索 10 条
- 选 1 个平台时，该平台搜索 60 条
- 选 N 个平台时（N>1），每平台搜索 max(10, 40//N) 条
- 最终返回结果数 ≤ 10

### Property 2: 评分归一化正确性
- 所有返回结果的 quality_score 在 [0.0, 1.0] 区间内
- 最高分结果的 quality_score == 1.0（归一化后）

### Property 3: 平台选择器传递正确性
- 用户选择的平台列表完整传递到 SearchOrchestrator
- 未选择时传递全部 4 个默认平台

### Property 4: 评论去重正确性
- 小红书结果的 deduplicated_comment_count ≤ 原始 comments_count
- 去重使用前 30 字指纹，相同指纹的评论只计一次

### Property 5: 关键词统一性
- Orchestrator 和 TutorAgent 使用的搜索关键词列表引用同一对象
- 修改 SEARCH_KEYWORDS 后两处检测行为同步变化
