# 需求文档：搜索体验重设计

## 简介

对现有搜索功能进行全面升级，涵盖四大核心领域：两阶段漏斗筛选策略（互动数据初筛 + LLM 质量评估精筛）、搜索体验重设计（并发搜索、SSE 进度推送、跨平台统一排序 top 10）、搜索阶段详情提取（正文与评论在搜索流程中完成提取）、以及材料预览展示体系（本地文件原文展示、外部资源摘要浮窗）。系统的核心价值是 AI 帮用户粗筛高质量文章，通过提取正文和评论进行质量评估和推荐，最终输出跨平台统一排序的 top 10 高价值内容，节约用户时间。

## 术语表

- **Search_Orchestrator**: 搜索调度器，协调多平台并发搜索、两阶段漏斗筛选、缓存管理和结果聚合的后端模块（`src/specialists/search_orchestrator.py`）
- **Resource_Collector**: 资源提取器，从浏览器页面或拦截 API 中提取结构化数据的后端模块（`src/specialists/resource_collector.py`）
- **Browser_Agent**: 浏览器代理，基于 Playwright 执行搜索和页面交互的后端模块（`src/specialists/browser_agent.py`）
- **Search_Panel**: 搜索面板，前端搜索 UI 组件（`frontend/src/components/source-panel/SearchPanel.tsx`）
- **Source_Panel**: 资源面板，前端左侧资源管理区域（`frontend/src/components/source-panel/SourcePanel.tsx`）
- **Preview_Popup**: 预览浮窗，点击外部资源时弹出的摘要展示浮窗组件（新增）
- **Content_Viewer**: 内容查看器，在 Source_Panel 中展示本地文件原文的区域（新增）
- **Search_Session**: 搜索会话，一次搜索操作的完整生命周期，包含查询词、平台选择、搜索状态和结果
- **Engagement_Ranker**: 互动数据排序器，基于评论/点赞比例和标题关键词加权对搜索结果进行初筛排序的模块（新增）
- **Quality_Assessor**: 质量评估器，使用 LLM 对提取的正文和评论进行内容质量评估、评分和推荐理由生成的模块（新增）
- **SSE**: Server-Sent Events，服务端推送事件流，用于实时推送搜索阶段性进度状态
- **Pipeline_Executor**: 流水线执行器，负责详情提取与 LLM 评估的流水线并行调度，提取完一条立即送入评估队列（新增）

## 需求

### 需求 1：并发搜索与统一漏斗架构

**用户故事：** 作为用户，我希望各平台搜索独立并发执行，所有平台搜索完成后统一进入漏斗筛选，最终输出跨平台统一排序的 top 10 结果。

#### 验收标准

1. WHEN 用户发起多平台搜索请求, THE Search_Orchestrator SHALL 为每个平台创建独立的异步搜索任务并发执行
2. WHEN 所有平台搜索完成（或超时）, THE Search_Orchestrator SHALL 将各平台的搜索结果汇总后统一进入漏斗筛选流程
3. IF 某个平台搜索失败或超时, THEN THE Search_Orchestrator SHALL 使用其他已完成平台的结果继续进入漏斗筛选，并记录失败平台的错误信息
4. WHEN 用户在搜索进行中发起新的搜索请求, THE Search_Panel SHALL 取消当前所有进行中的搜索任务，并启动新的搜索
5. THE Search_Orchestrator SHALL 为每个平台独立维护搜索超时计时器，单平台超时时间为 45 秒
6. THE Search_Orchestrator SHALL 将最终的 top 10 结果（含摘要、评分、推荐理由、评论结论等完整数据）作为整体缓存，缓存键为 query + platforms 组合
7. WHEN 相同 query + platforms 组合的搜索请求在缓存有效期内再次发起, THE Search_Orchestrator SHALL 直接返回缓存的完整 top 10 结果，不重新执行漏斗筛选流程
8. WHEN 用户取消搜索, THE Search_Orchestrator SHALL 关闭所有正在使用的浏览器 tab 和浏览器实例，释放所有资源，防止资源泄漏


### 需求 2：SSE 阶段性进度推送

**用户故事：** 作为用户，我希望在搜索过程中看到系统当前正在做什么（搜索中、初筛中、提取中、评估中），而不是只看到一个空白等待，这样我能了解进度并保持耐心。

#### 验收标准

1. WHEN 搜索流程进入某个阶段, THE Search_Orchestrator SHALL 通过 SSE 推送对应的阶段性进度事件
2. THE SSE 进度事件 SHALL 包含 `stage` 字段，取值为以下枚举之一：`searching`、`filtering`、`extracting`、`evaluating`、`done`
3. WHEN 阶段为 `searching`, THE Search_Orchestrator SHALL 在进度事件中附带当前正在搜索的平台名称（如"正在搜索小红书..."）
4. WHEN 阶段为 `filtering`, THE Search_Orchestrator SHALL 在进度事件中附带已获取的原始结果总数（如"已获取 N 条，正在初筛..."）
5. WHEN 阶段为 `extracting`, THE Search_Orchestrator SHALL 在进度事件中附带提取进度数字（如"正在提取详情（3/15）..."），每完成一条提取即推送一次进度更新
6. WHEN 阶段为 `evaluating`, THE Search_Orchestrator SHALL 推送进度事件（如"AI 正在评估内容质量..."）
7. WHEN 阶段为 `done`, THE Search_Orchestrator SHALL 在进度事件中一次性返回最终的跨平台统一排序 top 10 结果列表
8. THE SSE `done` 事件的结果列表中每条结果 SHALL 包含以下字段：id、标题、URL、来源平台、AI 内容摘要、评论结论、互动指标、质量评分、推荐理由
9. WHEN Search_Panel 收到进度事件, THE Search_Panel SHALL 根据 `stage` 字段显示对应的中文状态文案
10. IF 搜索过程中发生错误, THEN THE Search_Orchestrator SHALL 通过 SSE 推送包含错误信息的 `error` 事件

### 需求 3：搜索结果展示与历史保留

**用户故事：** 作为用户，我希望搜索完成后看到跨平台统一排序的 top 10 结果列表，每条结果标注来源平台；每次搜索留下历史记录卡片，点击可展开回顾之前的搜索结果。

#### 验收标准

1. WHEN 搜索完成, THE Search_Panel SHALL 以统一列表形式展示跨平台排序的 top 10 结果，不按平台分组
2. THE Search_Panel SHALL 在每条结果项中显示来源平台标识（平台图标或文字标签）
3. WHEN 搜索完成, THE Search_Panel SHALL 将本次搜索保存为一条搜索历史记录卡片，卡片折叠显示在搜索面板中
4. THE 搜索历史记录卡片 SHALL 折叠态显示以下信息：搜索关键词（如"agent开发"）、搜索模式标签（"混合搜索"或具体平台图标列表如"📕📺"）、结果数量
5. WHEN 用户点击搜索历史记录卡片, THE Search_Panel SHALL 展开该卡片，覆盖当前搜索面板区域，展示该次搜索的完整 top 10 结果列表，左上角显示搜索时间（如"3月4日 14:32"）
6. WHEN 搜索历史记录卡片已展开, THE Search_Panel SHALL 提供收起按钮，点击后恢复折叠态
7. WHEN 用户发起新的搜索, THE Search_Panel SHALL 在搜索历史列表顶部新增一条记录，不清除之前的历史记录
8. THE Search_Panel SHALL 按时间倒序排列搜索历史记录（最新的在最上方）

### 需求 4：两阶段漏斗筛选 — 第一阶段互动数据初筛

**用户故事：** 作为用户，我希望系统在搜索阶段就能基于互动数据智能筛选出高价值文章，过滤掉低质量的流量贴和水文，让我看到的结果都是值得阅读的。

#### 验收标准

1. WHEN 所有平台搜索结果汇总后, THE Engagement_Ranker SHALL 对全部结果进行跨平台互动数据初筛排序
2. THE Engagement_Ranker SHALL 计算每条结果的评论数与点赞数比例作为核心排序指标（评论/点赞比例高的文章权重更高）
3. THE Engagement_Ranker SHALL 对标题包含以下关键词的文章给予额外加权：经验贴、面经、攻略、踩坑、总结、实战
4. THE Engagement_Ranker SHALL 从初筛排序后的结果中取 top 15 至 20 条进入第二阶段筛选
5. IF 汇总后的结果总数少于 20 条, THEN THE Engagement_Ranker SHALL 将全部结果传入第二阶段，不做截断


### 需求 5：两阶段漏斗筛选 — 第二阶段 LLM 质量评估

**用户故事：** 作为用户，我希望系统通过 AI 对初筛后的文章进行内容质量评估，识别出真正有价值的行业文章，过滤广告和水文，并给出质量评分和推荐理由。

#### 验收标准

1. WHEN 第一阶段初筛完成, THE Pipeline_Executor SHALL 对 top N 条结果并行提取正文内容和高赞评论（最多 10 条高赞评论，含评论文本、点赞数、作者）
2. WHEN 正文和评论提取完成, THE Quality_Assessor SHALL 将正文和评论内容提交给 LLM 进行内容质量评估
3. THE Quality_Assessor SHALL 基于以下标准评估内容质量：是否为行业内有效文章（而非广告、水文或纯引流内容）
4. THE Quality_Assessor SHALL 在单次 LLM 调用中同时完成以下四项任务：质量评分（1-10 分）、不超过 50 字的推荐理由、不超过 150 字的内容摘要、不超过 100 字的评论结论摘要（总结评论区的主要观点和情感倾向）
5. IF 正文内容少于 50 字, THEN THE Quality_Assessor SHALL 直接使用原文作为内容摘要，LLM 调用中仅生成质量评分、推荐理由和评论结论摘要
6. IF LLM 调用失败, THEN THE Quality_Assessor SHALL 使用正文前 150 字作为降级内容摘要，评论结论摘要置空，质量评分基于互动数据估算
7. THE Quality_Assessor SHALL 从评估结果中选出 top 10 条高质量结果作为最终输出
8. IF 某条结果的正文提取失败, THEN THE Quality_Assessor SHALL 基于标题、描述和互动数据进行降级评估，并在推荐理由中标注"正文未提取"
9. IF LLM 质量评估调用失败, THEN THE Search_Orchestrator SHALL 使用第一阶段的互动数据排序结果作为降级输出
10. THE Search_Orchestrator SHALL 将生成的摘要与质量评估结果一起缓存

### 需求 6：并行优化与流水线调度

**用户故事：** 作为用户，我希望搜索全流程尽可能快，系统应充分利用并行能力缩短等待时间。

#### 验收标准

1. WHEN 第二阶段开始提取详情, THE Pipeline_Executor SHALL 以最多 5 个并发浏览器 tab 并行提取正文和评论
2. WHEN 某条结果的详情提取完成, THE Pipeline_Executor SHALL 立即将该条结果送入 LLM 评估队列，不等待其他结果提取完成
3. THE Quality_Assessor SHALL 将待评估的结果批量打包（标题 + 正文摘要 + 评论）为一个 prompt 进行单次 LLM 调用，而非逐条单独调用
4. WHILE Quality_Assessor 等待凑批期间有新的提取结果到达, THE Quality_Assessor SHALL 将新结果加入当前批次（批次上限为 15 条），超过 3 秒未有新结果到达时立即发起 LLM 调用
5. WHILE 搜索阶段使用 API 拦截模式获取结果, THE Engagement_Ranker SHALL 边接收结果边实时计算互动数据排序，不等待滚动加载全部完成
6. IF 某条结果的详情提取超时（单条超时 30 秒）, THEN THE Pipeline_Executor SHALL 跳过该条并继续处理队列中的下一条

### 需求 7：小红书图片 URL 提取与缩略图展示

**用户故事：** 作为用户，我知道小红书很多核心信息在图片上，我希望系统能提取图片 URL 并在预览中展示缩略图，方便我快速浏览图片内容。

#### 验收标准

1. WHEN Resource_Collector 从小红书 API 拦截数据中提取搜索结果, THE Resource_Collector SHALL 同时提取笔记的图片 URL 列表（最多 9 张）
2. WHEN 第二阶段提取小红书笔记正文时, THE Pipeline_Executor SHALL 在提取结果中包含图片 URL 列表
3. WHEN Preview_Popup 展示小红书资源详情, THE Preview_Popup SHALL 以缩略图网格形式展示笔记图片
4. THE Preview_Popup SHALL 支持点击缩略图查看大图

### 需求 8：外部资源预览浮窗

**用户故事：** 作为用户，我点击外部资源（小红书、Google 等搜索结果）时，希望看到一个摘要浮窗，快速了解资源核心内容，而不是直接跳转到原始页面。

#### 验收标准

1. WHEN 用户点击外部资源类型的材料项, THE Preview_Popup SHALL 直接使用搜索阶段已获取的数据（正文摘要、评论结论、图片 URL、互动指标、质量评分、推荐理由）渲染浮窗，不发起额外 API 请求
2. THE Preview_Popup SHALL 包含以下内容区域：资源标题、URL、来源平台标识、AI 生成的内容摘要、评论结论摘要、图片缩略图（如有）、互动指标（点赞/收藏/评论数）、质量评分、推荐理由
3. THE Preview_Popup SHALL 提供"查看完整信息"按钮，点击后在新标签页中打开资源原始 URL
4. THE Preview_Popup SHALL 提供"刷新"按钮，点击后调用 `/api/resource/refresh` 端点重新获取并更新浮窗中的数据
5. THE Preview_Popup SHALL 提供关闭按钮，点击后关闭浮窗
6. WHILE Preview_Popup 正在执行刷新操作, THE Preview_Popup SHALL 显示加载骨架屏
7. IF 刷新操作失败, THEN THE Preview_Popup SHALL 显示错误提示并提供"重试"按钮
8. THE Preview_Popup SHALL 支持键盘操作：Escape 键关闭浮窗


### 需求 9：本地文件内容查看器

**用户故事：** 作为用户，我上传的本地文件（PDF、Markdown 等）点击后应该直接在左侧资源区域展示原文内容，类似 NotebookLM 的体验。

#### 验收标准

1. WHEN 用户点击本地文件类型的材料项, THE Content_Viewer SHALL 在 Source_Panel 中展示该文件的原文内容
2. THE Content_Viewer SHALL 支持 Markdown 格式文件的渲染展示（标题、列表、代码块、链接等）
3. THE Content_Viewer SHALL 支持 PDF 文件的文本内容展示
4. THE Content_Viewer SHALL 提供返回材料列表的导航按钮
5. WHILE 文件内容正在加载, THE Content_Viewer SHALL 显示加载指示器
6. IF 文件内容加载失败, THEN THE Content_Viewer SHALL 显示错误提示并提供"重试"按钮

### 需求 10：详情刷新 API 端点

**用户故事：** 作为前端开发者，我需要一个 API 端点来手动刷新某条搜索结果的详情信息（正文、评论、图片 URL），以便在缓存过期或提取失败时重新获取。

#### 验收标准

1. THE Search_Orchestrator SHALL 提供 POST `/api/resource/refresh` 端点，接受资源 URL 和平台类型作为参数
2. WHEN 收到详情刷新请求, THE Search_Orchestrator SHALL 重新提取该资源的正文内容、评论列表和图片 URL 列表，并调用 Quality_Assessor 重新评估质量
3. THE Search_Orchestrator SHALL 返回包含以下字段的 JSON 响应：正文内容、AI 内容摘要、评论列表、评论结论摘要、图片 URL 列表、互动指标、质量评分、推荐理由
4. THE Search_Orchestrator SHALL 在 90 秒内完成详情刷新并返回响应
5. IF 刷新超时, THEN THE Search_Orchestrator SHALL 返回 HTTP 408 状态码和超时错误信息
6. IF 资源 URL 无法访问, THEN THE Search_Orchestrator SHALL 返回 HTTP 422 状态码和错误描述
7. WHEN 刷新成功, THE Search_Orchestrator SHALL 更新缓存中该资源的详情数据

