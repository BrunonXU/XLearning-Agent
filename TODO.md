# XLearning-Agent TODO

> **最后更新**：2026-03-03
> **当前状态**：React + FastAPI 前端已完成，旧 Streamlit UI 已清理

---

## 已完成 ✅

- React + FastAPI 前端（NotebookLM 风格）12 个模块全部完成
- 旧 Streamlit UI、POC 实验脚本、调试文件已清理
- 40/40 前端属性测试通过
- Git 已提交并推送到远程

## 当前 TODO

### P0 - 核心功能完善

- [ ] 端到端功能验收（参照 `docs/acceptance_test.md`）
  - [ ] PDF 上传 → 解析 → 生成学习计划
  - [ ] GitHub URL → 识别并分析仓库
  - [ ] 多轮对话上下文理解
  - [ ] Studio 工具卡片生成内容（学习指南、闪卡、测验等）
  - [ ] 笔记 CRUD 完整流程
  - [ ] 资源搜索 → 加入材料 → 对话引用

- [ ] LangSmith 全链路追踪配置与验证（需要 API Key）

### P1 - 体验优化

- [ ] 深色模式视觉微调（部分组件可能有颜色不协调）
- [ ] 移动端不考虑，但确保 1280px+ 桌面端体验流畅
- [ ] 错误提示文案优化（用户友好的中文提示）
- [ ] 加载状态优化（骨架屏已有，检查是否所有异步操作都覆盖）

### P2 - 面试加分项

- [ ] LangGraph 版 Orchestrator UI 切换开关接通后端
- [ ] RAG Eval 评测（设计评测集 + 评测脚本 + 报告）
- [ ] 引用来源标注（RAGEngine 返回 source metadata → Tutor 携带 citations → UI 渲染引用折叠区）
- [ ] 3 分钟演示脚本与计时演练
- [ ] 演示视频录制

### P3 - 锦上添花

- [ ] CSS 动画优化
- [ ] 更新 README 中的开发计划表和架构图
- [ ] 更新 `TODO.md` 中的旧内容（已完成 ✅）

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
# 后端: uvicorn backend.main:app --reload --port 8000
# 前端: cd frontend && npm run dev
```
