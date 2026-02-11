# XLearning-Agent 改进清单 (TODO)

> **创建日期**：2026-02-10
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

## UI 当前排障清单（2026-02-11）

> **职责**：仅 UI 布局、样式、交互逻辑；参考 docs/ui_mockups.md 预期效果图。

### UI-BLOCKER-1. 启动命令环境不稳定（本机提示 `streamlit` 未识别）✅
- **现象**：终端中执行 `streamlit run app.py` 直接报 `CommandNotFoundException`
- **根因**：当前 PowerShell 会话未正确激活 venv，PATH 中没有 `streamlit`
- **建议固定命令**（推荐）：
  - `venv\\Scripts\\python.exe -m streamlit run app.py`
- **验收标准**：无论是否激活 venv，执行上述命令都可启动
- [x] 有 check_startup.py 启动前自检
- [x] 在 README 增加 Windows 启动命令（免激活）说明
- [x] 增加 `scripts/run_ui.ps1` 一键启动脚本

### UI-BLOCKER-2. Streamlit 配置文件容错与回归
- **现象**：历史上出现过 `hh[theme]` 导致 TOML 解析失败
- **文件**：`.streamlit/config.toml`
- **验收标准**：配置可被 `toml.loads()` 正常解析；不会出现非法首行
- [x] 保持 `[theme]` / `[server]` 配置最小化
- [x] 保留 `check_startup.py` 作为启动前自检

### UI-FIX-1. Stepper 显示与兼容性收敛 ✅
- **现象**：顶部 Stepper 有时仅白条吸顶，视觉与“灵动岛”预期不一致
- **文件**：`src/ui/layout.py`, `src/ui/styles.py`
- **验收标准**：滚动时 Stepper 主体（圆点+文字）始终清晰可见，位置稳定
- [x] Stepper 固定吸顶，单次输出确保 DOM 正确
- [x] 校准侧边栏 420px 下的 margin-left
- [x] 补充截图回归指南：`docs/screenshots/README.md`

### UI-FIX-2. 聊天气泡渲染安全与可读性 ✅
- **现象**：历史上出现过标签碎片（`</div>`）显示在消息中
- **文件**：`src/ui/renderer.py`
- **验收标准**：消息支持 Markdown 且不出现 HTML 结构泄漏
- [x] 内置 _markdown_to_html() 转换器，Agent 消息正确渲染 Markdown
- [x] 用户消息纯文本转义，避免 XSS；保留头像/气泡样式
- [x] 增加 `tests/test_markdown_renderer.py` 回归测试（代码块、引用、列表、转义）

### UI-FIX-3. 首页交互统一（ChatGPT 风格）✅
- **目标**：单主输入区 + 六个快捷示例统一放在输入区下方
- **文件**：`src/ui/layout.py`, `src/ui/styles.py`
- **验收标准**：无双输入框错觉；输入框足够宽；快捷入口与示例位置统一
- [x] 主输入框放最上，大而宽；PDF 收起到 expander；6 个快捷示例在下方
- [x] .home-input-wrap 白底、max-width: 1040px

### UI-FIX-4. 布局与分隔线 ✅
- **目标**：侧边栏固定、双列分隔线可见且可拖拽
- **文件**：`src/ui/layout.py`, `src/ui/styles.py`
- **验收标准**：侧边栏 420px 固定、隐藏拖拽把手和滚动条；分隔线支持拖动
- [x] 侧边栏 420px 固定，::after 遮挡拖拽把手，折叠按钮改为箭头
- [x] 隐藏侧边栏滚动条
- [x] 双列 2px 灰色分隔线（CSS 瞄准列容器）
- [x] JS 注入实现拖拽调整宽度（flex-wrap: nowrap + 像素宽度）

### UI-FIX-5. 右侧面板阶段化展示 ✅
- **现象**：Plan/Study 阶段仍大量复用 Brain 面板，信息层次不够
- **文件**：`src/ui/layout.py`, `src/ui/renderer.py`
- **验收标准**：Plan 有结构化计划预览，Study 有学习卡片/摘要区
- [x] 新增 `render_plan_panel()` 与 `render_study_panel()`（轻量版）
- [x] layout 中 Plan/Study 阶段改为调用二者，替代 render_brain_tab

---

## 下一步安排（UI/UX 职责范围）

> **参考**：`docs/ui_mockups.md` 预期效果图

| 优先级 | 任务 | 预计 | 说明 |
|--------|------|------|------|
| **1** | UI-BLOCKER-1 收尾 | 0.5h | README 启动说明 + `scripts/run_ui.ps1` ✅ |
| **2** | **UI-FIX-5** 右侧面板阶段化 | 1-2h | Plan 阶段：结构化计划预览 + 下载 .md；Study 阶段：学习卡片区 |
| **3** | 引导 Banner 动作分发完善 | 1h | 对照 mockups 9.2 表，确保各阶段按钮绑定到 `logic.handle_*`，Stepper 随阶段推进 |
| **4** | 完成庆祝页视觉校准 | 0.5h | 对照 mockups 第 7 节，三指标卡片、出口按钮布局（待验收） |
| **5** | 侧边栏增强 | 0.5h | 底部版本号 + LangSmith 连接状态（mockups 8）；开发者选项 LangGraph 开关预留（待验收） |
| **6** | 聊天气泡细节 | 0.5h | 证据来源折叠区样式；含代码块、引用样例的 Markdown 渲染回归（待验收） |
| **7** | 配色与视觉一致性 | 0.5h | 对照 mockups 附录配色方案，统一 Primary/Success/Warning（待验收） |

**职责边界**：仅 UI 布局、样式、交互逻辑；后端 Agent/Orchestrator 由其他模块负责。

---

## 验收办法（用户操作指引）

> **说明**：以下为从用户视角的手动验收步骤。验收成功后，再勾选对应 checklist 并标记完成。

### 启动验收（UI-BLOCKER-1）
1. **免激活 venv 启动**：在项目根目录打开 PowerShell，执行  
   `venv\Scripts\python.exe -m streamlit run app.py`  
   - ✓ 能正常启动，浏览器打开 `http://localhost:8501`
2. **PS1 脚本启动**：执行 `.\scripts\run_ui.ps1`  
   - ✓ 能正常启动
3. **README**：查看 README 中是否有 Windows 免激活启动说明  
   - ✓ 能找到上述命令或脚本说明

### 引导 Banner 与阶段切换（任务 3）
1. 启动应用 → 输入任意主题（如「Python 入门」）→ 点击「开始学习」→ 进入工作区
2. **Input 阶段**：看到横幅「资料已就绪」+ 按钮「📋 生成学习计划」→ 点击按钮  
   - ✓ 聊天区出现「正在生成计划」等反馈，右侧面板/Stepper 切换到 Plan
3. **Plan 阶段**：等计划生成完成后，看到横幅「计划已生成」+ 按钮「📖 开始学习第一章」→ 点击按钮  
   - ✓ Stepper 切换至「学习」为当前阶段，右侧显示学习相关内容
4. **Study 阶段**：若条件满足，出现「📝 开始测验」按钮 → 点击  
   - ✓ 进入测验流程或 Quiz 面板
5. **Quiz 完成后**：出现「📊 生成报告」→ 点击  
   - ✓ 右侧显示报告内容
6. **Report 完成后**：出现「🎉 查看总结」→ 点击  
   - ✓ 进入庆祝页（三指标卡片 + 下载报告 + 继续深入/新课程）

### 右侧面板阶段化（UI-FIX-5 / 任务 2）
1. 完成「生成学习计划」后，点击 Stepper 或 Banner 进入「规划」阶段
2. **Plan 面板验收**：
   - ✓ 右侧有「📋 学习计划预览」区域
   - ✓ 能看到阶段列表（阶段 1、2、3…）
   - ✓ 有「📥 下载计划 .md」按钮，点击能下载 .md 文件
3. 进入「学习」阶段
4. **Study 面板验收**：
   - ✓ 右侧显示知识库/学习计划相关区域（不是纯 Brain 记忆面板）
   - ✓ 能看到学习进度或学习卡片/摘要区

### 布局与分隔线（UI-FIX-4）
1. 进入工作区后，观察布局
2. **侧边栏**：左侧约 420px，无拖拽把手，折叠按钮为箭头 ◀
3. **双列**：聊天区与右侧面板之间有灰色竖线
4. **拖拽**：鼠标移到竖线附近，光标变为调整大小，可拖动改变左右宽度

### 庆祝页（任务 4）
1. 完成全流程（输入→计划→学习→测验→报告）后，点击「查看总结」
2. **验收**：
   - ✓ 顶部 Stepper 全部为 ✓ 完成状态
   - ✓ 有「恭喜！学习旅程已完成！」标题
   - ✓ 三张指标卡片：📚 学习阶段、📝 测验道题、📊 正确率（mockups 第 7 节）
   - ✓ 有主题、薄弱点摘要行
   - ✓ 有「下载完整报告」按钮
   - ✓ 有「🔄 继续深入学习」和「✨ 开始新课程」两个出口
   - ✓ 点击「开始新课程」返回首页

### 侧边栏（任务 5）
1. 查看左侧 Sidebar 最底部
2. **验收**：✓ 显示「v0.2.0 | LangSmith ✅」或「LangSmith ❌」（根据 API Key 是否配置）
3. 展开「🛠️ 开发者选项」
4. **验收**：✓ 有「🆕 LangGraph 模式」复选框（可勾选，逻辑预留）

### 聊天气泡（任务 6）
1. 触发一条含代码块（\`\`\`python ... \`\`\`）的 Agent 回复
2. **验收**：✓ 代码块深色背景、等宽字体、可读
3. 触发含引用（> 文本）的回复
4. **验收**：✓ 引用有左侧蓝条、浅蓝背景
5. 触发含证据来源（citations）的回复
6. **验收**：✓ 证据来源可折叠，样式清晰

### 配色（任务 7）
1. 查看 Stepper 当前阶段（如「学习」）
2. **验收**：✓ 活跃阶段圆点为橙色（Primary #F97316）
3. 查看已完成阶段
4. **验收**：✓ 已完成圆点为绿色（Success #22C55E）

---

## P0 - 致命断路（必须最先修复）

### P0-1. 修复 Planner 硬编码计划 ✅
- **文件**: `src/agents/planner.py` → `_parse_plan()`
- **已完成**：Prompt 改为 JSON 输出 + `_parse_plan()` 三层防御（JSON → 正则 → raw_markdown 兜底）
- **效果**: 不同 PDF / URL / 文本输入会生成不同的计划，包含真实术语
- [x] 修改 `_parse_plan()` 解析 LLM 输出
- [x] 修改 Prompt 为 JSON 格式输出
- [ ] 测试 3 种不同输入（PDF/URL/文本），验证计划差异化（待跑验收）

### P0-2. 连通 Report UI 与后端 ✅
- **文件**: `src/ui/renderer.py` + `src/ui/logic.py`
- **已完成**：新增 `handle_generate_report()`，"生成报告"按钮连通后端
- [x] 新增 `handle_generate_report()` 函数
- [x] 连接 UI 按钮到后端
- [ ] 报告包含 quiz_accuracy、weak_topics 等真实数据（待跑验收）

### P0-3. Quiz 数据同步 - 统一两个入口 ✅
- **文件**: `src/ui/logic.py`
- **已完成**：`handle_generate_quiz()` 改为调用真实 ValidatorAgent + Chat 触发 quiz 时同步写入 session
- [x] 重写 `handle_generate_quiz()` 调用真实后端
- [x] 统一 quiz 数据格式
- [ ] 测试两个入口生成的 quiz 是否一致（待跑验收）

### P0-4. 修复 Tutor History 未注入 LLM ✅
- **文件**: `src/agents/tutor.py` → `_handle_free_mode()`
- **已完成**：最近 6 轮历史拼入 prompt + 指代词触发 RAG query expansion
- [x] 将 history 拼入 prompt
- [ ] 测试多轮对话上下文理解（待跑验收）

---

## P1 - 体验断裂修复（用户流程自动化）

### P1-1. 解决流程断裂感 - 自动化引导流程 ✅
- **文件**: `src/ui/layout.py` → `_render_action_banner()` + `_dispatch_action()`
- **已完成**：Action Banner 按钮绑定真实后端动作（plan → quiz → report），Stepper 自动推进
- [x] 重写 `_render_action_banner()` 分发真实后端动作
- [x] PDF 上传后自动提示生成计划
- [x] Stepper 自动推进
- [ ] 测试全流程：上传 → 计划 → 学习 → 测验 → 报告（待跑端到端验收）

### P1-2. 解决 Quiz 入口不直观 ✅
- **文件**: `src/ui/logic.py` → `process_pending_chat()`
- **已完成**：Chat 触发 quiz 时同步写入 session["quiz"]，Quiz Tab 读取 session 数据
- [x] Chat quiz 结果写入 session
- [x] Quiz Tab 读取 session quiz 数据
- [x] action banner 添加"开始测验"按钮

### P1-3. 添加学习闭环 - 完成仪式感 ✅
- **文件**: `src/ui/layout.py` → `_check_completion()` + `_render_completion_view()`
- **已完成**：完成条件判断 + 庆祝页（三指标卡片 + 出口按钮）
- [x] 定义完成条件判断逻辑
- [x] 渲染完成卡片
- [x] Stepper 全绿 ✓
- [x] 提供"下载报告"和"新课程"按钮

---

## P2 - 面试加分项（简历关键词补全）

### P2-1. 实现 LangGraph 版 Orchestrator ✅
- **文件**: `src/agents/orchestrator_langgraph.py`（356 行，含面试话术注释）
- **已完成**：LearningState TypedDict + intent_router_node + planner/tutor/validator/report Node + 条件边路由
- [x] 创建 LangGraph 版本文件
- [x] 实现 StateGraph + 三个 Node
- [x] 条件边路由
- [ ] UI 切换开关（侧边栏已预留 checkbox，需接通后端）
- [ ] 对比测试（待跑验收）

### P2-2. 实现真实 GitHub API 调用 ✅
- **文件**: `src/specialists/repo_analyzer.py`
- **已完成**：httpx 调用 GitHub REST API + README + languages + 降级策略
- [x] 实现 GitHub API 调用
- [x] 获取 README + languages
- [x] 降级处理
- [ ] 导入 RAG（待验收自动导入链路）

### P2-3. 升级意图识别为 LLM-based
- **文件**: `src/agents/orchestrator.py` → `_detect_intent()`
- **问题**: 纯关键词匹配，容易误判
- **修复方案**:
  1. 用 LLM 做分类（一次额外调用，返回固定 JSON）
  2. Prompt: "判断用户意图，返回 JSON: {intent: 'create_plan' | 'ask_question' | 'start_quiz' | 'get_report' | 'chitchat'}"
  3. 保留关键词匹配作为 fallback（省 token）
  4. 添加缓存（相同输入不重复调用）
- **验收标准**: "帮我整理学习要点"不再误识别为 create_plan
- [ ] LLM 意图分类 Prompt
- [ ] Fallback 策略
- [ ] 测试边界用例

### P2-4. 实现 Tutor 流式输出
- **文件**: `src/agents/tutor.py` → `stream_response()`，`src/ui/logic.py`
- **问题**: 当前是一次性返回全部内容，用户等待体验差
- **修复方案**:
  1. 使用 LangChain ChatTongyi 的 `.stream()` 方法
  2. 在 UI 端用占位符逐步更新内容
  3. 只对 Tutor 的 Free 模式启用流式
- **验收标准**: 回答逐字/逐句出现，类似 ChatGPT 体验
- [ ] 实现真正的 stream_response
- [ ] UI 端逐步更新
- [ ] 测试流畅度

---

## P3 - 锦上添花

### P3-1. RAG Eval 评测
- 实现 10 条人工抽检 + hit@k 评估
- 记录评测结果到 `data/eval/`
- [ ] 设计评测集
- [ ] 实现评测脚本
- [ ] 生成评测报告

### P3-2. 引用来源标注
- Tutor 回答时标注 RAG 检索到的文档片段出处
- 显示在 Chat bubble 下方的"证据来源"折叠区
- [ ] RAGEngine 返回 source metadata
- [ ] Tutor 回答携带 citations
- [ ] UI 渲染引用

### P3-3. UI 精细打磨
- 更好的 CSS 动画
- 暗色主题支持
- 移动端适配
- [ ] CSS 优化
- [ ] 暗色主题
- [ ] 响应式布局

### P3-4. 演示视频录制
- 录制 3-5 分钟完整流程演示
- 上传到 GitHub Releases 或 YouTube
- README 中嵌入视频
- [ ] 录制脚本准备
- [ ] 录制 + 剪辑
- [ ] 上传 + 嵌入

---

## 执行时间表（实际进度）

| 天数 | 任务 | 状态 |
|------|------|------|
| **Day 1-3** | 基础设施 + RAG + Agents 骨架 | ✅ 完成 |
| **Day 4** | UI 重构 + Orchestrator 增强 + 文档 | ✅ 完成 |
| **Day 5** | UI 布局大改（UI-FIX-1~5）+ P0-1~P0-4 后端修复 | ✅ 完成 |
| **Day 6** | P1 全部 + P2-1/P2-2 | ✅ 完成 |
| **Day 7 →** | P2-3 LLM 意图识别 + P2-4 流式输出 | ⬜ 下一步 |
| **Day 8 →** | 端到端验收 + 集成调试 | ⬜ 待做 |
| **Day 9 →** | P3 打磨 + 演示视频 + 简历更新 | ⬜ 待做 |

---

## 最终验收标准（面试演示 Checklist）

- [x] 上传 PDF → 计划包含 PDF 关键术语（不是万年模板）— 代码已改，待实测
- [x] 多轮问答 → Tutor 能理解"它"指什么 — 代码已改，待实测
- [x] 点击"下一步" → 自动执行对应后端动作 — 代码已改，待实测
- [x] Quiz Tab 和 Chat 中的测验数据一致 — 代码已改，待实测
- [x] 生成报告 → 看到真实的正确率和薄弱知识点 — 代码已改，待实测
- [x] 完成全流程 → 看到庆祝卡片和学习总结 — 代码已改，待实测
- [x] 有 LangGraph 版本文件（UI 切换开关待接通）
- [x] GitHub URL → 能看到真实 README 分析 — 代码已改，待实测
- [ ] LangSmith 中能看到完整调用链 — 需要配置 API Key 后验证
- [ ] 能在 3 分钟内完成一次完整演示 — 需要跑全流程后计时
- [ ] P2-3 LLM-based 意图识别 — 尚未实现
- [ ] P2-4 Tutor 流式输出 — 尚未实现
