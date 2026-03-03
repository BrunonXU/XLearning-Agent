# Requirements Document

## Introduction

当前搜索模块存在架构混乱问题：老的 `ResourceSearcher`（httpx 直连 API）和新的 `BrowserResourceSearcher`（Playwright 浏览器 Agent）共存于同一文件，老代码已无生产调用但仍占据 ~370 行；搜索意图检测分散在 Orchestrator 和 TutorAgent 两层，关键词列表不一致导致触发不可靠；Orchestrator 识别到搜索意图后绕道 TutorAgent free mode 再二次检测，路由路径冗余。

此外，用户无法在 UI 中选择特定平台进行搜索，搜索量策略不够灵活（选定平台时应集中搜索更多内容），各平台排名策略不统一，小红书评论去重未反映到互动分计算中，且缺少 B站平台支持。

本次重构旨在：清理死代码、统一意图检测、简化调用链路、新增平台选择器 UI、实现弹性搜索量策略、统一各平台排名逻辑、新增 B站平台支持。

## Glossary

- **Orchestrator**: 顶层意图路由器（`src/agents/orchestrator.py`），负责识别用户意图并分发到对应处理器
- **TutorAgent**: 教学对话代理（`src/agents/tutor.py`），处理自由对话和资源搜索
- **BrowserResourceSearcher**: 基于 Playwright 浏览器的资源搜索器（`src/specialists/resource_searcher.py`），当前生产使用的搜索实现
- **Old_ResourceSearcher**: 基于 httpx 直连 API 的旧搜索器（同文件），已无生产调用
- **SearchOrchestrator**: 搜索调度器（`src/specialists/search_orchestrator.py`），协调多平台并发搜索、缓存和评分
- **Search_Keyword_List**: 用于关键词匹配检测搜索意图的关键词集合
- **Search_Intent**: Orchestrator 识别出的 "search_resource" 意图类型
- **SearchResult**: 搜索结果数据模型（`src/core/models.py`）
- **Platform_Selector**: 聊天框中的平台选择 UI 组件，允许用户选择搜索的目标平台
- **Platform_Category**: 平台分类（社区笔记类、网页文章类、视频类）
- **Candidate_Pool**: 搜索候选池，存储所有平台搜到的原始结果，经评分排序后截取 top_k 返回
- **Deduplicated_Comment_Count**: 去重后的评论数量，用于替代 API 返回的原始 comments_count 参与互动分计算

## Requirements

### Requirement 1: 移除旧搜索器死代码

**User Story:** 作为开发者，我希望移除不再使用的旧 `ResourceSearcher` 类及其所有方法，以减少代码量和维护负担。

#### Acceptance Criteria

1. THE Refactored_Module SHALL 不包含 Old_ResourceSearcher 类及其全部方法（`_search_bilibili`、`_search_youtube`、`_search_google`、`_search_github`、`_search_xiaohongshu`、`_search_wechat`、`search`）
2. WHEN 移除 Old_ResourceSearcher 后，THE Refactored_Module SHALL 保留 BrowserResourceSearcher 作为唯一的搜索器实现
3. WHEN 移除 Old_ResourceSearcher 后，THE Refactored_Module SHALL 将 BrowserResourceSearcher 重命名为 ResourceSearcher，消除别名导入（`BrowserResourceSearcher as ResourceSearcher`）
4. WHEN 移除 Old_ResourceSearcher 后，THE Refactored_Module SHALL 更新所有导入语句，使其直接导入新的 ResourceSearcher（不再使用 `as` 别名）
5. THE Refactored_Module SHALL 移除仅测试 Old_ResourceSearcher 的测试用例，并保留或迁移针对 BrowserResourceSearcher 的测试

### Requirement 2: 统一搜索意图关键词检测

**User Story:** 作为开发者，我希望搜索意图的关键词检测只在一个地方维护，以避免两层关键词列表不一致导致搜索漏触发或误触发。

#### Acceptance Criteria
可以帮我看看tasks运行到哪了吗
1. THE System SHALL 维护唯一一份 Search_Keyword_List，供所有搜索意图检测逻辑引用
2. THE Search_Keyword_List SHALL 包含 Orchestrator 和 TutorAgent 当前两份列表的并集（至少包含：搜索资源、找资源、推荐资源、search resource、搜索更多资源、找学习资源、推荐学习资源、有什么资源、资源推荐、有哪些资源、学习资源、find resource、recommend、搜索更多）
3. WHEN Orchestrator 检测到 Search_Intent 时，THE Orchestrator SHALL 使用统一的 Search_Keyword_List 进行匹配
4. WHEN TutorAgent 检测搜索请求时，THE TutorAgent SHALL 使用同一份 Search_Keyword_List 进行匹配
5. IF Search_Keyword_List 需要新增或修改关键词，THEN THE System SHALL 只需在一处修改即可生效于所有检测点

### Requirement 3: 简化搜索调用链路

**User Story:** 作为开发者，我希望 Orchestrator 识别到搜索意图后直接调用搜索器，而不是绕道 TutorAgent free mode 再二次检测，以减少不必要的间接调用和潜在的触发失败。

#### Acceptance Criteria

1. WHEN Orchestrator 识别到 Search_Intent 时，THE Orchestrator SHALL 直接调用 ResourceSearcher 执行搜索，不再经由 TutorAgent.run() 中转
2. WHEN Orchestrator 直接执行搜索后，THE Orchestrator SHALL 将搜索结果传递给 TutorAgent 用于生成包含资源推荐的回复
3. THE TutorAgent SHALL 移除 `_try_resource_search` 方法中的关键词检测逻辑，改为接收外部传入的搜索结果
4. WHEN TutorAgent 在 free mode 下收到用户输入且未经 Orchestrator 路由时，THE TutorAgent SHALL 不再自行触发搜索（搜索触发统一由 Orchestrator 负责）
5. IF Orchestrator 搜索执行失败，THEN THE Orchestrator SHALL 记录错误日志并回退到普通对话模式，将用户输入交给 TutorAgent 以 free mode 处理

### Requirement 4: 保持搜索功能完整性

**User Story:** 作为用户，我希望重构后搜索功能的行为与重构前一致，搜索结果的质量和展示不受影响。

#### Acceptance Criteria

1. THE ResourceSearcher SHALL 保持 `search(query, platforms)` 方法签名不变
2. WHEN 搜索返回结果时，THE System SHALL 将结果存入 session state 供 Resources 面板展示（与重构前行为一致）
3. WHEN 搜索返回结果时，THE System SHALL 在回复末尾附加 "🔍 推荐资源" 区块（与重构前格式一致）
4. THE SearchOrchestrator、BrowserAgent、ResourceCollector、QualityScorer、SearchCache 等下游组件 SHALL 保持接口和行为不变

### Requirement 5: 清理导入和类型标注

**User Story:** 作为开发者，我希望重构后所有文件的导入路径和类型标注保持一致且正确，不存在断裂的引用。

#### Acceptance Criteria

1. WHEN BrowserResourceSearcher 重命名为 ResourceSearcher 后，THE System SHALL 更新 `orchestrator.py`、`tutor.py`、`planner.py` 中的导入语句
2. WHEN BrowserResourceSearcher 重命名为 ResourceSearcher 后，THE System SHALL 更新 `tutor.py` 中 `set_resource_searcher` 方法的类型标注
3. THE System SHALL 确保所有测试文件中的导入路径指向重命名后的 ResourceSearcher
4. IF 存在引用 Old_ResourceSearcher 的测试用例（如 `test_resource_aggregation_properties.py`），THEN THE System SHALL 移除或重写这些测试以使用新的 ResourceSearcher

### Requirement 6: 平台选择器 UI 组件

**User Story:** 作为用户，我希望在聊天框中可以选择搜索的目标平台，以便集中搜索我关心的资源类型。

#### Acceptance Criteria

1. THE Platform_Selector SHALL 在聊天输入区域提供可选的平台多选组件，支持以下 4 个平台：小红书、Google、YouTube、B站
2. THE Platform_Selector SHALL 按 Platform_Category 分组展示：社区笔记类（小红书）、网页文章类（Google）、视频类（YouTube、B站）
3. WHEN 用户未选择任何平台时，THE System SHALL 默认搜索全部 4 个平台
4. WHEN 用户选择了特定平台时，THE System SHALL 仅搜索用户选择的平台
5. THE Platform_Selector SHALL 将用户选择的平台列表传递给 Orchestrator，由 Orchestrator 转发给 ResourceSearcher

### Requirement 7: 弹性搜索量策略

**User Story:** 作为用户，我希望选择特定平台时能获得更深入的搜索结果，不选时各平台均衡搜索。

#### Acceptance Criteria

1. WHEN 用户未选择特定平台（默认全搜）时，THE SearchOrchestrator SHALL 对每个平台搜索 10 条，最终返回 top 10 条结果
2. WHEN 用户选择了单个平台时，THE SearchOrchestrator SHALL 对该平台集中搜索 60 条，最终返回 top 10 条结果
3. WHEN 用户选择了多个平台时，THE SearchOrchestrator SHALL 将 40 条搜索配额均分到各选中平台（如选 2 个平台则每平台 20 条），最终返回 top 10 条结果
4. THE SearchOrchestrator SHALL 将所有平台搜到的原始结果存入 Candidate_Pool，经 QualityScorer 评分排序后截取 top_k 返回
5. THE System SHALL 始终返回 top 10 条结果给用户，无论搜索了多少条原始结果

### Requirement 8: 统一各平台排名策略

**User Story:** 作为用户，我希望各平台的搜索结果都有合理的排名，而不是只有小红书有互动分排序。

#### Acceptance Criteria

1. THE QualityScorer SHALL 对小红书结果使用互动分排序：`Deduplicated_Comment_Count × 5 + 收藏数 × 2 + 点赞数 × 1`
2. WHEN 计算小红书互动分时，THE System SHALL 使用 Deduplicated_Comment_Count（去重后的评论数）替代 API 返回的原始 comments_count
3. THE QualityScorer SHALL 对 B站结果使用：`播放量 × 1 + 弹幕数 × 3 + 收藏数 × 2 + 点赞数 × 1`
4. THE QualityScorer SHALL 对 YouTube 结果使用：`观看数 × 1 + 点赞数 × 2 + 评论数 × 3`
5. THE QualityScorer SHALL 对 Google 结果使用启发式评分：有内容摘要 +0.3，来自知名技术站点（如 MDN、Stack Overflow、官方文档）+0.3，标题与查询相关度 +0.4
6. WHEN 多平台结果混合排序时，THE System SHALL 将各平台的互动分归一化到 [0, 1] 区间后再统一排序

### Requirement 9: 新增 B站平台支持

**User Story:** 作为用户，我希望能搜索 B站的学习视频资源。

#### Acceptance Criteria

1. THE System SHALL 新增 bilibili 平台配置到 PLATFORM_CONFIGS
2. THE bilibili 平台 SHALL 优先使用 B站搜索 API（`api.bilibili.com/x/web-interface/search/type`）获取结果，不依赖 Playwright 浏览器
3. THE bilibili 搜索结果 SHALL 包含标题、URL、播放量、弹幕数、收藏数、点赞数等互动指标
4. IF B站 API 请求失败，THEN THE System SHALL 回退到构造 B站搜索链接作为降级结果
5. THE bilibili 平台 SHALL 出现在 Platform_Selector 的"视频类"分组中
