# XLearning-Agent 改进清单 (TODO)

> **创建日期**：2026-02-10
> **最后更新**：2026-02-23
> **目标**：修复核心断路点，达到面试可演示水平
> **预计总工时**：5-7 天集中开发

---

## 总览：优先级分层

| 优先级 | 类别 | 预计工时 | 影响 |
|--------|------|---------|------|
| **P0** | 致命断路 - 演示翻车级 | 1-2 天 | 不修就废 |
| **P1** | 体验断裂 - 用户困惑级 | 2-3 天 | 面试扣分 |
| **P2** | 面试加分 - 简历关键词级 | 2-3 天 | 锦上添花 |
| **P3** | 锦上添花 - 专业度级 | 1-2 天 | 有余力再做 |

---

## 最新变更快照（2026-02-23）

> 说明：本节记录最近一次状态更新。

- ✅ P0-1~P0-4 全部代码实现完成（待端到端验收）
- ✅ P1-1~P1-3 全部代码实现完成（待端到端验收）
- ✅ P2-1~P2-4 全部代码实现完成（P2-1 UI 切换开关待接通）
- ✅ BF-1~BF-10 全部 Bug Fix 完成
- ✅ UI 3-Tab 重构完成（6 阶段 Stepper → 3 个可点击 Tab）
- ✅ UI 布局 5 项 Bugfix 已落地（侧边栏宽度、Stepper 定位、嵌套列、Brain 面板、拖拽 JS）
- ⬜ 端到端验收尚未执行（docs/acceptance_test.md 中 58 项待跑）
- ⬜ P3 锦上添花全部未开始

### 当前阶段：Day 10+ — 资源聚合 + 动态学习路径转型

> Quiz/Report 流程降级为可选，核心价值转向「多源资源聚合 + 动态学习路径」。
> 详细需求见 `.kiro/specs/resource-aggregation-dynamic-learning/requirements.md`

- [ ] 新增 ResourceSearcher 专家模块（`src/specialists/resource_searcher.py`）
- [ ] Planner 集成 ResourceSearcher，生成带真实资源的学习路径
- [ ] Tutor 集成 ResourceSearcher，对话中推荐资源
- [ ] 新增 ProgressTracker 会话级进度追踪
- [ ] 动态学习大纲调整（根据进度/反馈调整计划）
- [ ] UI 主流程从 3-Tab（Plan|Study|Quiz）简化为 2-Tab（Plan|Study）
- [ ] Quiz 降级为 Study 页面内可选入口
- [ ] 端到端验收：参照 `docs/acceptance_test.md` 逐项测试
- [ ] 验证 LangSmith 全链路追踪是否完整
- [ ] 完成 3 分钟演示脚本与计时演练
- [ ] 更新 README 中的开发计划表

---

## UI 当前排障清单（2026-02-11）

> **职责**：仅 UI 布局、样式、交互逻辑；参考 docs/ui_mockups.md 预期效果图。

### UI-BLOCKER-1. 启动命令环境不稳定 ✅
- **现象**：终端中执行 `streamlit run app.py` 直接报 `CommandNotFoundException`
- **根因**：当前 PowerShell 会话未正确激活 venv，PATH 中没有 `streamlit`
- **建议固定命令**：`venv\\Scripts\\python.exe -m streamlit run app.py`
- [x] 有 check_startup.py 启动前自检
- [x] 在 README 增加 Windows 启动命令（免激活）说明
- [x] 增加 `scripts/run_ui.ps1` 一键启动脚本

### UI-BLOCKER-2. Streamlit 配置文件容错与回归 ✅
- **现象**：历史上出现过 `hh[theme]` 导致 TOML 解析失败
- **文件**：`.streamlit/config.toml`
- [x] 保持 `[theme]` / `[server]` 配置最小化
- [x] 保留 `check_startup.py` 作为启动前自检

### UI-FIX-1. Stepper 显示与兼容性收敛 ✅
- [x] Stepper 固定吸顶，单次输出确保 DOM 正确
- [x] 校准侧边栏下的 margin-left
- [x] 补充截图回归指南：`docs/screenshots/README.md`

### UI-FIX-2. 聊天气泡渲染安全与可读性 ✅
- [x] 内置 _markdown_to_html() 转换器
- [x] 用户消息纯文本转义，避免 XSS
- [x] 增加 `tests/test_markdown_renderer.py` 回归测试

### UI-FIX-3. 首页交互统一（ChatGPT 风格）✅
- [x] 主输入框放最上，大而宽；PDF 收起到 expander；6 个快捷示例在下方
- [x] .home-input-wrap 白底、max-width: 1040px

### UI-FIX-4. 布局与分隔线 ✅
- [x] 侧边栏固定，隐藏拖拽把手和滚动条
- [x] 双列 2px 灰色分隔线
- [x] JS 注入实现拖拽调整宽度

### UI-FIX-5. 右侧面板阶段化展示 ✅
- [x] 新增 `render_plan_panel()` 与 `render_study_panel()`
- [x] layout 中 Plan/Study 阶段改为调用二者

### UI-FIX-6. 侧边栏宽度修正 ✅（Spec Bugfix）
- [x] `--sidebar-width` 从 420px 改为 294px

### UI-FIX-7. Stepper 定位修正 ✅（Spec Bugfix）
- [x] `.stepper-fixed-wrap` top 从 0 改为 48px
- [x] `.stepper-btn-row` 完全隐藏

### UI-FIX-8. 嵌套列异常修正 ✅（Spec Bugfix）
- [x] `render_plan_panel()` 中移除嵌套 `st.columns`

### UI-FIX-9. Brain 面板缺失修正 ✅（Spec Bugfix）
- [x] `render_workspace_view()` 中添加 `render_brain_tab()` 调用

### UI-FIX-10. 拖拽 JS 选择器修正 ✅（Spec Bugfix）
- [x] 排除 `.stepper-btn-row` 内部的水平块

---

## 下一步安排（UI/UX 职责范围）

> **参考**：`docs/ui_mockups.md` 预期效果图

| 优先级 | 任务 | 预计 | 状态 |
|--------|------|------|------|
| **1** | UI-BLOCKER-1 收尾 | 0.5h | ✅ 完成 |
| **2** | UI-FIX-5 右侧面板阶段化 | 1-2h | ✅ 完成 |
| **3** | UI 布局 Spec Bugfix（5 项） | 1h | ✅ 完成（代码已改，Spec 测试待跑） |
| **4** | 端到端验收 | 1-2h | ⬜ 未开始 |
| **5** | 引导 Banner 动作分发完善 | 1h | ⬜ 待验收确认 |
| **6** | 完成庆祝页视觉校准 | 0.5h | ⬜ 待验收确认 |
| **7** | 侧边栏增强（版本号 + LangSmith 状态） | 0.5h | ⬜ 待验收确认 |
| **8** | 聊天气泡细节（证据来源折叠区） | 0.5h | ⬜ 待验收确认 |
| **9** | 配色与视觉一致性 | 0.5h | ⬜ 待验收确认 |

---

## 验收办法（用户操作指引）

> **说明**：详细验收步骤见 `docs/acceptance_test.md`（58 项）。
> 以下为快速验收 checklist。

### 快速验收 Checklist

- [ ] 启动正常（免激活 venv 或 PS1 脚本）
- [ ] 首页显示欢迎语 + 输入区 + 快捷示例
- [ ] PDF 上传 → 处理成功 → 生成计划包含 PDF 关键术语
- [ ] GitHub URL → 识别并分析仓库
- [ ] 纯文本输入 → 生成差异化计划
- [ ] 多轮对话 → Tutor 理解指代词
- [ ] 流式输出 → 逐字出现
- [ ] 测验 → 题目出现 + 评分正确
- [ ] 报告 → 包含真实正确率和薄弱知识点
- [ ] 庆祝页 → 三指标卡片 + 出口按钮
- [ ] 全流程 < 3 分钟（不含 LLM 等待）

---

## P0 - 致命断路（必须最先修复）✅ 全部完成

### P0-1. 修复 Planner 硬编码计划 ✅
- **文件**: `src/agents/planner.py` → `_parse_plan()`
- **已完成**：Prompt 改为 JSON 输出 + `_parse_plan()` 三层防御
- [x] 修改 `_parse_plan()` 解析 LLM 输出
- [x] 修改 Prompt 为 JSON 格式输出
- [ ] 测试 3 种不同输入（PDF/URL/文本），验证计划差异化（待跑验收）

### P0-2. 连通 Report UI 与后端 ✅
- **文件**: `src/ui/renderer.py` + `src/ui/logic.py`
- **已完成**：新增 `handle_generate_report()`
- [x] 新增 `handle_generate_report()` 函数
- [x] 连接 UI 按钮到后端
- [ ] 报告包含 quiz_accuracy、weak_topics 等真实数据（待跑验收）

### P0-3. Quiz 数据同步 ✅
- **文件**: `src/ui/logic.py`
- **已完成**：统一两个入口
- [x] 重写 `handle_generate_quiz()` 调用真实后端
- [x] 统一 quiz 数据格式
- [ ] 测试两个入口生成的 quiz 是否一致（待跑验收）

### P0-4. 修复 Tutor History 未注入 LLM ✅
- **文件**: `src/agents/tutor.py` → `_handle_free_mode()`
- **已完成**：最近 6 轮历史拼入 prompt
- [x] 将 history 拼入 prompt
- [ ] 测试多轮对话上下文理解（待跑验收）

---

## P1 - 体验断裂修复 ✅ 全部完成

### P1-1. 自动化引导流程 ✅
- [x] 重写 `_render_action_banner()` 分发真实后端动作
- [x] PDF 上传后自动提示生成计划
- [x] Stepper 自动推进
- [ ] 测试全流程端到端（待跑验收）

### P1-2. Quiz 入口统一 ✅
- [x] Chat quiz 结果写入 session
- [x] Quiz Tab 读取 session quiz 数据
- [x] action banner 添加"开始测验"按钮

### P1-3. 学习闭环 - 完成仪式感 ✅
- [x] 定义完成条件判断逻辑
- [x] 渲染完成卡片
- [x] Stepper 全绿 ✓
- [x] 提供"下载报告"和"新课程"按钮

---

## P2 - 面试加分项 ✅ 代码全部完成

### P2-1. LangGraph 版 Orchestrator ✅
- **文件**: `src/agents/orchestrator_langgraph.py`（356 行）
- [x] 创建 LangGraph 版本文件
- [x] 实现 StateGraph + 三个 Node
- [x] 条件边路由
- [ ] UI 切换开关接通后端（侧边栏已预留 checkbox）
- [ ] 对比测试（待跑验收）

### P2-2. GitHub API 真实调用 ✅
- **文件**: `src/specialists/repo_analyzer.py`
- [x] 实现 GitHub API 调用
- [x] 获取 README + languages
- [x] 降级处理
- [ ] 导入 RAG 自动链路（待验收）

### P2-3. LLM-based 意图识别 ✅
- **文件**: `src/agents/orchestrator.py` → `_detect_intent()`
- [x] LLM 意图分类 Prompt
- [x] Fallback 策略
- [x] 测试边界用例（Day 7-8 验收通过）

### P2-4. Tutor 流式输出 ✅
- **文件**: `src/agents/tutor.py` → `stream_response()`
- [x] 实现真正的 stream_response
- [x] UI 端逐步更新
- [x] 测试流畅度（Day 7-8 验收通过）

---

## Bug Fixes (Day 7-8) ✅ 全部完成

| 编号 | 问题 | 文件 | 状态 |
|------|------|------|------|
| BF-1 | LLM API 超时 | `providers/tongyi.py` | ✅ |
| BF-2 | RAG 跨 Session 污染 | `orchestrator.py` | ✅ |
| BF-3 | doc_meta 系统 | `tutor.py`, `orchestrator.py` | ✅ |
| BF-4 | 意图识别增强 | `orchestrator.py` | ✅ |
| BF-5 | system_prompt 硬编码示例 | `tutor.py` | ✅ |
| BF-6 | 学习计划主题提取 | `renderer.py` | ✅ |
| BF-7 | RAG 短查询扩展 | `orchestrator.py` | ✅ |
| BF-8 | UI 3-Tab 重构 | `layout.py`, `state.py`, `styles.py`, `renderer.py` | ✅ |
| BF-9 | GitHub URL 识别 | `orchestrator.py` | ✅ |
| BF-10 | 删除会话功能 | `state.py` | ✅ |

---

## P3 - 锦上添花 ⬜ 全部未开始

### P3-1. RAG Eval 评测
- [ ] 设计评测集（10 条人工抽检 + hit@k）
- [ ] 实现评测脚本
- [ ] 生成评测报告到 `data/eval/`

### P3-2. 引用来源标注
- [ ] RAGEngine 返回 source metadata
- [ ] Tutor 回答携带 citations
- [ ] UI 渲染引用折叠区

### P3-3. UI 精细打磨
- [ ] CSS 动画优化
- [ ] 暗色主题支持
- [ ] 移动端适配

### P3-4. 演示视频录制
- [ ] 录制脚本准备
- [ ] 录制 + 剪辑
- [ ] 上传 + 嵌入 README

---

## 执行时间表（实际进度）

| 天数 | 任务 | 状态 |
|------|------|------|
| **Day 1-3** | 基础设施 + RAG + Agents 骨架 | ✅ 完成 |
| **Day 4** | UI 重构 + Orchestrator 增强 + 文档 | ✅ 完成 |
| **Day 5** | UI 布局大改（UI-FIX-1~5）+ P0-1~P0-4 后端修复 | ✅ 完成 |
| **Day 6** | P1 全部 + P2-1/P2-2 | ✅ 完成 |
| **Day 7-8** | P2-3/P2-4 + Bug Fixes + UI 3-Tab 重构 + 验收调试 | ✅ 完成 |
| **Day 9** | UI 布局 Spec Bugfix（5 项修复） | ✅ 完成 |
| **Day 10 →** | 🆕 资源聚合 + 动态学习路径转型 + 端到端验收 | 🚧 进行中 |

---

## 最终验收标准（面试演示 Checklist）

- [x] 上传 PDF → 计划包含 PDF 关键术语 — 代码已改，待实测
- [x] 多轮问答 → Tutor 能理解"它"指什么 — 代码已改，待实测
- [x] 点击"下一步" → 自动执行对应后端动作 — 代码已改，待实测
- [x] Quiz Tab 和 Chat 中的测验数据一致 — 代码已改，待实测
- [x] 生成报告 → 看到真实的正确率和薄弱知识点 — 代码已改，待实测
- [x] 完成全流程 → 看到庆祝卡片和学习总结 — 代码已改，待实测
- [x] 有 LangGraph 版本文件（UI 切换开关待接通）
- [x] GitHub URL → 能看到真实 README 分析 — 代码已改，待实测
- [x] P2-3 LLM-based 意图识别 ✅
- [x] P2-4 Tutor 流式输出 ✅
- [ ] LangSmith 中能看到完整调用链 — 需要配置 API Key 后验证
- [ ] 能在 3 分钟内完成一次完整演示 — 需要跑全流程后计时
