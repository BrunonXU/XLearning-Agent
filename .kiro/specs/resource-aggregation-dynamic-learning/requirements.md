# 需求文档：资源聚合 + 动态学习路径

## 简介

将 XLearning-Agent 的核心价值从 Quiz/Report 展示流转向「资源聚合 + 动态学习路径」。用户上传 PDF 或粘贴 GitHub URL 后，系统生成专业学习路径并搜索真实学习资源（YouTube、Bilibili、微信公众号、小红书、编程网站等），在会话过程中记忆学习进度并动态调整学习大纲。Quiz/测验降级为可选功能，不再作为主流程。

## 术语表

- **ResourceSearcher**: 新增的资源搜索专家模块（`src/specialists/resource_searcher.py`），封装多源搜索能力，可被 Planner 和 Tutor 调用
- **Planner**: 规划 Agent（`src/agents/planner.py`），负责生成结构化学习计划
- **Tutor**: 辅导 Agent（`src/agents/tutor.py`），负责自由对话模式下的学习辅导
- **Orchestrator**: 编排器（`src/agents/orchestrator.py`），负责意图识别和 Agent 调度
- **LearningPhase**: 学习阶段数据模型，包含阶段名称、时长、知识点和资源列表
- **LearningPlan**: 学习计划数据模型，包含多个 LearningPhase
- **ProgressTracker**: 会话级学习进度追踪机制，记录用户在各阶段/知识点的完成状态
- **SearchResult**: 资源搜索结果数据模型，包含标题、URL、来源平台、类型等字段

## 需求

### 需求 1：多源资源搜索专家模块

**用户故事：** 作为学习者，我希望系统能从多个平台搜索真实的学习资源，以便我获得高质量、多样化的学习材料。

#### 验收标准

1. THE ResourceSearcher SHALL 封装对 Bilibili、YouTube、Google、GitHub 四个平台的搜索能力，并以统一的 SearchResult 列表返回结果
2. WHEN Planner 生成学习计划时，THE Planner SHALL 对每个 LearningPhase 的 topics 调用 ResourceSearcher 搜索资源，并将结果填入该阶段的 `resources` 字段
3. WHEN 用户在 Tutor 对话中请求资源推荐时，THE Tutor SHALL 调用 ResourceSearcher 搜索并返回相关资源
4. IF ResourceSearcher 对某个平台的搜索请求失败，THEN THE ResourceSearcher SHALL 跳过该平台并返回其余平台的搜索结果，同时在日志中记录失败原因
5. THE SearchResult SHALL 包含以下字段：标题（title）、链接（url）、来源平台（platform）、资源类型（type）、简要描述（description）
6. WHEN ResourceSearcher 收到搜索关键词时，THE ResourceSearcher SHALL 在 10 秒内返回搜索结果

### 需求 2：专业学习路径生成

**用户故事：** 作为初学者，我希望上传 PDF 或粘贴 GitHub URL 后，系统能生成一份包含真实资源的专业学习路径，以便我有清晰的学习方向。

#### 验收标准

1. WHEN 用户提供 PDF 或 GitHub URL 时，THE Planner SHALL 生成包含 3-5 个阶段的结构化学习计划，每个阶段包含具体知识点和对应的真实学习资源
2. THE Planner SHALL 为每个 LearningPhase 的每个 topic 至少关联 2 个来自不同平台的学习资源
3. THE LearningPlan 的 `resources` 字段 SHALL 包含真实可访问的 URL，而非占位符或泛化描述
4. WHEN 学习计划生成完成时，THE Planner SHALL 以结构化 JSON 格式输出计划，包含 phases、topics、resources 三层嵌套结构
5. IF ResourceSearcher 未能为某个 topic 找到资源，THEN THE Planner SHALL 在该 topic 的 resources 中标注"暂无推荐资源"并继续生成计划的其余部分

### 需求 3：会话级学习进度追踪

**用户故事：** 作为学习者，我希望系统在对话过程中记住我的学习进度，以便我不需要重复告知已学内容。

#### 验收标准

1. THE ProgressTracker SHALL 在每次会话中维护用户在各 LearningPhase 和 topic 上的完成状态
2. WHEN 用户在对话中表示已完成某个知识点或阶段时，THE ProgressTracker SHALL 将对应的 topic 或 LearningPhase 标记为已完成
3. WHEN 用户询问学习进度时，THE Tutor SHALL 基于 ProgressTracker 的数据返回当前完成百分比和未完成的知识点列表
4. THE ProgressTracker SHALL 将进度数据持久化到当前会话的 session 存储中，以便页面刷新后进度不丢失
5. WHEN 用户开始新的会话时，THE ProgressTracker SHALL 初始化为空白状态

### 需求 4：动态学习大纲调整

**用户故事：** 作为学习者，我希望系统能根据我的学习进度和反馈动态调整学习大纲，以便学习路径始终贴合我的实际水平。

#### 验收标准

1. WHEN 用户完成一个 LearningPhase 后，THE Tutor SHALL 主动推荐下一阶段的学习内容和资源
2. WHEN 用户表示某个知识点太难或太简单时，THE Planner SHALL 调整该知识点所在阶段的深度或跳过该知识点
3. WHEN 用户在对话中提出新的学习兴趣点时，THE Planner SHALL 将新兴趣点融入现有学习计划并搜索对应资源
4. THE Orchestrator SHALL 在检测到用户进度变化时，将更新后的进度上下文传递给 Planner 和 Tutor
5. WHILE 用户处于学习会话中，THE Tutor SHALL 基于当前进度上下文提供与未完成知识点相关的回答

### 需求 5：Quiz/测验功能降级为可选

**用户故事：** 作为学习者，我希望测验功能是可选的而非强制的，以便我可以专注于学习路径和资源探索。

#### 验收标准

1. THE UI SHALL 将 Quiz 标签页从主流程三步骤（Plan | Study | Quiz）中移除，改为在 Study 页面内提供可选入口
2. WHEN 用户主动请求测验时，THE Orchestrator SHALL 调用现有的 QuizMaker 生成测验
3. THE Orchestrator SHALL 将默认意图路由优先级调整为：生成计划 > 自由学习 > 资源搜索 > 测验
4. THE UI 的主流程 SHALL 变更为两步骤：Plan（学习路径）| Study（学习 + 资源探索）

### 需求 6：资源搜索结果的序列化与反序列化

**用户故事：** 作为开发者，我希望资源搜索结果能正确地序列化和反序列化，以便在会话存储和 Agent 间传递时数据不丢失。

#### 验收标准

1. THE SearchResult SHALL 支持序列化为 JSON 格式和从 JSON 格式反序列化
2. FOR ALL 有效的 SearchResult 对象，序列化后再反序列化 SHALL 产生与原始对象等价的结果（round-trip 属性）
3. THE LearningPhase 的 resources 字段 SHALL 从 `List[str]` 扩展为 `List[Union[str, SearchResult]]`，以兼容旧数据格式
4. WHEN 反序列化遇到无效 JSON 数据时，THE SearchResult 解析器 SHALL 返回描述性错误信息而非抛出未处理异常

### 需求 7：UI 主流程重构

**用户故事：** 作为学习者，我希望 UI 界面突出学习路径和资源探索的核心体验，以便我能高效地使用系统。

#### 验收标准

1. THE UI SHALL 在学习计划展示中为每个阶段显示关联的资源列表，每个资源包含标题、来源平台标识和可点击的链接
2. THE UI SHALL 在 Study 页面提供"搜索更多资源"的交互入口，允许用户针对当前知识点主动搜索资源
3. THE UI SHALL 在学习计划展示中显示各阶段的完成进度（已完成/总数）
4. WHEN 用户点击某个阶段时，THE UI SHALL 展开该阶段的详细知识点列表和对应资源
5. THE UI SHALL 在 Study 页面底部提供可折叠的"可选：自测一下"入口，链接到 Quiz 功能
