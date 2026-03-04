# 实施计划：搜索体验重设计

## 概述

基于需求和设计文档，对现有搜索模块进行增量升级。后端新增三个模块（EngagementRanker、QualityAssessor、PipelineExecutor），增量修改 SearchOrchestrator 和 API 端点；前端扩展类型、新增 zustand store 和四个组件。所有改动为增量修改，不重写现有模块。

## 任务

- [x] 1. 后端数据模型扩展与新增模块基础接口
  - [x] 1.1 扩展 `src/specialists/browser_models.py` 中的 `ScoredResult`，新增 `content_summary`、`comment_summary`、`extracted_content` 字段
    - 保持现有字段不变，仅追加新字段并设置默认值
    - _需求: 2.8, 5.4_
  - [x] 1.2 扩展 `src/core/models.py` 中的 `SearchResult`，新增 `content_summary`、`comment_summary`、`image_urls` 字段
    - 保持现有字段不变，仅追加新字段并设置默认值
    - _需求: 2.8, 7.2_
  - [x] 1.3 在 `backend/routers/search.py` 中新增 `SearchProgressEvent` 和扩展 `SearchResultItem` Pydantic 模型
    - 定义 SSE 事件数据结构：stage、message、platform、total、completed、results、error
    - SearchResultItem 新增 contentSummary、commentSummary、engagementMetrics、imageUrls 字段
    - _需求: 2.1, 2.2, 2.8_

- [x] 2. 实现 EngagementRanker 互动数据初筛模块
  - [x] 2.1 创建 `src/specialists/engagement_ranker.py`，实现 `EngagementRanker` 类
    - 实现 `rank(results, top_n=20)` 方法：跨平台互动数据排序
    - 实现 `_engagement_score(result)` 方法：评论/点赞比例 × 标题加权 × 广告降权
    - BOOST_KEYWORDS: ["经验贴", "面经", "攻略", "踩坑", "总结", "实战"]
    - 结果总数 < 20 时返回全部，不截断
    - _需求: 4.1, 4.2, 4.3, 4.4, 4.5_
  - [ ]* 2.2 编写属性测试：互动排序核心指标
    - **Property 9: 互动排序核心指标**
    - **验证: 需求 4.2**
  - [ ]* 2.3 编写属性测试：标题关键词加权
    - **Property 10: 标题关键词加权**
    - **验证: 需求 4.3**
  - [ ]* 2.4 编写属性测试：初筛输出数量约束
    - **Property 11: 初筛输出数量约束**
    - **验证: 需求 4.4, 4.5**

- [x] 3. 实现 QualityAssessor LLM 质量评估模块
  - [x] 3.1 创建 `src/specialists/quality_assessor.py`，实现 `QualityAssessor` 类
    - 实现 `AssessmentResult` 数据类：quality_score、recommendation_reason、content_summary、comment_summary
    - 实现 `assess_batch(items)` 方法：批量打包为单次 LLM 调用
    - 实现 `_build_batch_prompt(items)` 方法：正文 < 50 字时直接使用原文作为摘要
    - 实现 `assess_single_fallback(raw)` 方法：正文提取失败时降级评估，推荐理由标注"正文未提取"
    - 实现 `_heuristic_fallback(raw)` 方法：LLM 失败时启发式降级（正文前 150 字、评论结论置空、互动数据估算评分）
    - _需求: 5.2, 5.3, 5.4, 5.5, 5.6, 5.7, 5.8, 6.3_
  - [ ]* 3.2 编写属性测试：质量评估四项输出完整
    - **Property 12: 质量评估四项输出完整**
    - **验证: 需求 5.4**
  - [ ]* 3.3 编写属性测试：短正文直接作为摘要
    - **Property 13: 短正文直接作为摘要**
    - **验证: 需求 5.5**
  - [ ]* 3.4 编写属性测试：LLM 失败降级摘要
    - **Property 14: LLM 失败降级摘要**
    - **验证: 需求 5.6**
  - [ ]* 3.5 编写属性测试：最终输出不超过 10 条
    - **Property 15: 最终输出不超过 10 条**
    - **验证: 需求 5.7**
  - [ ]* 3.6 编写属性测试：批次大小上限为 15
    - **Property 17: 批次大小上限为 15**
    - **验证: 需求 6.4**

- [x] 4. 检查点 — 确保后端新模块测试通过
  - 确保所有测试通过，如有疑问请询问用户。

- [x] 5. 实现 PipelineExecutor 流水线执行器
  - [x] 5.1 创建 `src/specialists/pipeline_executor.py`，实现 `PipelineExecutor` 类
    - 构造函数接收 BrowserAgent、ResourceCollector、QualityAssessor、cancel_event
    - 实现 `execute(candidates, progress_callback)` 方法：并行提取 → 实时送入评估队列 → 批量 LLM 评估
    - 实现 `_extract_worker(queue, result, semaphore)` 方法：信号量控制并发 tab 数为 5，单条超时 30 秒
    - 实现 `_batch_assessor(queue, results)` 方法：凑批上限 15 条，超时 3 秒发起 LLM 调用
    - 取消机制：检查 cancel_event，设置后立即退出所有 worker
    - _需求: 5.1, 6.1, 6.2, 6.4, 6.6_
  - [ ]* 5.2 编写属性测试：并发提取上限为 5
    - **Property 16: 并发提取上限为 5**
    - **验证: 需求 6.1**

- [x] 6. 增量修改 SearchOrchestrator 集成漏斗流程
  - [x] 6.1 在 `src/specialists/search_orchestrator.py` 中新增 `search_all_platforms_stream()` 异步生成器方法
    - 构造函数中新增 EngagementRanker、QualityAssessor、PipelineExecutor 实例
    - 实现五阶段流式推送：searching → filtering → extracting → evaluating → done
    - 缓存命中时直接 yield done 事件
    - 单平台超时调整为 45 秒
    - 某平台失败时使用其他平台结果继续漏斗筛选，记录错误信息
    - 浏览器生命周期：提取完成后关闭浏览器，再进入 LLM 评估
    - 现有 `search_all_platforms()` 保持不变
    - _需求: 1.1, 1.2, 1.3, 1.5, 1.6, 1.7, 1.8, 2.1, 5.9, 5.10_
  - [ ]* 6.2 编写属性测试：缓存往返一致性
    - **Property 1: 缓存往返一致性**
    - **验证: 需求 1.6, 1.7, 5.10**
  - [ ]* 6.3 编写属性测试：SSE 事件结构正确性
    - **Property 2: SSE 事件结构正确性**
    - **验证: 需求 2.1, 2.2, 2.3, 2.4, 2.5**
  - [ ]* 6.4 编写属性测试：Done 事件结果完整性
    - **Property 3: Done 事件结果完整性**
    - **验证: 需求 2.7, 2.8**
  - [ ]* 6.5 编写属性测试：并发搜索任务数等于平台数
    - **Property 23: 并发搜索任务数等于平台数**
    - **验证: 需求 1.1, 1.2**

- [x] 7. 重构后端 API 端点
  - [x] 7.1 重构 `backend/routers/search.py` 中的 `/api/search/stream` SSE 端点
    - 调用 SearchOrchestrator.search_all_platforms_stream() 替代原有逻辑
    - 适配新的 SSE 事件格式（stage 字段 + 对应数据）
    - 支持 AbortController 取消：检测连接关闭后设置 cancel_event
    - _需求: 2.1, 2.2, 2.10, 1.4_
  - [x] 7.2 新增 `backend/routers/resource.py`，实现 `/api/resource/refresh` POST 端点
    - 定义 RefreshRequest（url, platform）和 RefreshResponse 模型
    - 调用 SearchOrchestrator 重新提取正文、评论、图片 URL，调用 QualityAssessor 重新评估
    - 超时 90 秒返回 HTTP 408，URL 不可访问返回 HTTP 422
    - 刷新成功后更新缓存
    - 在 `backend/main.py` 中注册新路由
    - _需求: 10.1, 10.2, 10.3, 10.4, 10.5, 10.6, 10.7_
  - [ ]* 7.3 编写属性测试：刷新响应结构完整
    - **Property 21: 刷新响应结构完整**
    - **验证: 需求 10.2, 10.3**
  - [ ]* 7.4 编写属性测试：刷新后缓存更新
    - **Property 22: 刷新后缓存更新**
    - **验证: 需求 10.7**

- [x] 8. 检查点 — 确保后端全部测试通过
  - 确保所有测试通过，如有疑问请询问用户。

- [x] 9. 前端类型扩展与 searchStore 创建
  - [x] 9.1 扩展 `frontend/src/types/index.ts`，新增搜索相关类型
    - 扩展 SearchResult 接口：新增 contentSummary、commentSummary、engagementMetrics、imageUrls 可选字段
    - 新增 SearchHistoryEntry 接口：id、query、platforms、results、resultCount、searchedAt
    - 新增 SearchStage 类型：'idle' | 'searching' | 'filtering' | 'extracting' | 'evaluating' | 'done' | 'error'
    - _需求: 2.8, 3.3_
  - [x] 9.2 创建 `frontend/src/store/searchStore.ts`，实现 zustand store + persist
    - history: SearchHistoryEntry[]，最多保留 20 条
    - resultDetailMap: Record<string, SearchResult>，材料 id → 完整搜索结果
    - addEntry / clearHistory / saveResultDetails / getResultDetail 方法
    - 使用 persist 中间件持久化到 localStorage
    - _需求: 3.3, 3.7, 3.8, 8.1_
  - [ ]* 9.3 编写属性测试：搜索历史单调递增
    - **Property 5: 搜索历史单调递增**
    - **验证: 需求 3.3, 3.7**
  - [ ]* 9.4 编写属性测试：搜索历史时间倒序
    - **Property 6: 搜索历史时间倒序**
    - **验证: 需求 3.8**

- [x] 10. 重构 SearchPanel 搜索面板
  - [x] 10.1 重构 `frontend/src/components/source-panel/SearchPanel.tsx`
    - 新增 searchStage 状态，根据 SSE stage 字段显示中文状态文案
    - SSE 事件处理适配新的 stage 字段格式
    - 搜索完成后调用 searchStore.addEntry() 保存历史记录
    - 新搜索时通过 AbortController 取消当前进行中的搜索
    - 结果列表按 qualityScore 降序统一排序，不按平台分组，每条显示平台标识
    - _需求: 1.4, 2.9, 3.1, 3.2, 3.3, 3.7_
  - [ ]* 10.2 编写属性测试：搜索阶段文案映射
    - **Property 4: 搜索阶段文案映射**
    - **验证: 需求 2.9**
  - [ ]* 10.3 编写属性测试：结果列表统一排序
    - **Property 8: 结果列表统一排序**
    - **验证: 需求 3.1, 3.2**

- [x] 11. 新增 SearchHistoryCard 搜索历史卡片组件
  - [x] 11.1 创建 `frontend/src/components/source-panel/SearchHistoryCard.tsx`
    - 折叠态：搜索关键词 + 平台图标列表 + 结果数量
    - 展开态：完整 top 10 结果列表 + 搜索时间（如"3月4日 14:32"）+ 收起按钮
    - 点击切换展开/收起
    - _需求: 3.4, 3.5, 3.6_
  - [ ]* 11.2 编写属性测试：历史卡片折叠态信息完整
    - **Property 7: 历史卡片折叠态信息完整**
    - **验证: 需求 3.4**

- [x] 12. 新增 PreviewPopup 外部资源预览浮窗组件
  - [x] 12.1 创建 `frontend/src/components/source-panel/PreviewPopup.tsx`
    - 内容区域：标题、URL、平台标识、AI 摘要、评论结论、图片缩略图网格、互动指标、评分、推荐理由
    - 操作按钮：查看完整信息（新标签页打开）、刷新（调用 /api/resource/refresh）、关闭
    - 键盘支持：Escape 关闭
    - 刷新状态：加载骨架屏 / 错误提示+重试按钮
    - 小红书图片缩略图网格展示，点击查看大图
    - 数据来源：从 searchStore.resultDetailMap 获取，不发起额外 API 请求
    - _需求: 7.3, 7.4, 8.1, 8.2, 8.3, 8.4, 8.5, 8.6, 8.7, 8.8_
  - [ ]* 12.2 编写属性测试：预览浮窗内容区域完整
    - **Property 19: 预览浮窗内容区域完整**
    - **验证: 需求 8.2**
  - [ ]* 12.3 编写属性测试：小红书图片 URL 数量约束
    - **Property 18: 小红书图片 URL 数量约束**
    - **验证: 需求 7.1, 7.2**

- [x] 13. 新增 ContentViewer 本地文件内容查看器组件
  - [x] 13.1 创建 `frontend/src/components/source-panel/ContentViewer.tsx`
    - Markdown 渲染（使用已有的 react-markdown 依赖）
    - PDF 文本内容展示
    - 返回材料列表导航按钮
    - 加载指示器 / 错误提示+重试按钮
    - _需求: 9.1, 9.2, 9.3, 9.4, 9.5, 9.6_
  - [ ]* 13.2 编写属性测试：Markdown 渲染正确性
    - **Property 20: Markdown 渲染正确性**
    - **验证: 需求 9.2**

- [x] 14. 集成与串联
  - [x] 14.1 在 SearchPanel 中集成 SearchHistoryCard 列表渲染
    - 搜索历史按时间倒序排列，最新在最上方
    - 展开某条历史时覆盖当前搜索面板区域
    - _需求: 3.5, 3.7, 3.8_
  - [x] 14.2 在 MaterialItem 或 SourcePanel 中集成 PreviewPopup 和 ContentViewer
    - 点击外部资源材料 → 打开 PreviewPopup
    - 点击本地文件材料 → 打开 ContentViewer
    - _需求: 8.1, 9.1_
  - [x] 14.3 在 ResourceCollector 中确保小红书 API 拦截数据包含图片 URL 列表（最多 9 张）
    - 增量修改 `src/specialists/resource_collector.py` 中小红书相关提取逻辑
    - _需求: 7.1_

- [x] 15. 最终检查点 — 确保所有测试通过
  - 确保所有测试通过，如有疑问请询问用户。

## 备注

- 标记 `*` 的任务为可选任务，可跳过以加速 MVP 交付
- 每个任务引用了具体的需求编号，确保可追溯性
- 属性测试验证通用正确性属性，单元测试验证具体示例和边界情况
- 后端属性测试文件：`tests/test_search_redesign_properties.py`
- 前端属性测试文件：`frontend/src/test/search-redesign.property.test.tsx`
- 所有改动为增量修改，不重写 BrowserAgent、ResourceCollector 等现有模块核心逻辑
