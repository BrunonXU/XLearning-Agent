# 需求文档：智能浏览器 Agent 资源搜索


# 简介


将现有的 `ResourceSearcher`（基于 httpx API 调用的传统爬虫）升级为智能浏览器 Agent。新系统使用真实浏览器（Playwright / browser-use）模拟人类浏览行为，在小红书、Bilibili、YouTube、GitHub、Google、微信公众号六大平台上搜索学习资源。通过 LLM 对内容质量进行多维度评估（互动指标、内容深度、评论质量、时效性），返回带有质量评分和推荐理由的排序资源列表。


## 术语表

- **Browser_Agent**: 基于 Playwright 或 browser-use 库的智能浏览器代理，能在真实浏览器中执行搜索、点击、阅读等操作
- **Quality_Scorer**: 使用 LLM 对搜索到的资源进行多维度质量评估的评分组件
- **Resource_Collector**: 负责从浏览器页面中提取结构化资源数据（标题、URL、互动指标、评论等）的数据采集组件
- **Search_Orchestrator**: 协调多平台搜索任务的调度器，管理并发搜索、超时控制和结果聚合
- **Quality_Score**: 0.0 到 1.0 之间的浮点数，表示资源的综合质量评分
- **Engagement_Metrics**: 互动指标，包括点赞数、收藏数、评论数、播放量等平台特定的用户互动数据
- **SearchResult**: 项目中已定义的资源搜索结果数据模型（`src/core/models.py`）
- **Platform_Config**: 每个平台的搜索配置，包括搜索 URL 模板、选择器、反检测策略等

## 需求

### 需求 1：浏览器 Agent 核心引擎

**用户故事：** 作为开发者，我希望系统使用真实浏览器进行资源搜索，以便绕过 API 限制并获取完整的页面内容。

#### 验收标准

1. THE Browser_Agent SHALL 使用 Playwright 启动真实的 Chromium 浏览器实例执行搜索任务
2. WHEN 收到搜索请求时，THE Browser_Agent SHALL 在浏览器中打开目标平台的搜索页面并输入搜索关键词
3. WHEN 搜索结果页面加载完成后，THE Browser_Agent SHALL 提取搜索结果列表中每条结果的标题、URL 和摘要信息
4. WHEN 需要获取详细内容时，THE Browser_Agent SHALL 点击进入具体帖子/视频页面，读取正文内容和评论区数据
5. THE Browser_Agent SHALL 在每次页面操作之间添加 1 至 3 秒的随机延迟以模拟人类浏览行为
6. IF 浏览器实例启动失败，THEN THE Browser_Agent SHALL 记录错误日志并返回空结果列表
7. IF 页面加载超过 15 秒未完成，THEN THE Browser_Agent SHALL 终止当前页面加载并跳过该页面

### 需求 2：多平台搜索支持

**用户故事：** 作为学习者，我希望系统能在小红书、Bilibili、YouTube、GitHub、Google、微信公众号六个平台上搜索资源，以便获取多元化的学习内容。

#### 验收标准

1. THE Search_Orchestrator SHALL 支持以下六个平台的搜索：小红书、Bilibili、YouTube、GitHub、Google、微信公众号
2. WHEN 用户未指定平台时，THE Search_Orchestrator SHALL 默认在全部六个平台上并发执行搜索
3. WHEN 用户指定了平台列表时，THE Search_Orchestrator SHALL 仅在指定的平台上执行搜索
4. THE Search_Orchestrator SHALL 为每个平台维护独立的 Platform_Config，包含搜索 URL 模板和页面元素选择器
5. IF 某个平台的搜索失败，THEN THE Search_Orchestrator SHALL 跳过该平台并继续处理其余平台的结果
6. THE Search_Orchestrator SHALL 在总超时时间 60 秒内完成所有平台的搜索，超时后返回已获取的部分结果

### 需求 3：LLM 驱动的内容质量评估

**用户故事：** 作为学习者，我希望系统能智能评估搜索到的资源质量，以便快速找到高质量的学习内容。

#### 验收标准

1. THE Quality_Scorer SHALL 使用 LLM 对每条搜索结果进行多维度质量评估
2. THE Quality_Scorer SHALL 评估以下四个维度：互动指标（点赞、收藏、评论数）、内容深度与实用性、评论质量、内容时效性
3. WHEN 一条资源的点赞数较低但评论区包含高质量技术讨论时，THE Quality_Scorer SHALL 给予该资源较高的 Quality_Score
4. THE Quality_Scorer SHALL 为每条资源生成一个 0.0 到 1.0 之间的 Quality_Score
5. THE Quality_Scorer SHALL 为每条资源生成一段中文推荐理由，说明该资源的优势和适用场景
6. WHEN 无法获取某个维度的数据时，THE Quality_Scorer SHALL 基于可用维度进行评估，并在推荐理由中注明缺失的维度

### 需求 4：资源数据采集与结构化

**用户故事：** 作为开发者，我希望从浏览器页面中提取结构化的资源数据，以便后续进行质量评估和展示。

#### 验收标准

1. THE Resource_Collector SHALL 从每个搜索结果页面中提取以下基础字段：标题、URL、平台名称、资源类型、描述
2. THE Resource_Collector SHALL 从详情页面中提取 Engagement_Metrics：点赞数、收藏数、评论数，以及平台特有指标（如 Bilibili 的播放量、GitHub 的 Star 数）
3. WHEN 进入详情页面时，THE Resource_Collector SHALL 提取评论区的前 10 条评论内容
4. THE Resource_Collector SHALL 将提取的数据转换为与现有 SearchResult 模型兼容的格式
5. IF 某个字段无法从页面中提取，THEN THE Resource_Collector SHALL 将该字段设为默认值（空字符串或 0）并继续处理

### 需求 5：搜索结果排序与返回

**用户故事：** 作为学习者，我希望搜索结果按质量评分排序，以便优先看到最有价值的学习资源。

#### 验收标准

1. THE Search_Orchestrator SHALL 将所有平台的搜索结果按 Quality_Score 从高到低排序后返回
2. THE Search_Orchestrator SHALL 默认返回排名前 10 条的搜索结果
3. WHEN 用户指定了返回数量时，THE Search_Orchestrator SHALL 返回指定数量的结果
4. THE Search_Orchestrator SHALL 返回的每条结果包含：标题、URL、平台、类型、描述、Quality_Score、推荐理由
5. THE Search_Orchestrator SHALL 保持与现有 `ResourceSearcher.search()` 方法相同的调用接口签名，确保 PlannerAgent 和 TutorAgent 无需修改调用代码

### 需求 6：反检测与稳定性

**用户故事：** 作为开发者，我希望浏览器 Agent 具备反检测能力和稳定性保障，以便长期可靠地运行搜索任务。

#### 验收标准

1. THE Browser_Agent SHALL 使用随机的 User-Agent 字符串和真实的浏览器指纹信息
2. THE Browser_Agent SHALL 支持 Cookie 持久化，在多次搜索之间保持登录状态
3. THE Browser_Agent SHALL 对同一平台的连续请求间隔不少于 2 秒
4. IF 平台返回验证码或反爬页面，THEN THE Browser_Agent SHALL 记录警告日志、跳过该平台并返回空结果
5. THE Browser_Agent SHALL 在搜索完成后正确关闭浏览器实例，释放系统资源

### 需求 7：搜索结果缓存

**用户故事：** 作为学习者，我希望相同的搜索请求能快速返回结果，以便减少等待时间和平台访问频率。

#### 验收标准

1. THE Search_Orchestrator SHALL 对搜索结果进行本地缓存，缓存键为搜索关键词与平台列表的组合
2. WHEN 缓存中存在未过期的搜索结果时，THE Search_Orchestrator SHALL 直接返回缓存结果而不执行浏览器搜索
3. THE Search_Orchestrator SHALL 将缓存有效期设为 1 小时
4. WHEN 缓存过期后，THE Search_Orchestrator SHALL 重新执行浏览器搜索并更新缓存

### 需求 8：扩展 SearchResult 数据模型

**用户故事：** 作为开发者，我希望 SearchResult 模型能承载质量评分和互动指标等新数据，以便 UI 层展示更丰富的资源信息。

#### 验收标准

1. THE SearchResult 模型 SHALL 新增以下可选字段：quality_score（float，默认 0.0）、recommendation_reason（str，默认空字符串）、engagement_metrics（dict，默认空字典）、comments_preview（list，默认空列表）
2. THE SearchResult 模型 SHALL 保持与现有代码的向后兼容性，新增字段均有默认值
3. THE SearchResult 的 to_dict 方法 SHALL 包含所有新增字段
4. THE SearchResult 的 from_dict 方法 SHALL 能正确解析包含或不包含新增字段的字典数据

### 需求 9：UI 资源卡片增强

**用户故事：** 作为学习者，我希望资源卡片能展示质量评分和推荐理由，以便直观了解每条资源的价值。

#### 验收标准

1. WHEN 资源包含 quality_score 时，THE render_resource_card 函数 SHALL 在卡片中显示质量评分（以星级或分数形式）
2. WHEN 资源包含 recommendation_reason 时，THE render_resource_card 函数 SHALL 在卡片中显示推荐理由文本
3. WHEN 资源包含 engagement_metrics 时，THE render_resource_card 函数 SHALL 在卡片中显示关键互动指标（点赞数、评论数等）
4. THE render_resource_card 函数 SHALL 对不包含新增字段的旧格式 SearchResult 保持正常渲染
