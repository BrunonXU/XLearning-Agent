# 实施任务

## 任务 1: SearchResult 数据模型与序列化

- [x] 1.1 在 `src/core/models.py` 中新增 `SearchResult` Pydantic 模型，包含 title、url、platform、type、description 字段，platform 支持 6 个平台值（bilibili, youtube, google, github, xiaohongshu, wechat）
- [x] 1.2 实现 `SearchResult.to_dict()` 和 `SearchResult.from_dict()` 方法
- [x] 1.3 新增 `LearningDay` 模型（day_number, title, topics, resources），替代原 `LearningPhase`
- [x] 1.4 修改 `LearningPlan` 模型，从 phases 结构改为 days: List[LearningDay] 结构
- [x] 1.5 编写 `tests/test_resource_aggregation_properties.py` 中 Property 1（SearchResult round-trip）和 Property 8（无效 JSON 错误处理）的属性测试

## 任务 2: ResourceSearcher 专家模块

- [x] 2.1 创建 `src/specialists/resource_searcher.py`，实现 `ResourceSearcher` 类框架，PLATFORMS 列表包含 6 个平台
- [x] 2.2 实现 `_search_bilibili()`、`_search_youtube()`、`_search_google()`、`_search_github()` 四个搜索方法
- [x] 2.3 实现 `_search_xiaohongshu()` 小红书搜索方法（通过 Web API 搜索笔记）
- [x] 2.4 实现 `_search_wechat()` 微信公众号搜索方法（通过搜狗微信搜索接口）
- [x] 2.5 实现 `search()` 主方法，包含平台故障容错逻辑（跳过失败平台、日志记录、10秒超时）
- [x] 2.6 编写 `tests/test_resource_aggregation_properties.py` 中 Property 2（平台故障容错）的属性测试

## 任务 3: ProgressTracker 每日线性进度

- [x] 3.1 创建 `src/core/progress.py`，实现 `DayProgress` 模型和 `ProgressTracker` 类
- [x] 3.2 实现 `init_from_plan()`，从 LearningPlan 的 days 列表初始化 DayProgress 列表
- [x] 3.3 实现 `mark_day_completed(day_number)` 方法
- [x] 3.4 实现 `get_progress_summary()` 方法，返回 total_days、completed_days、percentage、current_day
- [x] 3.5 实现 `save()` / `load()` / `reset()` 方法，与现有 session storage 集成
- [x] 3.6 编写 Property 4（每日完成状态一致性）、Property 5（线性进度摘要正确性）、Property 6（持久化 round-trip）的属性测试

## 任务 4: PlannerAgent 改造（按天生成计划 + 资源搜索）

- [x] 4.1 修改 `src/agents/planner.py` 的 prompt，使其生成以 Day 为单位的学习计划（Day 1, Day 2...）
- [x] 4.2 在 `run()` 方法中集成 ResourceSearcher，为每天的学习主题搜索资源
- [x] 4.3 实现资源搜索降级逻辑：搜索失败时标注"暂无推荐资源"，不阻塞计划生成
- [x] 4.4 编写 Property 3（多平台资源覆盖）的属性测试

## 任务 5: TutorAgent 改造（参考来源 + 进度感知）

- [x] 5.1 在 `src/agents/tutor.py` 中新增 `_build_reference_section()` 方法，生成「📎 参考来源」区块
- [x] 5.2 修改 `_handle_free_mode()` 方法，在每次回复末尾追加参考来源区块
- [x] 5.3 实现来源追踪逻辑：记录本次回复引用了哪些 PDF 片段、搜索平台、RAG 检索结果
- [x] 5.4 集成 ProgressTracker，在 prompt 中注入当前进度上下文
- [x] 5.5 集成 ResourceSearcher，支持对话中的资源搜索请求
- [x] 5.6 编写 Property 10（Tutor 参考来源完整性）的属性测试

## 任务 6: Orchestrator 改造（移除 Quiz + 新增资源搜索意图）

- [x] 6.1 在 `src/agents/orchestrator.py` 中新增 `search_resource` 意图类型
- [x] 6.2 完全移除 `start_quiz` 意图及所有 Quiz/Validator 相关路由代码
- [x] 6.3 调整意图路由优先级为：create_plan > ask_question > search_resource
- [x] 6.4 在 `_detect_intent_by_keywords` 中添加资源搜索关键词（搜索资源、找资源、推荐资源等）
- [x] 6.5 在调用 Agent 前注入 ProgressTracker 上下文
- [x] 6.6 编写 Property 9（意图路由优先级，无 Quiz）的属性测试

## 任务 7: UI 重构（资源卡片 + 每日进度条 + 移除 Quiz）

- [x] 7.1 修改 `src/ui/layout.py`，将主流程从三步骤（Plan | Study | Quiz）改为两步骤（Plan | Study），移除所有 Quiz 相关步骤
- [x] 7.2 在 `src/ui/renderer.py` 中实现 `render_resource_card()` 函数，渲染资源卡片（标题、平台标识、描述、链接）
- [x] 7.3 在 Plan 页面实现每日学习大纲展示，以 Day 为单位列出，每天带「完成」按钮
- [x] 7.4 在 Plan 页面顶部实现线性进度条（st.progress_bar），展示已完成天数 / 总天数
- [x] 7.5 在 Study 页面添加「搜索更多资源」交互入口
- [x] 7.6 全面清理 UI 中所有 Quiz、测验、自测相关的入口、按钮、标签页和文案
- [x] 7.7 编写 Property 7（LearningDay resources 向后兼容）的属性测试

## 任务 8: 集成测试与清理

- [x] 8.1 编写 `tests/test_resource_aggregation.py` 单元测试，覆盖 SearchResult 构造（含 xiaohongshu/wechat）、DayProgress 模型、ProgressTracker 初始化/标记/摘要
- [x] 8.2 编写 UI 相关单元测试：主流程两步骤验证、无 Quiz 入口验证、资源卡片渲染验证
- [x] 8.3 清理项目中所有 Quiz/Validator/QuizMaker 的残留引用（imports、配置、文档）
- [x] 8.4 运行全部属性测试和单元测试，确保通过
