# Implementation Plan: 搜索模块重构

## Overview

按照设计文档，分阶段重构搜索模块：先清理死代码和统一基础设施（关键词、导入），再简化调用链路，然后新增 B站支持和弹性搜索量，接着统一排名策略，最后实现平台选择器 UI。每步增量构建，确保不出现孤立代码。

## Tasks

- [x] 1. 清理死代码与重命名
  - [x] 1.1 移除 `src/specialists/resource_searcher.py` 中的旧 `ResourceSearcher` 类（第 27-398 行）及其全部方法（`_search_bilibili`、`_search_youtube`、`_search_google`、`_search_github`、`_search_xiaohongshu`、`_search_wechat`、`search`）
    - 保留 `BrowserResourceSearcher` 类作为唯一搜索器实现
    - _Requirements: 1.1, 1.2_
  - [x] 1.2 将 `BrowserResourceSearcher` 重命名为 `ResourceSearcher`，更新类名和文件内引用
    - 消除别名导入（`BrowserResourceSearcher as ResourceSearcher`）
    - _Requirements: 1.3_
  - [x] 1.3 更新所有导入语句：`orchestrator.py`、`tutor.py`、`planner.py` 及测试文件中的导入路径
    - 直接 `from src.specialists.resource_searcher import ResourceSearcher`，不再使用 `as` 别名
    - 移除或重写仅测试旧 `ResourceSearcher` 的测试用例（如 `test_resource_aggregation_properties.py` 中的相关用例）
    - _Requirements: 1.4, 5.1, 5.2, 5.3, 5.4_
  - [ ]* 1.4 编写单元测试验证重命名后的 ResourceSearcher 可正常实例化和调用 search 方法
    - _Requirements: 1.5, 4.1_

- [x] 2. 统一搜索意图关键词
  - [x] 2.1 新建 `src/core/search_keywords.py`，定义 `SEARCH_KEYWORDS` 列表和 `is_search_intent(user_input)` 函数
    - 关键词列表为 Orchestrator 和 TutorAgent 当前两份列表的并集
    - _Requirements: 2.1, 2.2_
  - [x] 2.2 修改 `src/agents/orchestrator.py` 的 `_detect_intent_by_keywords` 方法，引用 `search_keywords.is_search_intent`
    - 移除 Orchestrator 内部的搜索关键词硬编码
    - _Requirements: 2.3_
  - [x] 2.3 修改 `src/agents/tutor.py` 的 `_try_resource_search` 方法中的关键词检测，引用同一份 `search_keywords.is_search_intent`
    - 移除 TutorAgent 内部的搜索关键词硬编码
    - _Requirements: 2.4, 2.5_
  - [ ]* 2.4 编写属性测试验证关键词统一性
    - **Property 5: 关键词统一性**
    - **Validates: Requirements 2.1, 2.5**

- [x] 3. 简化搜索调用链路
  - [x] 3.1 修改 `src/agents/orchestrator.py` 的 `_handle_search_resource` 方法，直接调用 `ResourceSearcher.search()`，不再经由 `TutorAgent.run()` 中转
    - 搜索结果存入 session state，传给 TutorAgent 生成回复
    - 搜索失败时记录日志并回退到普通对话模式
    - _Requirements: 3.1, 3.5, 4.2, 4.3_
  - [x] 3.2 在 `src/agents/tutor.py` 中新增 `run_with_resources(user_input, search_results, history)` 方法
    - 接收外部传入的搜索结果，生成包含 "🔍 推荐资源" 区块的回复
    - _Requirements: 3.2, 3.3, 4.3_
  - [x] 3.3 移除 `src/agents/tutor.py` 中 `_try_resource_search` 方法的关键词检测和自行触发搜索逻辑
    - TutorAgent 在 free mode 下不再自行触发搜索
    - _Requirements: 3.3, 3.4_
  - [ ]* 3.4 编写单元测试验证调用链路简化
    - 测试 Orchestrator 识别搜索意图后直接调用 ResourceSearcher
    - 测试搜索失败时回退到普通对话
    - _Requirements: 3.1, 3.5_

- [x] 4. Checkpoint - 确保基础重构完成
  - 确保所有测试通过，ask the user if questions arise.

- [x] 5. 新增 B站平台支持
  - [x] 5.1 扩展 `src/specialists/platform_configs.py`：`PlatformConfig` 新增 `platform_category`、`scoring_weights`、`use_api_search`、`default_search_count`、`focused_search_count` 字段，新增 bilibili 配置到 `PLATFORM_CONFIGS`
    - _Requirements: 9.1, 6.2_
  - [x] 5.2 扩展 `src/specialists/browser_models.py`：`RawSearchResult` 新增 `deduplicated_comment_count` 字段
    - _Requirements: 8.2_
  - [x] 5.3 新建 `src/specialists/bilibili_searcher.py`，实现 `BiliBiliSearcher` 类
    - 使用 httpx 调用 `api.bilibili.com/x/web-interface/search/type` 获取视频结果
    - 提取标题、URL、播放量、弹幕数、收藏数、点赞数
    - API 失败时回退到构造 B站搜索链接作为降级结果
    - _Requirements: 9.2, 9.3, 9.4_
  - [x] 5.4 修改 `src/specialists/search_orchestrator.py` 的 `_search_single_platform` 方法，对 `use_api_search=True` 的平台（bilibili）调用 `BiliBiliSearcher` 而非 `BrowserAgent`
    - _Requirements: 9.2_
  - [ ]* 5.5 编写单元测试验证 B站搜索器
    - 测试 API 正常返回时的结果解析
    - 测试 API 失败时的降级逻辑
    - _Requirements: 9.2, 9.3, 9.4_

- [x] 6. 弹性搜索量策略
  - [x] 6.1 修改 `src/specialists/resource_searcher.py` 的 `ResourceSearcher.search()` 方法，新增 `user_selected` 参数，实现 `_calculate_limit` 搜索量计算逻辑
    - 未选平台：每平台 10 条；选 1 个：60 条；选多个：40 条均分
    - _Requirements: 7.1, 7.2, 7.3_
  - [x] 6.2 修改 `src/specialists/search_orchestrator.py` 的 `search_all_platforms` 方法，新增 `per_platform_limit` 参数，按传入的 limit 控制每平台搜索条数
    - 所有原始结果汇入 Candidate_Pool，评分排序后截取 top 10
    - _Requirements: 7.4, 7.5_
  - [ ]* 6.3 编写属性测试验证搜索量策略正确性
    - **Property 1: 搜索量策略正确性**
    - **Validates: Requirements 7.1, 7.2, 7.3, 7.5**

- [x] 7. 统一各平台排名策略
  - [x] 7.1 修改 `src/specialists/quality_scorer.py`，新增 `_platform_score(result)` 方法，根据平台配置的 `scoring_weights` 计算原始互动分
    - 小红书：`deduplicated_comment_count × 5 + 收藏数 × 2 + 点赞数 × 1`
    - B站：`播放量 × 1 + 弹幕数 × 3 + 收藏数 × 2 + 点赞数 × 1`
    - YouTube：`观看数 × 1 + 点赞数 × 2 + 评论数 × 3`
    - Google：启发式评分（有摘要 +0.3，知名站点 +0.3，标题相关度 +0.4）
    - _Requirements: 8.1, 8.3, 8.4, 8.5_
  - [x] 7.2 修改 `src/specialists/quality_scorer.py`，新增 `_normalize_scores(scored)` 方法，将各平台评分归一化到 [0, 1] 区间
    - _Requirements: 8.6_
  - [x] 7.3 修改 `src/specialists/search_orchestrator.py` 的 `_search_single_platform`，小红书详情抓取后用去重评论数替换 `comments_count`
    - _Requirements: 8.2_
  - [ ]* 7.4 编写属性测试验证评分归一化正确性
    - **Property 2: 评分归一化正确性**
    - **Validates: Requirements 8.6**

- [x] 8. Checkpoint - 确保搜索后端完成
  - 确保所有测试通过，ask the user if questions arise.

- [x] 9. 平台选择器 UI
  - [x] 9.1 修改 `src/ui/renderer.py` 的 `_render_chat_input` 函数，新增平台选择器组件
    - 定义 `PLATFORM_OPTIONS` 按分类分组：社区笔记（小红书）、网页文章（Google）、视频（YouTube、B站）
    - 使用 `st.expander` + `st.checkbox` 实现可折叠多选
    - 选中平台存入 `st.session_state.selected_platforms`
    - _Requirements: 6.1, 6.2, 6.3, 6.4_
  - [x] 9.2 修改 `src/ui/layout.py` 的 `render_home_view`，将 `st.session_state.selected_platforms` 传递给 Orchestrator
    - 未选择时传 None（默认全搜），选择时传平台列表
    - _Requirements: 6.5_
  - [ ]* 9.3 编写属性测试验证平台选择器传递正确性
    - **Property 3: 平台选择器传递正确性**
    - **Validates: Requirements 6.3, 6.4, 6.5**

- [x] 10. 集成联调与最终验证
  - [x] 10.1 确保 Orchestrator 接收 UI 传入的 platforms 参数，完整走通：用户选择平台 → Orchestrator 意图识别 → ResourceSearcher.search → SearchOrchestrator → QualityScorer → 返回 top 10
    - 更新 `Orchestrator._handle_search_resource` 签名接收 `platforms` 参数
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 6.5_
  - [ ]* 10.2 编写集成测试验证端到端搜索流程
    - 测试默认全平台搜索、单平台搜索、多平台搜索场景
    - _Requirements: 4.1, 4.2, 4.3, 7.1, 7.2, 7.3_

- [x] 11. Final checkpoint - 确保所有测试通过
  - 确保所有测试通过，ask the user if questions arise.

## Notes

- 标记 `*` 的子任务为可选测试任务，可跳过以加速 MVP
- 每个任务引用了具体的需求编号，确保可追溯性
- Checkpoint 任务用于阶段性验证，确保增量构建的正确性
- 属性测试验证设计文档中的 5 个 Correctness Properties
