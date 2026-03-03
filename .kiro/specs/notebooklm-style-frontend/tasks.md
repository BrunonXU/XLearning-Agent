# 实现任务：NotebookLM 风格前端重设计

## 任务列表

- [x] 1. 前端项目脚手架与设计系统
  - [x] 1.1 初始化 React + TypeScript + Vite 项目，配置 Tailwind CSS
  - [x] 1.2 在 tailwind.config.ts 中配置颜色 token、字体、圆角、过渡规范
  - [x] 1.3 创建通用 UI 原子组件：Button、Badge、Modal、Spinner、ResizablePanel
  - [x] 1.4 实现全局 TypeScript 类型定义（types/index.ts）
  - [x] 1.5 配置 React Router，设置首页路由和工作区路由 `/workspace/:planId`

- [x] 2. 静态 UI Shell（无后端逻辑，纯布局与样式）
  - [x] 2.1 实现顶部导航栏（56px，Logo + 规划名称 + 设置图标 + 用户头像）
  - [x] 2.2 实现三列可拖拽布局（左 20% / 中 50% / 右 30%，1px 分割线，最小宽度限制）
  - [x] 2.3 实现左侧材料面板静态 UI（面板标题、上传/搜索 Tab、材料列表占位、搜索结果占位）
  - [x] 2.4 实现中间对话区静态 UI（建议问题区、消息气泡样式、输入框固定底部）
  - [x] 2.5 实现右侧 Studio 面板静态 UI（今日任务区、工具卡片 2 列网格、内容库 Tab、底部状态栏）
  - [x] 2.6 实现首页学习规划列表静态 UI（精选规划横向滚动、规划卡片网格、新建弹窗）
  - [x] 2.7 实现深色模式切换（`class="dark"` 切换，所有颜色 token 正确响应）
  - [x] 2.8 对照设计文档视觉验收清单逐项验收（17 项全部通过）

- [x] 3. Zustand 全局状态管理
  - [x] 3.1 实现 chatStore（messages、isStreaming、suggestedQuestions 及对应 actions）
  - [x] 3.2 实现 sourceStore（materials、searchResults、platformSearchStatus 及对应 actions）
  - [x] 3.3 实现 studioStore（currentDay、allDays、generatedContents、notes 及对应 actions），配置 persist 中间件
  - [x] 3.4 实现 planStore（plans、currentPlanId 及对应 actions），配置 persist 中间件
  - [x] 3.5 为 studioStore.completeDay 编写属性测试（Property 2、3）：验证 currentDay 始终指向第一个未完成 Day，完成后进度单调递增

- [x] 4. FastAPI 后端基础框架
  - [x] 4.1 创建 `backend/` 目录，初始化 FastAPI 应用（main.py），配置 CORS
  - [x] 4.2 实现 SessionContext 懒加载机制，集成现有 TutorAgent、ProgressTracker、Orchestrator
  - [x] 4.3 实现 `GET /api/plans`、`POST /api/plans`、`PUT /api/plans/{id}`、`DELETE /api/plans/{id}` 端点
  - [x] 4.4 实现 `GET /api/session/{plan_id}` 端点（恢复会话状态）
  - [x] 4.5 编写 FastAPI 端点单元测试（请求/响应格式、HTTP 状态码）

- [x] 5. 学习材料面板功能接入
  - [x] 5.1 实现文件上传功能：`POST /api/upload`，支持 PDF 拖拽上传和 GitHub URL 粘贴
  - [x] 5.2 实现上传进度状态轮询（parsing → chunking → ready），前端 MaterialItem 显示对应状态动画
  - [x] 5.3 实现材料点击联动：点击材料 → 调用 `GET /api/material/{id}/summary` → 对话区插入摘要系统消息
  - [x] 5.4 实现材料移除功能（确认对话框 + sourceStore.removeMaterial）
  - [x] 5.5 为 MaterialItem 编写属性测试（Property 5）：验证所有 PlatformType 值都能渲染对应图标

- [x] 6. 资源搜索功能接入
  - [x] 6.1 实现 `POST /api/search` 端点，集成 ResourceSearcher + QualityScorer，按 quality_score 降序排列
  - [x] 6.2 实现前端 SearchPanel：关键词输入 + 平台选择 + 触发搜索
  - [x] 6.3 实现每平台独立搜索进度显示（platformSearchStatus），搜索超时（>15s）显示"搜索超时"
  - [x] 6.4 实现 SearchResultItem 渲染（平台图标、标题、摘要、⭐ x.x/10 评分、推荐理由、勾选框）
  - [x] 6.5 实现"加入学习材料"按钮（显示已选数量，点击后添加到材料列表）
  - [x] 6.6 为搜索排序编写属性测试（Property 1）：验证返回结果始终按 quality_score 降序排列
  - [x] 6.7 为 SearchResultItem 编写属性测试（Property 6）：验证评分显示格式为 `⭐ x.x/10`

- [x] 7. AI 对话区功能接入
  - [x] 7.1 实现 `useSSE` hook：建立 SSE 连接，处理 chunk/sources/done 事件，支持自动重连（最多 3 次）
  - [x] 7.2 实现 `POST /api/chat` SSE 端点，集成 TutorAgent 流式输出，响应 chunk/sources/done 事件
  - [x] 7.3 实现对话历史窗口截断（最近 6 轮 = 12 条消息），前端维护并传给后端
  - [x] 7.4 实现流式输出渲染（逐字出现 + 末尾闪烁光标），完成后渲染来源引用标签
  - [x] 7.5 实现来源引用点击弹窗（显示原始引用片段完整内容）
  - [x] 7.6 实现建议问题区域（后端异步生成 3-5 个推荐问题，点击自动填入并发送）
  - [x] 7.7 实现无材料提示横幅（材料列表为空时显示）
  - [x] 7.8 为 SSE 流式输出编写属性测试（Property 7）：验证非空回复产生 ≥2 个 chunk 事件
  - [x] 7.9 为对话历史窗口编写属性测试（Property 8）：验证 history 长度不超过 12 条

- [x] 8. Studio 面板功能接入
  - [x] 8.1 实现 `GET /api/studio/{type}` 端点（learning-plan / study-guide / flashcards / quiz / progress-report），集成 Planner/TutorAgent
  - [x] 8.2 实现今日任务区块：从 studioStore.currentDay 读取数据，任务勾选 + 完成 Day 按钮
  - [x] 8.3 实现 `PUT /api/plan/day/{day_id}/complete` 端点，集成 ProgressTracker.mark_day_completed（幂等）
  - [x] 8.4 实现工具卡片点击触发内容生成（调用 /api/studio/{type}，显示加载状态）
  - [x] 8.5 实现首次添加材料时自动触发生成"学习指南"
  - [x] 8.6 实现内容库 Tab（AI 生成按时间倒序 + 导出 Markdown；我的笔记按编辑时间倒序 + 新建/编辑）
  - [x] 8.7 实现笔记编辑器（Markdown 支持 + "AI 整理"按钮调用 Tutor）
  - [x] 8.8 实现笔记 CRUD 端点：`POST /api/notes`、`PUT /api/notes/{id}`、`DELETE /api/notes/{id}`
  - [x] 8.9 为 ProgressTracker.mark_day_completed 编写属性测试（Property 3）：验证进度单调递增
  - [x] 8.10 为会话状态持久化编写属性测试（Property 4）：验证 save/load 往返一致

- [x] 9. 开发者工具（Dev Mode）
  - [x] 9.1 实现开发者模式开关（studioStore.devMode），仅开发者模式下显示开发者工具卡片
  - [x] 9.2 实现 LangGraph 模式切换（studioStore.langGraphEnabled），切换后使用 orchestrator_langgraph.py
  - [x] 9.3 实现 Agent Trace 卡片（展示工具调用、耗时、Token 消耗）
  - [x] 9.4 实现 LangSmith 状态指示器（底部常驻 + 开发者卡片，✅/❌ + 点击跳转 trace 链接）

- [x] 10. 首页与规划管理
  - [x] 10.1 实现首页规划卡片网格（封面色块、标题、来源数、最后访问时间）
  - [x] 10.2 实现精选学习规划横向滚动区域
  - [x] 10.3 实现新建规划弹窗（三种创建方式：上传 PDF / 粘贴链接 / 直接描述主题）
  - [x] 10.4 实现规划卡片 hover 操作菜单（打开、重命名、删除）
  - [x] 10.5 实现空状态引导页（无规划时显示）
  - [x] 10.6 实现网格/列表视图切换

- [x] 11. 键盘快捷键与无障碍
  - [x] 11.1 实现 `useKeyboard` hook（Ctrl/Cmd+K 聚焦输入框、Ctrl/Cmd+N 新建规划、Escape 关闭弹窗）
  - [x] 11.2 为 MaterialList 实现键盘导航（↑/↓ 切换，Enter 选中，Delete 触发移除确认）
  - [x] 11.3 为所有图标按钮添加 `aria-label` 属性
  - [x] 11.4 确保所有交互元素有 `focus-visible:ring-2 focus-visible:ring-primary` 焦点指示器

- [x] 12. 会话恢复与错误处理
  - [x] 12.1 实现页面刷新时从 `GET /api/session/{plan_id}` 恢复对话历史和材料列表
  - [x] 12.2 实现 SSE 断线重连逻辑（最多 3 次，失败后降级为普通 HTTP）
  - [x] 12.3 实现各错误场景的前端处理（PDF 解析失败、LLM 不可用、笔记保存冲突）
  - [x] 12.4 实现加载骨架屏（内容加载时显示 animate-pulse 占位块）
