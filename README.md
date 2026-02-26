# 🎓 XLearning-Agent

> **AI 智能学习助手** - 基于 LangChain + RAG + Multi-Agent 架构的个性化学习平台

[![Python Version](https://img.shields.io/badge/python-3.10+-blue.svg)](https://python.org)
[![LangChain](https://img.shields.io/badge/LangChain-0.2+-green.svg)](https://langchain.com)
[![LangSmith](https://img.shields.io/badge/LangSmith-Enabled-purple.svg)](https://smith.langchain.com)

---

## ✨ 功能特性

- 📋 **智能规划** - Planner Agent 自动分析 GitHub 仓库/PDF 论文，生成包含真实学习资源的个性化学习路径
- 🔍 **多源资源聚合** - ResourceSearcher 从 Bilibili、YouTube、Google、GitHub 等平台搜索真实学习资源
- 🎓 **互动教学** - Tutor Agent 支持自由对话、资源推荐、动态学习进度追踪
- 📈 **动态学习路径** - 会话级进度记忆，根据学习反馈动态调整学习大纲
- 🔍 **RAG 知识检索** - ChromaDB 向量存储，基于用户上传资料的个性化知识问答
- 📊 **全链路追踪** - LangSmith 集成，Token 统计 & 调用链可视化
- 🔄 **双模式运行** - 单独模式精细控制，协调模式一键完成全流程
- 📝 **可选测验** - Quiz 测验作为可选功能，不强制用户走测验流程

---

## 🏗️ 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                    展示层 (Streamlit)                        │
│              Plan (学习路径) | Study (学习+资源)             │
├─────────────────────────────────────────────────────────────┤
│                    可观测层 (LangSmith)                      │
├─────────────────────────────────────────────────────────────┤
│                    协调层 (Orchestrator)                     │
│              意图识别 · Agent 调度 · 进度上下文               │
├─────────────────────────────────────────────────────────────┤
│   Planner Agent   │   Tutor Agent   │   Validator Agent    │
│   (学习路径生成)   │  (互动教学+RAG) │   (可选测验/报告)    │
├─────────────────────────────────────────────────────────────┤
│ ResourceSearcher │ RepoAnalyzer │ PDFAnalyzer │ QuizMaker  │
│ (多源资源搜索)   │ (GitHub分析) │ (PDF解析)   │ (可选测验) │
├─────────────────────────────────────────────────────────────┤
│                    RAG 层 (ChromaDB)                        │
├─────────────────────────────────────────────────────────────┤
│                    Provider 层 (Tongyi/Qwen)                │
└─────────────────────────────────────────────────────────────┘
```

---

## 🚀 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/your-username/XLearning-Agent.git
cd XLearning-Agent
```

### 2. 创建虚拟环境

```bash
python -m venv venv
# Windows
.\venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件，填入你的 API Keys
```

### 5. 运行应用

```bash
streamlit run app.py
```

> **Windows 免激活 venv 启动**：若 PowerShell 未激活虚拟环境，`streamlit` 可能报 `CommandNotFoundException`。使用以下任一方式即可：
>
> - 推荐：`venv\Scripts\python.exe -m streamlit run app.py`
> - 一键脚本：`.\scripts\run_ui.ps1`（需在项目根目录执行）
>
> 启动前可运行 `python check_startup.py` 做自检。

---

## 📁 项目结构

```
XLearning-Agent/
├── docs/                          # 文档
│   ├── ultimate_technical_specification.md
│   ├── ui_mockups.md              # UI 线框图
│   └── acceptance_test.md         # 验收测试清单
├── src/                           # 源代码
│   ├── providers/                 # LLM Provider 抽象层
│   │   ├── base.py               # 抽象基类
│   │   ├── factory.py            # 工厂模式
│   │   ├── tongyi.py             # Tongyi/Qwen 实现
│   │   └── local_embedding.py    # 本地 Embedding
│   ├── rag/                       # RAG 知识层
│   │   └── engine.py             # RAG 引擎 (ChromaDB)
│   ├── agents/                    # Agent 层
│   │   ├── base.py               # Agent 基类
│   │   ├── planner.py            # 规划 Agent（学习路径+资源）
│   │   ├── tutor.py              # 教学 Agent（对话+RAG+进度）
│   │   ├── validator.py          # 验证 Agent（可选测验/报告）
│   │   ├── orchestrator.py       # 协调器（意图识别+调度）
│   │   └── orchestrator_langgraph.py  # LangGraph 版协调器
│   ├── specialists/               # 专业处理层
│   │   ├── resource_searcher.py  # 🆕 多源资源搜索
│   │   ├── repo_analyzer.py      # GitHub 仓库分析
│   │   ├── pdf_analyzer.py       # PDF 解析
│   │   └── quiz_maker.py         # Quiz 生成（可选）
│   ├── observability/             # 可观测层
│   │   └── tracing.py            # LangSmith 追踪
│   ├── core/                      # 核心模块
│   │   ├── config.py             # 配置管理
│   │   ├── file_manager.py       # 文件管理
│   │   └── models.py             # 数据模型
│   └── ui/                        # UI 组件
│       ├── layout.py             # 页面布局（Home/Workspace）
│       ├── renderer.py           # 聊天渲染器
│       ├── logic.py              # UI 业务逻辑
│       ├── state.py              # 会话状态管理
│       ├── styles.py             # CSS 样式
│       └── components.py         # 通用组件
├── tests/                         # 测试
├── data/                          # 数据目录（ChromaDB + Sessions）
├── requirements.txt               # 依赖
├── app.py                         # 应用入口
└── README.md
```

---

## 🎯 开发计划

| 阶段 | 日期 | 任务 | 状态 |
|------|------|------|------|
| 基础搭建 | Day 1-3 | 项目初始化、Provider、RAG | ✅ 完成 |
| 核心 Agent | Day 4-5 | UI 重构、Orchestrator 增强、P0 后端修复 | ✅ 完成 |
| 功能完善 | Day 6-8 | P1/P2 全部、Bug Fixes、UI 3-Tab 重构 | ✅ 完成 |
| UI 打磨 | Day 9 | UI 布局 Spec Bugfix（5 项修复） | ✅ 完成 |
| 方向转型 | Day 10+ | 🆕 资源聚合 + 动态学习路径 | 🚧 进行中 |
| 收尾 | — | 端到端验收、演示视频、简历更新 | ⏳ 待开始 |

### 🆕 当前重点：资源聚合 + 动态学习路径

> Quiz/Report 流程降级为可选，核心价值转向「多源资源聚合 + 动态学习路径」

- 新增 `ResourceSearcher` 专家模块，聚合 Bilibili/YouTube/Google/GitHub 资源
- Planner 生成学习路径时自动搜索真实学习资源
- 会话级学习进度追踪（ProgressTracker）
- UI 主流程简化为 Plan | Study 两步

---

## 📜 License

MIT License

---

## 🙏 致谢

- [Yixiang-Wu-LearningAgent](https://github.com/Lorry-LY/LearningAgent) - 三层 Agent 架构设计灵感
- [melxy1997-ColumnWriter](https://github.com/melxy1997/ColumnWriter) - Orchestrator 协调模式参考
- [LangChain](https://langchain.com) - 核心框架
- [LangSmith](https://smith.langchain.com) - 可观测性平台
