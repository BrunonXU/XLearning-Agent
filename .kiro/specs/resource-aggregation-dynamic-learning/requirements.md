# 需求文档：资源聚合 + 动态学习路径

## 简介

将 XLearning-Agent 的核心价值从 Quiz/Report 展示流转向「资源聚合 + 动态学习路径」。用户上传 PDF 或粘贴 GitHub URL 后，系统生成以「天」为最小单位的专业学习路径，并从 6 大平台（Bilibili、YouTube、Google、GitHub、小红书、微信公众号）搜索真实学习资源。每天的学习内容以资源卡片形式展示，用户点击「完成」按钮标记当天学习完成，进度条线性推进。Tutor 每次回复末尾附带「📎 参考来源」列表。完全移除 Quiz/测验功能。

## 术语表

- **ResourceSearcher**: 资源搜索专家模块（`src/specialists/resource_searcher.py`），封装 6 大平台搜索能力
- **Planner**: 规划 Agent（`src/agents/planner.py`），负责生成以天为单位的结构化学习计划
- **Tutor**: 辅导 Agent（`src/agents/tutor.py`），负责自由对话模式下的学习辅导，每次回复附带参考来源
- **Orchestrator**: 编排器（`src/agents/orchestrator.py`），负责意图识别和 Agent 调度
- **DayProgress**: 每日学习进度数据模型，包含 day_number、title、completed 三个字段
- **LearningPlan**: 学习计划数据模型，以 Day（Day 1, Day 2...）为最小时间单位组织
- **ProgressTracker**: 会话级每日学习进度追踪机制，维护线性进度条（已完成天数 / 总天数）
- **SearchResult**: 资源搜索结果数据模型，包含标题、URL、来源平台、类型等字段
- **ResourceCard**: 资源卡片，每日学习大纲的展开内容，展示该天关联的学习资源详情

## 需求

### 需求 1：多源资源搜索专家模块

**用户故事：** 作为学习者，我希望系统能从多个平台搜索真实的学习资源，以便我获得高质量、多样化的学习材料。

#### 验收标准

1. THE ResourceSearcher SHALL 封装对 Bilibili、YouTube、Google、GitHub、小红书、微信公众号 六个平台的搜索能力，并以统一的 SearchResult 列表返回结果
2. WHEN Planner 生成学习计划时，THE Planner SHALL 对每天的学习主题调用 ResourceSearcher 搜索资源，并将结果填入该天的 `resources` 字段
3. WHEN 用户在 Tutor 对话中请求资源推荐时，THE Tutor SHALL 调用 ResourceSearcher 搜索并返回相关资源
4. IF ResourceSearcher 对某个平台的搜索请求失败，THEN THE ResourceSearcher SHALL 跳过该平台并返回其余平台的搜索结果，同时在日志中记录失败原因
5. THE SearchResult SHALL 包含以下字段：标题（title）、链接（url）、来源平台（platform）、资源类型（type）、简要描述（description）
6. WHEN ResourceSearcher 收到搜索关键词时，THE ResourceSearcher SHALL 在 10 秒内返回搜索结果

### 需求 2：专业学习路径生成（按天组织）

**用户故事：** 作为初学者，我希望上传 PDF 或粘贴 GitHub URL 后，系统能生成一份以天为单位、包含真实资源的专业学习路径，以便我有清晰的每日学习方向。

#### 验收标准

1. WHEN 用户提供 PDF 或 GitHub URL 时，THE Planner SHALL 生成以 Day（Day 1, Day 2...）为最小时间单位的结构化学习计划，每天包含学习主题和对应的真实学习资源
2. THE Planner SHALL 为每天的学习主题至少关联 2 个来自不同平台的学习资源
3. THE LearningPlan 的 `resources` 字段 SHALL 包含真实可访问的 URL，而非占位符或泛化描述
4. WHEN 学习计划生成完成时，THE Planner SHALL 以结构化 JSON 格式输出计划，包含 days 列表，每天包含 day_number、title、resources 字段
5. IF ResourceSearcher 未能为某天的主题找到资源，THEN THE Planner SHALL 在该天的 resources 中标注"暂无推荐资源"并继续生成计划的其余部分

### 需求 3：每日线性进度追踪

**用户故事：** 作为学习者，我希望系统以每日线性进度条的形式追踪我的学习进度，点击「完成」即可标记当天学习完成，简单直观。

#### 验收标准

1. THE ProgressTracker SHALL 维护一个 DayProgress 列表，每个 DayProgress 包含 day_number（天数编号）、title（当天学习主题）、completed（是否完成）三个字段
2. WHEN 用户点击某天的「完成」按钮时，THE ProgressTracker SHALL 将对应 DayProgress 的 completed 标记为 True
3. WHEN 用户询问学习进度时，THE Tutor SHALL 基于 ProgressTracker 的数据返回已完成天数、总天数和完成百分比
4. THE UI SHALL 显示线性进度条，进度值为已完成天数除以总天数
5. THE ProgressTracker SHALL 将进度数据持久化到当前会话的 session 存储中，以便页面刷新后进度不丢失
6. WHEN 用户开始新的会话时，THE ProgressTracker SHALL 初始化为空白状态

### 需求 4：动态学习大纲调整

**用户故事：** 作为学习者，我希望系统能根据我的学习进度和反馈动态调整学习大纲，以便学习路径始终贴合我的实际水平。

#### 验收标准

1. WHEN 用户完成当天学习后，THE Tutor SHALL 主动推荐下一天的学习内容和资源
2. WHEN 用户表示某个知识点太难或太简单时，THE Planner SHALL 调整该天所在内容的深度或跳过该内容
3. WHEN 用户在对话中提出新的学习兴趣点时，THE Planner SHALL 将新兴趣点融入现有学习计划并搜索对应资源
4. THE Orchestrator SHALL 在检测到用户进度变化时，将更新后的进度上下文传递给 Planner 和 Tutor
5. WHILE 用户处于学习会话中，THE Tutor SHALL 基于当前进度上下文提供与未完成天数相关的回答

### 需求 5：Tutor 回复附带参考来源

**用户故事：** 作为学习者，我希望 Tutor 每次回复末尾都附带参考来源列表，以便我了解信息的出处并深入学习。

#### 验收标准

1. THE Tutor SHALL 在每次回复末尾附加「📎 参考来源」区块，列出本次回复所引用的信息来源
2. WHEN Tutor 引用了 PDF 内容时，THE Tutor SHALL 在参考来源中标注 PDF 文件名和相关章节
3. WHEN Tutor 调用了 ResourceSearcher 时，THE Tutor SHALL 在参考来源中列出所使用的搜索平台和搜索关键词
4. WHEN Tutor 引用了 RAG 检索结果时，THE Tutor SHALL 在参考来源中标注检索到的文档片段来源
5. IF Tutor 的回复完全基于自身知识而未引用外部来源，THEN THE Tutor SHALL 在参考来源中标注「基于 AI 通用知识」

### 需求 6：资源搜索结果的序列化与反序列化

**用户故事：** 作为开发者，我希望资源搜索结果能正确地序列化和反序列化，以便在会话存储和 Agent 间传递时数据不丢失。

#### 验收标准

1. THE SearchResult SHALL 支持序列化为 JSON 格式和从 JSON 格式反序列化
2. FOR ALL 有效的 SearchResult 对象，序列化后再反序列化 SHALL 产生与原始对象等价的结果（round-trip 属性）
3. THE LearningDay 的 resources 字段 SHALL 支持 `List[Union[str, SearchResult]]`，以兼容旧数据格式
4. WHEN 反序列化遇到无效 JSON 数据时，THE SearchResult 解析器 SHALL 返回描述性错误信息而非抛出未处理异常

### 需求 7：UI 主流程重构（资源卡片 + 每日进度）

**用户故事：** 作为学习者，我希望 UI 界面以资源卡片和每日进度条为核心体验，以便我能高效地使用系统。

#### 验收标准

1. THE UI SHALL 在学习计划展示中以天为单位列出每日学习大纲，每天显示 day_number、title 和关联的资源卡片
2. THE UI SHALL 为每天的学习大纲提供「完成」按钮，点击后标记该天为已完成
3. THE UI SHALL 在页面顶部显示线性进度条，展示已完成天数占总天数的比例
4. WHEN 用户点击某天时，THE UI SHALL 展开该天的资源卡片列表，每张卡片包含资源标题、来源平台标识、简要描述和可点击的链接
5. THE UI SHALL 在 Study 页面提供「搜索更多资源」的交互入口，允许用户针对当天主题主动搜索资源
6. THE UI 的主流程 SHALL 为两步骤：Plan（学习路径）| Study（学习 + 资源探索），完全移除 Quiz 相关入口
7. THE UI SHALL 不包含任何 Quiz、测验、自测相关的入口、按钮或标签页
