# XLearning-Agent TODO

> **最后更新**：2026-03-07
> **当前状态**：React + FastAPI 前端已完成，旧 Streamlit UI 已清理

---

## 已完成 ✅

- React + FastAPI 前端（NotebookLM 风格）12 个模块全部完成
- 旧 Streamlit UI、POC 实验脚本、调试文件已清理
- 40/40 前端属性测试通过
- Git 已提交并推送到远程

## 当前 TODO

### 🔴 BUG — 必须立即修复

- [x] 刷新页面后搜索资源全部丢失（搜索历史 + 已添加的搜索材料都没了）
- [] 搜索并发问题：部分平台没有被搜索到（并发调度 bug）
- [] 搜索 hover 预览问题：搜索结果 vs 搜索历史结果的数据结构不统一导致 hover 异常

### 🟠 P0 — 核心功能（影响可用性）

- [ ] 聊天 Agent Orchestrator：对话中可执行命令（如触发搜索、生成内容等）
- [ ] 聊天 Agent 感知材料变化：用户添加材料后 agent 能识别并利用新材料信息
- [ ] 将 chat.py 接入 Orchestrator（当前直接调 TutorAgent，绕过了意图识别/进度注入/搜索路由）
- [ ] 对话中触发 Studio 生成（如"帮我创建学习规划"→ 意图识别 → 生成内容 → SSE 推送到 Studio）
- [ ] 清理 Orchestrator 中的 Streamlit 残留代码（`st.session_state` 引用）
- [ ] Studio 各功能生成策略优化（prompt 策略、生成质量）
- [ ] 端到端功能验收（参照 `docs/acceptance_test.md`）
  - [ ] PDF 上传 → 解析 → 生成学习计划
  - [ ] GitHub URL → 识别并分析仓库
  - [ ] 多轮对话上下文理解
  - [ ] Studio 工具卡片生成内容（学习指南、闪卡、测验等）
  - [ ] 笔记 CRUD 完整流程
  - [ ] 资源搜索 → 加入材料 → 对话引用

### 🟡 P1 — 搜索 & 资源体验

- [ ] 添加知乎作为搜索源
- [x] 搜索中断按钮（用户可手动取消正在进行的搜索）
- [x] 材料查看器：打开小红书/其他网页资源时应与 PDF/MD 一样的缩放比例和宽度，UIUX 统一

### 🔵 P2 — 设置 & 可观测性

- [ ] 设置页：用户配置 API Key（LLM 和 Tokenizer/Embedding 的 API 如何统一？用户是否需要配两个？）
- [ ] LangChain/LangSmith 调用追踪可视化
- [ ] LangSmith 全链路追踪配置与验证（需要 API Key）

### 🟣 P3 — UI 打磨

- [ ] 深色模式视觉微调（部分组件可能有颜色不协调）
- [ ] 确保 1280px+ 桌面端体验流畅
- [ ] 错误提示文案优化（用户友好的中文提示）
- [ ] 加载状态优化（骨架屏已有，检查是否所有异步操作都覆盖）
- [ ] CSS 动画优化

### ⚪ P4 — 面试加分 & 锦上添花

- [ ] 多模态材料理解：PDF 图片用 VL 模型提取描述文本存入 ChromaDB，小红书图片同理，使 LLM 能"看到"图片内容
- [ ] LangGraph 版 Orchestrator UI 切换开关接通后端
- [ ] RAG Eval 评测（设计评测集 + 评测脚本 + 报告）
- [ ] 引用来源标注（RAGEngine 返回 source metadata → Tutor 携带 citations → UI 渲染引用折叠区）
- [ ] 3 分钟演示脚本与计时演练
- [ ] 演示视频录制
- [ ] 更新 README 中的开发计划表和架构图

---

## 技术栈

| 层 | 技术 |
|---|------|
| 前端 | React + TypeScript + Vite + Tailwind CSS + Zustand |
| 后端 API | FastAPI（`backend/`，薄封装层） |
| 核心逻辑 | `src/` — Agents、Providers、RAG、Specialists |
| 测试 | Vitest（前端）+ Pytest + Hypothesis（后端/核心） |

## 启动方式

```powershell
# 一键启动
.\start_dev.ps1

# 或分别启动
# 后端: uvicorn backend.main:app --port 8000
# 前端: cd frontend && npm run dev
```
