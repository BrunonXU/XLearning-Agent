# 需求文档：NotebookLM 风格前端重设计

## 简介

将 XLearning-Agent 的前端体验向 Google NotebookLM 的交互范式靠拢。NotebookLM 的核心设计哲学是：**以"笔记本/来源"为中心，而非以"对话"为中心**。用户先上传学习材料（PDF、URL、文本），系统将其组织为一个"学习笔记本"，AI 的所有回答都锚定在这些来源上，并提供可追溯的引用。

本 spec 聚焦于前端 UI/UX 的重新设计，将现有的 Streamlit 三栏 Tab 布局改造为 NotebookLM 风格的三区域布局：左侧来源面板、中间 AI 对话区、右侧笔记/输出区。同时保留并整合现有的 AI 学习辅导功能（Planner、Tutor、ResourceSearcher、ProgressTracker）。

---

## 术语表

- **Notebook**: 一个学习会话的容器，对应现有的 Session，包含来源、对话历史和笔记
- **Source**: 用户上传或添加的学习材料，包括 PDF、GitHub URL、网页链接、纯文本
- **Source_Panel**: 左侧来源管理面板，展示当前 Notebook 中所有 Source 的列表
- **Chat_Area**: 中间 AI 对话区域，用于与 Tutor/Planner 进行交互
- **Notes_Panel**: 右侧笔记与输出面板，展示学习计划、资源卡片、进度等结构化内容
- **Grounding_Badge**: 每条 AI 回复下方的来源引用标记，显示回答依据了哪些 Source
- **Audio_Overview**: 类 NotebookLM 的"音频概览"功能的文字版替代——自动生成的学习摘要卡片
- **Study_Guide**: 由 AI 自动生成的结构化学习指南，包含关键概念、学习路径、常见问题
- **Tutor**: 辅导 Agent（`src/agents/tutor.py`），负责基于 Source 回答学习问题
- **Planner**: 规划 Agent（`src/agents/planner.py`），负责生成结构化学习计划
- **Orchestrator**: 编排器（`src/agents/orchestrator.py`），负责意图识别和 Agent 调度
- **ResourceSearcher**: 资源搜索专家模块，封装多平台搜索能力
- **ProgressTracker**: 每日学习进度追踪机制

---

## 需求

### 需求 1：三区域布局（NotebookLM 核心布局）

**用户故事：** 作为学习者，我希望界面分为来源管理、AI 对话、笔记输出三个清晰区域，以便我能同时管理学习材料、与 AI 交互并查看结构化输出。

#### 验收标准

1. THE UI SHALL 采用三列布局：左侧 Source_Panel（宽度约 20%）、中间 Chat_Area（宽度约 50%）、右侧 Notes_Panel（宽度约 30%）
2. WHEN 用户在移动端或窄屏（宽度 < 768px）访问时，THE UI SHALL 将三列折叠为单列垂直布局，Source_Panel 和 Notes_Panel 以可折叠抽屉形式呈现
3. THE Source_Panel SHALL 始终显示当前 Notebook 中所有已添加 Source 的列表，每个 Source 显示图标、名称和状态（处理中/就绪/错误）
4. THE Chat_Area SHALL 占据页面中央，包含消息历史和底部输入框，输入框始终固定在底部可见
5. THE Notes_Panel SHALL 根据当前上下文动态展示内容：无计划时显示 Study_Guide 生成入口，有计划时显示学习进度和资源卡片
6. WHEN 用户点击 Source_Panel 中的某个 Source 时，THE UI SHALL 高亮显示该 Source 并在 Chat_Area 中显示该 Source 的摘要信息

### 需求 2：来源管理面板（Source Panel）

**用户故事：** 作为学习者，我希望能在左侧面板中集中管理所有学习材料，像 NotebookLM 一样清晰地看到"我的学习来源"，以便我知道 AI 的回答基于哪些材料。

#### 验收标准

1. THE Source_Panel SHALL 在顶部提供"+ 添加来源"按钮，点击后展开上传选项：上传 PDF、粘贴 URL（GitHub/网页）、输入纯文本
2. WHEN 用户添加 Source 时，THE Source_Panel SHALL 显示处理进度指示器（解析中 → 分块中 → 就绪），处理完成后显示绿色就绪状态
3. THE Source_Panel SHALL 为每个 Source 显示：类型图标（📄 PDF / 🔗 URL / 📝 文本）、名称（截断至 20 字符）、就绪状态标记
4. WHEN 用户将鼠标悬停在 Source 上时，THE Source_Panel SHALL 显示操作菜单：查看详情、从 Notebook 移除
5. IF 用户尝试移除 Source 时，THEN THE Source_Panel SHALL 显示确认对话框，提示该操作将影响基于此 Source 的 AI 回答
6. THE Source_Panel SHALL 在底部显示当前 Notebook 的统计信息：来源数量、总知识切片数（chunks）
7. WHEN Notebook 中没有任何 Source 时，THE Source_Panel SHALL 显示引导提示："添加来源，让 AI 基于你的材料回答"

### 需求 3：AI 对话区（Chat Area）增强

**用户故事：** 作为学习者，我希望 AI 的每条回复都清晰标注引用了哪些来源，像 NotebookLM 一样让我知道答案的依据，以便我能信任并深入追溯。

#### 验收标准

1. THE Chat_Area SHALL 在每条 AI 回复下方显示 Grounding_Badge，列出本次回复引用的 Source 名称和片段
2. WHEN 用户点击 Grounding_Badge 中的某个来源引用时，THE Chat_Area SHALL 在弹出层中显示原始引用片段的完整内容
3. THE Chat_Area SHALL 支持在输入框中使用 "@" 符号触发 Source 选择器，允许用户指定针对某个特定 Source 提问
4. WHEN AI 正在生成回复时，THE Chat_Area SHALL 显示流式输出效果（逐字/逐句出现），并在消息底部显示"正在思考..."状态
5. THE Chat_Area SHALL 在消息列表顶部提供"建议问题"区域，显示 3-5 个基于当前 Source 内容自动生成的推荐问题
6. WHEN 用户的 Notebook 中没有 Source 时，THE Chat_Area SHALL 在输入框上方显示提示横幅："添加来源后，AI 将基于你的材料回答"
7. THE Chat_Area 的输入框 SHALL 支持多行输入，按 Shift+Enter 换行，按 Enter 发送

### 需求 4：笔记与输出面板（Notes Panel）

**用户故事：** 作为学习者，我希望右侧面板能像 NotebookLM 的"笔记"功能一样，自动整理 AI 生成的学习计划、资源推荐和关键概念，以便我不需要手动整理学习成果。

#### 验收标准

1. THE Notes_Panel SHALL 包含以下可切换的内容区块：Study_Guide（学习指南）、Learning_Plan（学习计划与进度）、Resources（资源卡片）
2. WHEN 用户首次进入 Notebook 且已添加 Source 时，THE Notes_Panel SHALL 显示"生成学习指南"按钮，点击后调用 Planner 生成 Study_Guide
3. THE Study_Guide SHALL 包含：关键概念列表（5-10 个）、常见问题（FAQ，3-5 条）、推荐学习路径概述
4. WHEN Planner 生成学习计划后，THE Notes_Panel SHALL 自动切换到 Learning_Plan 视图，以交互式时间线展示每日学习进度
5. THE Learning_Plan 视图 SHALL 允许用户点击每天的节点查看详情，并提供"标记完成"按钮
6. THE Resources 视图 SHALL 以卡片形式展示 ResourceSearcher 搜索到的学习资源，每张卡片包含平台图标、标题、简介和可点击链接
7. THE Notes_Panel SHALL 在每个内容区块右上角提供"导出"按钮，支持将内容导出为 Markdown 格式

### 需求 5：Notebook 首页（类 NotebookLM 的笔记本列表）

**用户故事：** 作为学习者，我希望应用首页像 NotebookLM 一样展示我的"学习笔记本"列表，每个笔记本代表一个学习主题，以便我能快速切换和管理多个学习项目。

#### 验收标准

1. THE UI 首页 SHALL 以卡片网格形式展示所有历史 Notebook，每张卡片显示：标题、来源数量、最后访问时间、学习进度百分比
2. THE 首页 SHALL 在卡片网格顶部提供醒目的"+ 新建笔记本"按钮
3. WHEN 用户点击"+ 新建笔记本"时，THE UI SHALL 显示新建对话框，允许用户输入笔记本名称并立即添加第一个 Source
4. THE 首页卡片 SHALL 支持悬停时显示操作菜单：打开、重命名、删除
5. IF 用户没有任何 Notebook 时，THEN THE 首页 SHALL 显示空状态引导页，包含三个快速开始选项：上传 PDF、粘贴 GitHub URL、直接提问
6. THE 首页 SHALL 支持按最近访问时间对 Notebook 卡片进行排序

### 需求 6：Audio Overview 的文字替代——自动摘要卡片

**用户故事：** 作为学习者，我希望系统能像 NotebookLM 的 Audio Overview 一样，在我添加来源后自动生成一个"内容速览"卡片，让我快速了解材料的核心内容，以便我决定如何深入学习。

#### 验收标准

1. WHEN 用户成功添加并处理完一个 Source 后，THE UI SHALL 在 Notes_Panel 顶部自动显示该 Source 的"内容速览"卡片
2. THE 内容速览卡片 SHALL 包含：主题摘要（2-3 句话）、关键词标签（5-8 个）、内容类型标识（论文/教程/代码库/文章）
3. THE Tutor SHALL 在用户添加 Source 后自动生成内容速览，无需用户主动触发
4. WHEN 内容速览生成完成时，THE UI SHALL 在 Chat_Area 中同步显示一条系统消息，提示用户可以开始基于该来源提问
5. IF Source 处理失败，THEN THE UI SHALL 在内容速览卡片位置显示错误状态和重试按钮

### 需求 7：建议问题（Suggested Questions）

**用户故事：** 作为学习者，我希望系统像 NotebookLM 一样在我添加来源后自动推荐几个值得探索的问题，以便我快速进入深度学习状态，不需要自己想问什么。

#### 验收标准

1. WHEN 用户添加 Source 并生成内容速览后，THE Tutor SHALL 基于 Source 内容自动生成 3-5 个推荐问题
2. THE Chat_Area SHALL 在消息列表上方以可点击的"问题芯片"（chip）形式展示推荐问题
3. WHEN 用户点击某个推荐问题芯片时，THE Chat_Area SHALL 将该问题填入输入框并自动发送
4. THE 推荐问题 SHALL 覆盖不同难度层次：理解类（"什么是..."）、应用类（"如何..."）、分析类（"为什么..."）
5. WHEN 用户已经开始对话后，THE Chat_Area SHALL 隐藏推荐问题芯片，避免干扰对话流程
6. THE 推荐问题 SHALL 在每次添加新 Source 后重新生成，反映最新的 Source 内容

### 需求 8：视觉风格与主题（NotebookLM 美学）

**用户故事：** 作为学习者，我希望界面视觉风格参考 NotebookLM 的简洁、专注、学术感设计，以便我在使用时感受到专业的学习氛围。

#### 验收标准

1. THE UI SHALL 采用以白色/浅灰为主的背景色系，主强调色使用深蓝（`#1A73E8`）或保留现有橙色（`#F97316`），避免过多彩色干扰
2. THE UI SHALL 使用无衬线字体，正文字号不小于 14px，确保长时间阅读的舒适度
3. THE Source_Panel 和 Notes_Panel SHALL 使用轻微的阴影和圆角卡片设计，与 Chat_Area 形成视觉层次区分
4. THE UI SHALL 提供深色模式（Dark Mode）切换选项，深色模式下背景色使用 `#1C1C1E`，文字使用 `#F5F5F7`
5. WHEN AI 正在处理请求时，THE UI SHALL 显示优雅的加载动画（脉冲点或进度条），而非简单的"请稍候"文字
6. THE UI 的所有交互元素（按钮、卡片、输入框）SHALL 具有一致的圆角半径（8px）和过渡动画（150ms ease）

### 需求 9：键盘快捷键与无障碍访问

**用户故事：** 作为高效学习者，我希望能通过键盘快捷键快速操作界面，以便我不需要频繁切换鼠标和键盘。

#### 验收标准

1. THE UI SHALL 支持以下键盘快捷键：`Ctrl/Cmd + K` 聚焦到输入框、`Ctrl/Cmd + N` 新建 Notebook、`Escape` 关闭弹出层
2. THE UI 的所有交互元素 SHALL 具有可见的键盘焦点指示器（focus ring）
3. THE UI 的所有图标按钮 SHALL 提供 `aria-label` 属性，确保屏幕阅读器可以正确描述按钮功能
4. THE Source_Panel 中的 Source 列表 SHALL 支持键盘导航（上下箭头键切换，Enter 键选中）

### 需求 10：响应式布局与 Streamlit 兼容性

**用户故事：** 作为开发者，我希望新的 NotebookLM 风格布局能在现有 Streamlit 框架内实现，以便不需要迁移到其他前端框架。

#### 验收标准

1. THE UI SHALL 在 Streamlit 框架内通过 `st.columns`、`st.markdown(unsafe_allow_html=True)` 和自定义 CSS 实现三区域布局
2. THE UI 的自定义 CSS SHALL 通过 `st.markdown` 注入，不依赖外部 CSS 文件，确保部署简单性
3. WHEN Streamlit 版本升级时，THE UI 的核心布局 SHALL 不依赖已废弃的 API（如 `st.experimental_rerun` 应迁移至 `st.rerun`）
4. THE UI 的所有自定义 HTML 组件 SHALL 通过 `streamlit.components.v1.html` 渲染，避免 XSS 风险
5. THE UI SHALL 在 Streamlit Cloud 和本地环境中均能正常运行，不依赖本地文件系统以外的外部服务
