# XLearning-Agent 验收测试文档

> **更新日期**：2026-02-28
> **版本**：v0.3.0
> **自动化测试**：191 passed, 0 failed (1 pre-existing teardown error in test_rag.py)
> **前置条件**：`.env` 中已配置 `DASHSCOPE_API_KEY`

---

## 如何使用

- 每项前有 `[ ]`，通过后改为 `[x]`
- 遇到问题在对应项下方记录
- 全部通过 = 可以演示

---

## 0. 启动

```powershell
venv\Scripts\python.exe -m streamlit run app.py
# 或
.\scripts\run_ui.ps1
```

- [ ] 应用正常启动，浏览器打开 `http://localhost:8501`
- [ ] 无 import 报错、无 TOML 解析错误
- [ ] 首页显示欢迎语和输入框

---

## 1. 核心流程 — Plan | Study | Resources

### 1.1 计划生成（PlannerAgent）

**A：纯文本输入**
1. 首页输入 `Python 异步编程` → 进入工作区
2. 在聊天框输入"生成计划"或等待自动引导

- [ ] 计划按 Day 为单位生成（Day 1, Day 2...）
- [ ] 计划内容与输入主题相关（包含 async/await/asyncio 等术语）
- [ ] 右侧 Plan 面板显示每日大纲，前 3 天展开
- [ ] 顶部显示线性进度条（0/N 天）
- [ ] 每天有「完成」按钮

**B：PDF 输入**
1. 新对话 → 上传 PDF → 生成计划

- [ ] 计划内容与 PDF 文档相关
- [ ] 聊天区显示 PDF 处理信息（页数、切片数）

**C：GitHub URL**
1. 新对话 → 输入 `https://github.com/langchain-ai/langchain`

- [ ] 系统识别 GitHub URL，调用 RepoAnalyzer
- [ ] 计划包含 LangChain 相关术语

### 1.2 学习对话（TutorAgent）

1. 进入 Study Tab
2. 发送：`什么是 Self-Attention？`
3. 发送：`它和 RNN 有什么区别？`

- [ ] Tutor 理解"它"指 Self-Attention（多轮上下文保持）
- [ ] 回答末尾有「📎 参考来源」区块
- [ ] 流式输出（逐字出现，非一次性加载）

### 1.3 资源搜索

1. 在聊天框输入：`搜索资源` 或 `找资源`

- [ ] Orchestrator 正确识别 search_resource 意图
- [ ] 返回资源卡片（标题、平台标识、描述、链接）

2. 切换到 Resources Tab

- [ ] 显示已搜索的资源列表
- [ ] 有「搜索更多资源」入口

### 1.4 进度追踪

1. 在 Plan 面板点击某天的「完成」按钮

- [ ] 进度条更新（如 1/7 天）
- [ ] 该天标记为已完成

---

## 2. 浏览器 Agent 资源搜索（browser-agent-resource-search）

### 2.1 数据模型

- [ ] SearchResult 包含新字段：quality_score, recommendation_reason, engagement_metrics, comments_preview
- [ ] 旧格式数据（不含新字段）仍可正常解析

### 2.2 搜索调度器

- [ ] SearchOrchestrator 支持多平台并发搜索
- [ ] 缓存命中时不重复调用浏览器
- [ ] 广告标题被降权排序
- [ ] 单平台失败不影响其他平台

### 2.3 UI 资源卡片增强

- [ ] quality_score > 0 时显示评分徽章（⭐）
- [ ] 有推荐理由显示（💡）
- [ ] 有互动指标（👍 点赞 / ⭐ 收藏 / 💬 评论数）
- [ ] 有热门评论折叠面板
- [ ] 不含新字段的旧资源卡片正常渲染（向后兼容）

### 2.4 自动化测试覆盖

```powershell
venv\Scripts\python.exe -m pytest tests/test_browser_agent_resource_search.py -v
```

- [ ] 101 个测试全部通过
- [ ] 覆盖：数据模型、平台配置、缓存、采集器、评分器、调度器、端到端集成

---

## 3. UI 布局修复（ui-layout-fixes）

### 3.1 侧边栏宽度

- [ ] 侧边栏宽度约 235px（不再是 420px）
- [ ] 内容不截断，Logo/按钮/历史列表正常显示
- [ ] 折叠按钮为箭头 ◀，折叠/展开正常

### 3.2 Stepper 导航

- [ ] 顶部 Tab 栏：Plan | Study | Resources（3 个 Tab）
- [ ] 开发模式下额外显示 Trace Tab
- [ ] 当前 Tab 下方有橙色指示线
- [ ] 无重复 Stepper 显示
- [ ] 无 Quiz/测验 相关入口

### 3.3 嵌套列修复

- [ ] Plan 面板中按钮垂直排列（无 st.columns 嵌套）
- [ ] 无 StreamlitAPIException 报错

### 3.4 Brain 区域

- [ ] 右侧面板底部始终显示「🧠 记忆与知识」区域
- [ ] 显示上传的上下文信息和生成的产物

### 3.5 双列布局

- [ ] 聊天区与面板之间有灰色竖线分隔
- [ ] 左右两列独立滚动
- [ ] 列宽比例约 3:2

### 3.6 自动化测试覆盖

```powershell
venv\Scripts\python.exe -m pytest tests/test_ui_bugfix_exploration.py tests/test_ui_bugfix_preservation.py -v
```

- [ ] 6 个缺陷探索测试全部通过
- [ ] 16 个保留性测试全部通过

---

## 4. 资源聚合与动态学习（resource-aggregation-dynamic-learning）

### 4.1 Quiz 移除确认

- [ ] UI 中无 Quiz/测验/自测 相关入口、按钮、标签页
- [ ] 意图路由中无 start_quiz
- [ ] 代码中无 QuizMaker/ValidatorAgent 残留引用

### 4.2 意图路由

- [ ] 优先级：create_plan > ask_question > search_resource
- [ ] 输入"帮我整理要点" → Tutor 回答（不触发计划生成）
- [ ] 输入"搜索资源" → 触发资源搜索

### 4.3 自动化测试覆盖

```powershell
venv\Scripts\python.exe -m pytest tests/test_resource_aggregation.py tests/test_resource_aggregation_properties.py -v
```

- [ ] 单元测试和属性测试全部通过

---

## 5. 全量自动化测试

```powershell
venv\Scripts\python.exe -m pytest tests/ -v --tb=short
```

- [ ] 191 passed
- [ ] 0 failed
- [ ] 1 pre-existing error (test_rag.py teardown — Windows 文件锁，与功能无关)

---

## 6. 验收结果汇总

| 类别 | 项数 | 通过 | 失败 | 备注 |
|------|------|------|------|------|
| 启动 | 3 | | | |
| 核心流程 | 18 | | | |
| 浏览器 Agent 搜索 | 12 | | | |
| UI 布局修复 | 12 | | | |
| 资源聚合与动态学习 | 5 | | | |
| 全量测试 | 3 | | | |
| **合计** | **53** | | | |

### 阻断性问题
```
（无则留空）
```

### 非阻断性问题
```
（无则留空）
```

---

## 7. Spec 交付清单

| Spec | 必需任务 | 完成 | 测试数 | 状态 |
|------|----------|------|--------|------|
| resource-aggregation-dynamic-learning | 8 大任务 | 8/8 | ~40 | ✅ 全部完成 |
| browser-agent-resource-search | 14 必需任务 | 14/14 | 101 | ✅ 全部完成 |
| ui-layout-fixes | 4 大任务 | 4/4 | 22 | ✅ 全部完成 |

**总计**：191 个自动化测试通过，3 个 Spec 全部交付。
