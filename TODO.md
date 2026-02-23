# XLearning-Agent 改进清单 (TODO)

> **创建日期**：2026-02-10
> **最后更新**：2026-02-23
> **目标**：修复核心断路点，达到面试可演示水平
> **当前版本**：v0.3.0

---

## 总览：优先级分层

| 优先级 | 类别 | 状态 | 影响 |
|--------|------|------|------|
| **P0** | 致命断路 - 演示翻车级 | ✅ 全部完成 | 不修就废 |
| **P1** | 体验断裂 - 用户困惑级 | ✅ 全部完成 | 面试扣分 |
| **P2** | 面试加分 - 简历关键词级 | ✅ 全部完成 | 锦上添花 |
| **P3** | 锦上添花 - 专业度级 | ⬜ 部分完成 | 有余力再做 |

---

## P0 - 致命断路 ✅ 全部完成

### P0-1. 修复 Planner 硬编码计划 ✅
### P0-2. 连通 Report UI 与后端 ✅
### P0-3. Quiz 数据同步 ✅
### P0-4. 修复 Tutor History 未注入 LLM ✅

---

## P1 - 体验断裂修复 ✅ 全部完成

### P1-1. 自动化引导流程 ✅
### P1-2. Quiz 入口统一 ✅
### P1-3. 学习闭环 - 完成仪式感 ✅

---

## P2 - 面试加分项 ✅ 全部完成

### P2-1. LangGraph 版 Orchestrator ✅
### P2-2. GitHub API 调用 ✅
### P2-3. LLM-based 意图识别 ✅
### P2-4. Tutor 流式输出 ✅

---

## Bug Fixes (Day 7-8) ✅ 全部完成

BF-1 ~ BF-10 已全部修复，详见 git 历史。

---

## Day 9+ 新增功能与修复

> **说明**：Day 9 起的迭代开发，以验收测试驱动

### DF-1. 首页 GPT 风格重设计 ✅
- **文件**: `src/ui/layout.py`, `src/ui/styles.py`
- 圆角药丸输入栏 + 左侧圆形 ➕ 按钮（点击展开文件上传）
- 6 个快捷示例居中排列在输入栏下方
- 纯白背景，CSS `:has()` + `#home-chatbar-anchor` 精准定位

### DF-2. 交互式菱形时间线路线图 ✅
- **文件**: `src/ui/renderer.py`, `src/ui/state.py`
- 菱形 Day 节点，点击展开详情卡片（任务/资源/验收/明日预告）
- 完成标记：绿色菱形 + 呼吸动画连接线
- 5 天视窗 + ◀▶ 箭头滑动浏览（不再一次显示全部）
- 详情卡片不再截断（iframe 高度 620px + scrolling）
- `_parse_daily_plan()` 解析 LLM 按天计划为结构化数据

### DF-3. Enter 发送 + 聊天体验优化 ✅
- **文件**: `src/ui/renderer.py`, `src/ui/layout.py`
- `st.text_input` + `on_change` 实现 Enter 直接发送
- 首页和工作区统一体验

### DF-4. 3-Tab 系统重构 ✅
- **文件**: `src/ui/layout.py`, `src/ui/styles.py`, `src/ui/state.py`, `src/ui/renderer.py`
- 6 阶段 Stepper → 3 个可点击 Tab（规划/学习/测验）
- 纯 CSS 样式，橙色下划线指示当前 Tab

### DF-5. 多格式文件上传 ✅
- **文件**: `src/ui/layout.py`, `src/agents/orchestrator.py`, `src/ui/logic.py`
- 支持 PDF / MD / TXT / DOCX 上传
- python-docx 处理 DOCX，纯文本处理 MD/TXT

### DF-6. 侧边栏会话管理 ✅
- **文件**: `src/ui/layout.py`, `src/ui/state.py`
- 会话改名 / 删除 / 清除全部
- 独立按钮布局避免 CSS 冲突

### DF-7. Planner 先问后答 ✅
- **文件**: `src/agents/orchestrator.py`
- Planner 收到模糊输入时先询问学习目标，再生成计划
- GitHub URL 也走先问流程

### DF-8. Tutor 首次交互行为 ✅
- **文件**: `src/agents/tutor.py`
- 首次交互询问学习目标，而非直接生成计划

### DF-9. 工作区双列独立滚动 ✅
- **文件**: `src/ui/styles.py`
- 聊天区和功能面板各自独立滚动
- 固定底部 Footer

### DF-10. 测验 Loading 状态 + 计划缓存 ✅
- **文件**: `src/ui/logic.py`, `src/ui/renderer.py`
- 生成测验/报告时显示 loading 提示
- 计划缓存到 `session["_cached_plan_md"]` 避免重复解析

---

## P3 - 锦上添花

### P3-1. RAG Eval 评测
- [ ] 设计评测集
- [ ] 实现评测脚本
- [ ] 生成评测报告

### P3-2. 引用来源标注
- [ ] RAGEngine 返回 source metadata
- [ ] Tutor 回答携带 citations
- [ ] UI 渲染引用

### P3-3. UI 精细打磨
- [x] 纯白背景 + GPT 风格首页
- [x] 交互式时间线路线图
- [ ] 暗色主题支持
- [ ] 移动端适配

### P3-4. 演示视频录制
- [ ] 录制脚本准备
- [ ] 录制 + 剪辑
- [ ] 上传 + 嵌入 README

### P3-5. LangGraph 模式接通
- [ ] UI 切换开关接通后端（侧边栏已预留 checkbox）
- [ ] 对比测试 LangGraph vs 原版 Orchestrator

---

## 执行时间表

| 天数 | 任务 | 状态 |
|------|------|------|
| **Day 1-3** | 基础设施 + RAG + Agents 骨架 | ✅ |
| **Day 4** | UI 重构 + Orchestrator 增强 + 文档 | ✅ |
| **Day 5** | UI 布局大改 + P0 后端修复 | ✅ |
| **Day 6** | P1 全部 + P2-1/P2-2 | ✅ |
| **Day 7-8** | P2-3/P2-4 + Bug Fixes + 3-Tab 重构 | ✅ |
| **Day 9-10** | 首页重设计 + 时间线路线图 + 多格式上传 + 会话管理 | ✅ |
| **Day 11** | 时间线 5 天视窗 + 首页 GPT 药丸输入栏 + TODO 更新 | ✅ |
| **Day 12 →** | P3 打磨 + 演示视频 + 简历更新 | ⬜ 下一步 |

---

## 最终验收标准（面试演示 Checklist）

- [x] 上传 PDF → 计划包含 PDF 关键术语
- [x] 多轮问答 → Tutor 能理解上下文
- [x] 3-Tab 导航 → 规划/学习/测验自由切换
- [x] Quiz Tab 和 Chat 中的测验数据一致
- [x] 生成报告 → 真实正确率和薄弱知识点
- [x] 完成全流程 → 庆祝卡片和学习总结
- [x] 有 LangGraph 版本文件
- [x] GitHub URL → 真实 README 分析
- [x] 交互式时间线路线图（菱形节点 + 5 天视窗 + 箭头滑动）
- [x] GPT 风格首页（药丸输入栏 + ➕ 上传 + 快捷示例）
- [x] 多格式文件上传（PDF/MD/TXT/DOCX）
- [x] 会话管理（改名/删除/清除全部）
- [ ] LangSmith 调用链可视化 — 需配置 API Key
- [ ] 3 分钟完整演示 — 需跑全流程计时
- [ ] 演示视频录制
