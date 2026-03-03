# 实施计划：智能浏览器 Agent 资源搜索

## 概述

将现有 `ResourceSearcher` 替换为基于 Playwright + LLM 的智能浏览器 Agent 架构。按照数据模型 → 内部组件 → 核心引擎 → 调度器 → UI 的顺序逐步实现，每步构建在前一步之上，确保无孤立代码。

## Tasks

- [x] 1. 扩展 SearchResult 数据模型与内部模型定义
  - [x] 1.1 在 `src/core/models.py` 中为 SearchResult 新增可选字段：quality_score（float, 默认 0.0）、recommendation_reason（str, 默认 ""）、engagement_metrics（dict, 默认 {}）、comments_preview（list, 默认 []）
    - 使用 Pydantic Field(default_factory=...) 定义 dict 和 list 字段
    - 确保 to_dict() 和 from_dict() 包含所有新增字段
    - 保持向后兼容：不包含新字段的旧字典数据仍可正确解析
    - _Requirements: 8.1, 8.2, 8.3, 8.4_

  - [x] 1.2 创建 `src/specialists/browser_models.py`，定义内部数据模型 RawSearchResult、ResourceDetail、ScoredResult
    - RawSearchResult：title, url, platform, resource_type, description, engagement_metrics, comments, content_snippet, image_urls
    - ResourceDetail：content_snippet, likes, favorites, comments_count, comments, extra_metrics, image_urls, image_descriptions
    - ScoredResult：raw (RawSearchResult), quality_score, recommendation_reason
    - 所有模型继承 Pydantic BaseModel
    - **注意**：需要补充 image_urls（List[str]）和 image_descriptions（List[str]）字段到已有模型
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 11.2, 11.3_

  - [ ]* 1.3 编写属性测试：SearchResult 序列化往返
    - **Property 13: SearchResult 序列化往返**
    - 使用 hypothesis 生成包含和不包含新字段的 SearchResult，验证 to_dict() → from_dict() 往返一致性
    - **Validates: Requirements 8.1, 8.2, 8.3, 8.4**

- [x] 2. Checkpoint - 确保数据模型测试通过
  - 确保所有测试通过，如有问题请询问用户。

- [x] 3. 实现平台配置与搜索缓存
  - [x] 3.1 创建 `src/specialists/platform_configs.py`，定义 PlatformConfig 和 DetailSelectors 数据类，以及六个平台的配置实例
    - 每个平台配置包含：name, search_url_template, result_selector, title_selector, link_selector, description_selector, resource_type, detail_selectors
    - PlatformConfig 新增字段：requires_login, cookie_file, use_js_extraction, js_extract_fn, use_hybrid_mode, api_intercept_patterns, detail_extract_method
    - DetailSelectors 新增字段：comment_likes_selector, initial_state_path
    - 小红书配置：requires_login=True, use_hybrid_mode=True, api_intercept_patterns=["/api/sns/web/v1/search/notes", "/api/sns/web/v2/comment/page", "/api/sns/web/v1/feed"], detail_extract_method="js_state", cookie_file="scripts/.xhs_cookies.json"
    - 定义 PLATFORM_CONFIGS 字典，键为平台名称字符串
    - _Requirements: 2.1, 2.4, 6.5.1_

  - [x] 3.2 创建 `src/specialists/search_cache.py`，实现 SearchCache 类
    - 实现 get(query, platforms) → Optional[List[SearchResult]]
    - 实现 set(query, platforms, results) → None
    - 实现 _make_key(query, platforms) → str，使用 query + sorted platforms 生成哈希键
    - TTL 默认 3600 秒（1 小时）
    - 缓存过期后 get() 返回 None
    - _Requirements: 7.1, 7.2, 7.3, 7.4_

  - [ ]* 3.3 编写属性测试：缓存存取一致性
    - **Property 11: 缓存存取一致性**
    - 使用 hypothesis 生成随机 query 和 platforms，验证存入后在 TTL 内取出结果一致
    - **Validates: Requirements 7.1, 7.2**

  - [ ]* 3.4 编写属性测试：缓存过期失效
    - **Property 12: 缓存过期失效**
    - 使用 time mock 验证超过 TTL 后缓存返回 None
    - **Validates: Requirements 7.4**

- [x] 4. 实现 ResourceCollector 数据采集组件
  - [x] 4.1 创建 `src/specialists/resource_collector.py`，实现 ResourceCollector 类
    - 实现 extract_search_results(page, config) → List[RawSearchResult]：从搜索结果页提取标题、URL、描述
    - 实现 extract_search_results_js(page, config) → List[RawSearchResult]：使用 JS evaluate 整体提取（小红书等平台）
    - 实现 extract_from_intercepted_json(items, config) → List[RawSearchResult]：从拦截到的 API JSON 中提取搜索结果（混合模式）
    - 实现 extract_detail(page, config) → ResourceDetail：从详情页提取正文、互动指标、前 10 条评论
    - 实现 extract_detail_from_initial_state(page) → str：从 `__INITIAL_STATE__` 内嵌 JSON 提取正文（三级回退策略）
    - 实现 extract_image_urls(page_or_json) → List[str]：从 __INITIAL_STATE__ 或 API JSON 的 image_list 字段提取图片 URL 列表
    - 实现 extract_top_comments(page, config) → List[Dict[str, str]]：提取高赞评论（文本+点赞数），按赞数排序
    - 实现 parse_intercepted_comments(raw_comments) → List[Dict[str, str]]：从拦截到的评论 API JSON 中解析评论，含去重和广告过滤
    - 评论去重：以前 30 字为指纹，跳过重复评论
    - 广告评论过滤：包含 2 个及以上营销关键词（私信、加我、免费领、优惠券、微信等）的评论自动跳过
    - 按笔记 ID 去重，优先保留带 xsec_token 的链接
    - 字段提取失败时设为默认值（空字符串或 0），不抛出异常
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 6.5.1, 6.5.2, 6.5.4, 6.5.5, 6.5.6, 11.1, 11.2_

  - [ ]* 4.2 编写属性测试：搜索结果提取完整性
    - **Property 1: 搜索结果提取完整性**
    - 验证提取的 RawSearchResult 的 title 非空、url 非空、platform 为六个平台之一
    - **Validates: Requirements 1.3, 4.1**

  - [ ]* 4.3 编写属性测试：评论提取上限
    - **Property 7: 评论提取上限**
    - 验证 ResourceDetail 的 comments 列表长度不超过 10
    - **Validates: Requirements 4.3**

- [x] 5. 实现 QualityScorer LLM 质量评估组件
  - [x] 5.1 创建 `src/specialists/quality_scorer.py`，实现 QualityScorer 类
    - 实现 score_batch(results) → List[ScoredResult]：批量评估资源质量
    - 实现 _build_scoring_prompt(result) → str：构建包含四个维度（互动指标、内容深度、评论质量、时效性）的评分 prompt
    - 实现 _parse_score_response(response) → Tuple[float, str]：解析 LLM 返回的评分和推荐理由
    - LLM 调用失败时返回 quality_score=0.0, recommendation_reason=""
    - LLM 返回格式异常时使用默认评分 0.0
    - 部分维度数据缺失时基于可用维度评估，在推荐理由中注明
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6_

  - [ ]* 5.2 编写属性测试：质量评分有效性
    - **Property 5: 质量评分有效性**
    - 验证 quality_score 在 [0.0, 1.0] 闭区间内，recommendation_reason 非空
    - **Validates: Requirements 3.4, 3.5**

  - [ ]* 5.3 编写属性测试：缺失维度评分降级
    - **Property 6: 缺失维度评分降级**
    - 使用 hypothesis 生成 engagement_metrics 部分或全部缺失的 RawSearchResult，验证仍返回有效评分
    - **Validates: Requirements 3.6**

- [x] 6. Checkpoint - 确保核心组件测试通过
  - 确保所有测试通过，如有问题请询问用户。

- [ ] 7. 实现 BrowserAgent 浏览器引擎
  - [x] 7.1 创建 `src/specialists/browser_agent.py`，实现 BrowserAgent 类
    - 实现 launch(config)：启动 Playwright Chromium 浏览器实例，配置随机 User-Agent、浏览器指纹；如 config.requires_login 则加载 Cookie
    - 实现 search_platform(query, config) → List[RawSearchResult]：在指定平台执行搜索；对 use_hybrid_mode 平台注册 API 响应拦截器，从拦截到的 JSON 中提取结构化数据；搜索阶段全量获取（~60 条），通过多次滚动触发分页 API
    - 实现 fetch_details_parallel(notes, config, top_k=20) → List[RawSearchResult]：并行获取 top_k 条结果的详情页，使用 asyncio.Semaphore(3) 控制最多 3 个 tab 并发，每个 tab 独立注册 API 响应拦截器
    - 实现 fetch_detail(url, config, retry=0) → Optional[ResourceDetail]：进入详情页提取内容和评论，支持最多 2 次重试；优先使用拦截到的 API 数据，回退到 __INITIAL_STATE__ 或 DOM 提取
    - 实现 extract_image_content(image_urls, max_images=3) → List[str]：[TODO 接口预留] MVP 阶段返回空列表，未来调用多模态 LLM 提取前 3 张图片内容
    - 实现 _intercept_response(response)：API 响应拦截回调，捕获搜索结果、详情和评论的 JSON 数据
    - 实现 _intercept_request(route, request)：请求拦截回调，捕获签名 headers（x-s, x-t, x-s-common）
    - 实现 _extract_content_from_page(page) → str：从详情页提取正文，三级回退：API JSON → __INITIAL_STATE__ → DOM
    - 实现 ensure_logged_in(page, config) → bool：检查登录状态，失效时提示重新登录
    - 实现 close()：关闭浏览器实例，保存 Cookie，释放资源
    - 从 __INITIAL_STATE__ 或 API JSON 中提取图片 URL 列表（image_list 字段），保存到 RawSearchResult.image_urls
    - 页面操作间添加 1~3 秒随机延迟
    - 同平台连续请求间隔不少于 2 秒
    - 页面加载超时 15 秒自动终止
    - 浏览器启动失败记录错误日志返回空结果
    - 验证码/反爬页面检测：记录警告日志，跳过该平台
    - 搜索结果页多次滚动加载（至少 5 次），触发分页 API 请求
    - 详情页自动检测并关闭登录弹窗
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 6.1, 6.2, 6.3, 6.4, 6.5.1-6.5.15, 10.1, 10.2, 10.3, 10.4, 11.1, 11.2, 11.3, 11.4_

  - [ ]* 7.2 编写属性测试：操作延迟范围
    - **Property 2: 操作延迟范围**
    - 验证生成的随机延迟值在 [1.0, 3.0] 秒闭区间内
    - **Validates: Requirements 1.5**

  - [ ]* 7.3 编写属性测试：同平台请求间隔
    - **Property 10: 同平台请求间隔**
    - 验证同一平台连续两次请求的时间戳之差不小于 2.0 秒
    - **Validates: Requirements 6.3**

- [ ] 8. 实现 SearchOrchestrator 搜索调度器
  - [x] 8.1 创建 `src/specialists/search_orchestrator.py`，实现 SearchOrchestrator 类
    - 实现 search_all_platforms(query, platforms, timeout, top_k) → List[SearchResult]
    - 实现 expand_keywords(query) → List[str]：[TODO 接口预留] MVP 阶段返回 [query]，未来使用 LLM 扩展 2-3 个相关关键词
    - 使用 asyncio.gather 并发搜索所有指定平台
    - 集成 SearchCache：搜索前检查缓存，搜索后写入缓存
    - 集成 QualityScorer：对原始结果批量评分，高赞评论质量作为评分维度之一
    - 将 ScoredResult 转换为 SearchResult（包含 quality_score、recommendation_reason、engagement_metrics、comments_preview）
    - 按 quality_score 降序排序，返回前 top_k 条
    - 小红书平台：搜索全量获取 ~60 条，详情获取 top 20，使用并行 3 tab 加速
    - 小红书平台使用特殊排序权重：评论数×5 + 收藏数×2 + 点赞数×1
    - 对标题包含广告关键词的结果降权
    - 总超时 60 秒（搜索阶段）+ 120 秒（详情阶段），超时后返回已获取的部分结果
    - 单平台失败时跳过继续处理其余平台
    - _Requirements: 2.1, 2.2, 2.3, 2.5, 2.6, 5.1, 5.2, 5.3, 5.4, 6.5.14, 6.5.15, 10.1, 10.2, 10.4, 12.1, 12.2, 12.3_

  - [ ]* 8.2 编写属性测试：平台过滤正确性
    - **Property 3: 平台过滤正确性**
    - 验证指定 platforms 后返回结果的 platform 字段仅包含指定平台
    - **Validates: Requirements 2.3**

  - [ ]* 8.3 编写属性测试：平台故障容错
    - **Property 4: 平台故障容错**
    - 模拟部分平台失败，验证不抛出异常且返回未失败平台的结果
    - **Validates: Requirements 2.5**

  - [ ]* 8.4 编写属性测试：原始结果到 SearchResult 转换
    - **Property 8: 原始结果到 SearchResult 转换**
    - 验证转换后包含所有必需字段，quality_score 和 recommendation_reason 正确传递
    - **Validates: Requirements 4.4**

  - [ ]* 8.5 编写属性测试：搜索结果排序与截断
    - **Property 9: 搜索结果排序与截断**
    - 验证结果列表长度不超过 top_k，quality_score 按非递增顺序排列
    - **Validates: Requirements 5.1, 5.3**

- [ ] 9. 实现 BrowserResourceSearcher 主入口并替换原有 ResourceSearcher
  - [x] 9.1 在 `src/specialists/resource_searcher.py` 中实现 BrowserResourceSearcher 类
    - 保持与原 ResourceSearcher.search(query, platforms) 相同的方法签名
    - 在 search() 中使用 asyncio.run() 包装异步调用，保持同步接口
    - 默认搜索全部 6 个平台，支持用户指定平台列表
    - 默认返回前 10 条结果
    - _Requirements: 5.4, 5.5_

  - [x] 9.2 更新 `src/agents/orchestrator.py` 和 `src/agents/planner.py` 中的导入，将 ResourceSearcher 替换为 BrowserResourceSearcher
    - 确保调用代码无需修改（接口兼容）
    - _Requirements: 5.5_

- [x] 10. Checkpoint - 确保核心搜索流程测试通过
  - 确保所有测试通过，如有问题请询问用户。

- [ ] 11. UI 资源卡片增强
  - [x] 11.1 修改 `src/ui/renderer.py` 中的 render_resource_card 函数
    - 当 quality_score > 0 时，在卡片中显示质量评分（星级或分数形式）
    - 当 recommendation_reason 非空时，显示推荐理由文本
    - 当 engagement_metrics 非空时，显示关键互动指标（点赞数、评论数等）
    - 对不包含新字段的旧格式 SearchResult 保持正常渲染
    - _Requirements: 9.1, 9.2, 9.3, 9.4_

  - [ ]* 11.2 编写属性测试：资源卡片渲染新字段
    - **Property 14: 资源卡片渲染新字段**
    - 验证包含 quality_score、recommendation_reason、engagement_metrics 的 SearchResult 渲染的 HTML 包含对应数据
    - **Validates: Requirements 9.1, 9.2, 9.3**

  - [ ]* 11.3 编写属性测试：资源卡片向后兼容
    - **Property 15: 资源卡片向后兼容**
    - 验证仅包含原始字段的 SearchResult 渲染不抛出异常
    - **Validates: Requirements 9.4**

- [x] 12. 最终 Checkpoint - 确保所有测试通过
  - 确保所有测试通过，如有问题请询问用户。

## Notes

- 标记 `*` 的子任务为可选，可跳过以加速 MVP 开发
- 每个任务引用了具体的需求编号，确保可追溯性
- 属性测试验证设计文档中的正确性属性，使用 hypothesis 库
- 测试文件：`tests/test_browser_agent_resource_search.py`（单元测试）、`tests/test_browser_agent_resource_search_properties.py`（属性测试）
- 运行测试命令：`venv\Scripts\python.exe -m pytest tests/test_browser_agent_resource_search.py -v`
