# XLearning-Agent TODO

> **最后更新**：2026-03-08
> **当前状态**：React + FastAPI 前端已完成，正在做 Agent Memory 系统设计

---

## 🔥 当前进行中

- [ ] **Agent Memory 系统设计**（Episodic Memory，spec 在 `.kiro/specs/episodic-memory/`）
  - 对话摘要压缩、归档机制
  - 多轮对话上下文理解依赖此系统

## 🔴 BUG / 待优化

- [ ] 搜索并发问题：部分平台没有被搜索到（并发调度待优化）
- [ ] 搜索过程中的 UIUX 体验不够好，需要重新设计

## 🔴 P0 — 核心功能

- [ ] RAG Eval 评测（10+ 条 query 人工抽检 + hit@k 脚本，面试必备数据）
- [ ] Studio Prompt 策略继续优化（生成质量、各工具类型的 prompt 调优）
- [ ] 将 chat.py 接入 Orchestrator（当前直接调 TutorAgent，绕过了意图识别/进度注入/搜索路由）
- [ ] 清理 Orchestrator 中的 Streamlit 残留代码（`st.session_state` 引用）
- [ ] 端到端功能验收（参照 `docs/acceptance_test.md`）
  - [x] PDF 上传 → 解析 → 生成学习计划
  - [ ] GitHub URL → 识别并分析仓库（从未测试过）
  - [x] Studio 工具卡片生成内容（学习指南、闪卡、测验等）
  - [x] 笔记 CRUD 完整流程
  - [x] 资源搜索 → 加入材料 → 对话引用

## 🟡 P1 — 未来功能

- [ ] 添加知乎作为搜索源（ZhihuSearcher 代码已有，需接入前端平台选择）
- [ ] 对话中触发 Studio 生成（意图识别 → 生成内容 → SSE 推送到 Studio）

## 🔵 P2 — 可观测性

- [ ] LangSmith 调用追踪可视化（前端展示）

## 🟣 P3 — UI 打磨

- [ ] 深色模式视觉微调
- [ ] 确保 1280px+ 桌面端体验流畅
- [ ] 错误提示文案优化
- [ ] 加载状态优化
- [ ] CSS 动画优化

## ⚪ P4 — 面试加分 & 锦上添花

- [ ] 多模态材料理解（PDF 图片 + 小红书图片用 VL 模型提取描述文本）
- [ ] LangGraph 版 Orchestrator UI 切换开关
- [ ] RAG Eval 评测（评测集 + 脚本 + 报告）
- [ ] 引用来源标注（RAGEngine → citations → UI 渲染）
- [ ] 3 分钟演示脚本与计时演练
- [ ] 演示视频录制
- [ ] 更新 README 中的开发计划表和架构图

---

## 已知技术债务

- `tutor.py` 的 `stream_response` 有 debug dump 到 `data/last_llm_call.txt`
- `prompt_builder.py` 中 `_build_study_guide_instruction` 重复定义了两次
- Orchestrator 未接入 chat.py，且有 Streamlit 残留代码
- `SearchHistoryCard.tsx` 有 BOM 编码问题
- `add_materials_from_search` 端点在 `upload.py` 里（不是 `resource.py`）

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

---

## ✅ 已完成（按优先级归档）

### 核心功能
- [x] React + FastAPI 前端（NotebookLM 风格）12 个模块全部完成
- [x] SQLite 统一持久化（8 张表 + 级联删除 + WAL 模式）
- [x] 多源搜索聚合（小红书/B站/YouTube/GitHub/Google，两阶段漏斗筛选）
- [x] 搜索策略优化（SlotAllocator 配额分配、关键词翻译、三批并发调度）
- [x] 材料感知聊天（拖拽材料到输入框，显式注入模式）
- [x] PromptBuilder 7 种工具类型基础实现（RAG 策略 + 进度注入 + 学习者画像）
- [x] Provider 热切换 + 设置页 API Key 配置

### UIUX & 体验
- [x] 搜索中断按钮
- [x] 材料查看器 UIUX 统一（网页资源与 PDF/MD 一致）
- [x] 搜索 hover 预览数据结构统一
- [x] 搜索历史持久化（刷新不丢失）

### 可观测性 & 工程化
- [x] LangSmith 全链路追踪（@traceable + 环境变量配置）
- [x] 40/40 前端属性测试通过
- [x] Kiro steering 文件体系（4 个领域 steering + project-conventions）
- [x] 技术文档更新（技术规格书 v4.0）

### 清理
- [x] 旧 Streamlit UI、POC 实验脚本、调试文件已清理
