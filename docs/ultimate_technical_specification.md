# 🎓 Enhanced Learning Agent - 终极技术规格书

> **版本**：v3.1 Final (Risk-Adjusted)
> **创建时间**：2026-02-05
> **更新时间**：2026-02-05 02:20
> **目标**：14天完成一个简历级 AI 学习助手项目

---

# ⚠️ 风险评估与 MVP 边界（重要！先读这里）

## 可行性评估

| 目标 | 可行性 | 说明 |
|------|--------|------|
| **做出能演示的简历级 MVP** | 🟢 70-80% | 高可行 |
| **文档里所有功能都落地且稳定** | 🟡 40-55% | 风险较高 |

## 6 个最容易被低估的难点

| # | 难点 | 为什么容易超时 | 应对策略 |
|---|------|---------------|----------|
| 1 | **GitHub 仓库分析范围** | "分析"可以从只读 README 到递归扫目录，范围失控 | ✅ **只读 README + requirements**，不做代码遍历 |
| 2 | **PDF 解析结构化质量** | 公式、表格、双栏会把 chunk 质量拉低 | ✅ **只提取正文**，跳过复杂结构 |
| 3 | **RAG 效果评估** | "能回答"不等于"引用对"，面试容易被问住 | ✅ **至少做 10 条人工抽检 + hit@k** |
| 4 | **LangSmith 集成摩擦** | HelloAgents 不是 LangChain 全家桶，接入有摩擦 | ✅ **只追踪 LLM call + retrieval**，不追求全覆盖 |
| 5 | **Streamlit 状态管理** | 聊天 + 上传 + 流式 + 双模式，调试时间常比写 Agent 久 | ✅ **先做最简 UI，不追求复杂仪表盘** |
| 6 | **多 Provider 流式兼容** | 各家流式协议、错误语义不一致 | ✅ **只做 1 个 Provider + 非流式先行** |

## ABC 优先级分层（严格执行！）

### 🅰️ 必须交付（简历级最关键）

| 功能 | 最小边界 | 不做什么 |
|------|---------|----------|
| **Provider** | 只实现 1 个（Tongyi/Qwen）+ 工厂模式接口预留 | 不做多 Provider 全兼容 |
| **三个 Agent** | Planner / Tutor / Validator，功能要薄 | 不做复杂错误恢复 |
| **双模式** | 单独/协调模式保留，但逻辑简化 | 不做状态机持久化 |
| **RAG** | 导入 1 份 PDF 或 1 个 README → 入库 → 问答 | 不做大仓库递归扫描 |
| **Quiz** | 客观题生成 + 基础评分 | 先不做主观题评分 |
| **进度报告** | 文本版 Markdown | 先不做图表可视化 |

### 🅱️ 可选加分（能做就加，做不完不伤）

| 功能 | 最小边界 |
|------|----------|
| **LangSmith** | 追踪每次 LLM call + retrieval，不追求全覆盖 |
| **Streamlit** | 对话 + 上传 + 1 个进度指标，不追求复杂仪表盘 |
| **LangGraph** | Checkpoint 2 达成后才做（Day 7+），之前只设计接口 |
| **流式输出** | 核心跑通后再加，只对 Tutor 最终回答流式 |

### 🅲️ 直接砍掉（14天内回报率低）

| 功能 | 原因 |
|------|------|
| **FastAPI 服务化** | 除非明确投后端岗 |
| **多 Provider 全量兼容** | 做 1 个就够讲设计能力 |
| **复杂图表仪表盘** | 时间杀手 |
| **代码递归分析** | 范围失控 |

## 🚦 Go/No-Go 检查点（严格执行！）

| 检查点 | 时间 | 必须达成 | 未达成怎么办 |
|--------|------|---------|-------------|
| **Checkpoint 1** | Day 3 结束 | RAG 最小闭环跑通（导入文本→检索→回答） | 立刻砍 LangSmith，专注 RAG |
| **Checkpoint 2** | Day 7 结束 | 三个 Agent + 双模式能完成最小演示链路 | 砍 LangGraph，简化 UI 计划 |
| **Checkpoint 3** | Day 11 结束 | Streamlit 上能完整演示一次流程 | 砍所有可选项，专注文档和简历 |

> ⚠️ **任何一个检查点未达成，立刻降 scope，不要硬追加分项！**

---

# 🎯 核心策略：LangChain 组件 + 自研编排

## 为什么这么做？

| 你的目标 JD | 应对策略 |
|-----------|----------|
| 强调 **LangChain/LangGraph** | 底层组件必须用 LangChain |
| 强调 **可观测性** | LangSmith 不是可选，是必须 |
| 强调 **工程能力** | 抽象层、状态机要能讲清楚 |

## 技术栈调整

```
┌─────────────────────────────────────────────────────────┐
│                     你的自研编排层                       │
│        Orchestrator（ReAct 风格，你能讲清楚原理）            │
│        + LangGraph 版本（对照实现，必做）                    │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│              LangChain 组件（简历关键词 ✔️）                │
│  • ChatTongyi / Qwen（LLM 调用）                           │
│  • DashScopeEmbeddings（向量化）                         │
│  • RecursiveCharacterTextSplitter（切分）              │
│  • Chroma（向量存储）                                    │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│                     LangSmith（必须）                       │
│              自动追踪 LangChain 组件调用                   │
│              + 手动追踪自研编排层                          │
└─────────────────────────────────────────────────────────┘
```

## 关键调整（vs 原计划）

| 原计划 | 新策略 |
|--------|--------|
| HelloAgentsLLM | → `ChatTongyi` (langchain_community) |
| 自己写 Embedding | → `DashScopeEmbeddings` (langchain_community) |
| 自己接 LangSmith | → 自动接（LangChain 组件默认支持） |
| LangGraph 可选 | → **Checkpoint 2 达成后做**（之前只设计接口） |
| Provider 抽象层 | → 保留工厂模式，但只实现 Tongyi 1 个 |

## 简历写法（关键词全覆盖）

> "基于 **LangChain** 组件（ChatTongyi/DashScopeEmbeddings/Chroma）+ 自研 Agent 编排层构建的 AI 学习助手。使用 **LangGraph** 实现状态机工作流，接入 **LangSmith** 实现全链路追踪。"

## 面试话术

> "我没有直接用 LangChain 的 create_react_agent，因为我想更深入理解 ReAct 的原理。但底层的 LLM 调用、向量化、检索都用的是 LangChain 组件（ChatTongyi + DashScopeEmbeddings），LangSmith 追踪也是一行代码就接上了。后来我又用 LangGraph 重新实现了一版 Orchestrator，对比两种方式的优劣。"

---

# 📑 目录

1. [项目概述](#1-项目概述)
2. [技术栈全景](#2-技术栈全景)
3. [系统架构](#3-系统架构)
4. [模块拆分与能力要求](#4-模块拆分与能力要求)
5. [设计决策与借鉴来源](#5-设计决策与借鉴来源)
6. [用户使用流程](#6-用户使用流程)
7. [数据流向](#7-数据流向)
8. [面试技术点与逻辑链](#8-面试技术点与逻辑链)
9. [可选技术扩展](#9-可选技术扩展)
10. [14天开发计划](#10-14天开发计划)
11. [简历写法](#11-简历写法)
12. [原两周计划价值提取](#12-原两周计划价值提取)

---

# 1. 项目概述

## 1.1 一句话定位

**"一个支持 GitHub仓库/PDF论文 分析、具备 RAG 知识检索、双模式互动学习、全链路可追踪的 AI 学习助手"**

## 1.2 项目故事

### 灵感来源

在学习 AI 技术的过程中，我发现：
- 📚 学习资料散落各处（GitHub 项目、论文、博客）
- 🤯 缺乏系统化的学习路径
- 📝 学过的知识容易遗忘
- ❓ 没有一个能随时答疑的"私人导师"

于是我决定打造一个 **AI 学习助手**，它能够：
1. 分析任何 GitHub 项目或 PDF 论文，自动生成学习计划
2. 记住我学过的知识，用 RAG 检索回答问题
3. 通过 Quiz 测验验证学习效果
4. 全程追踪学习进度，生成可视化报告

### 项目来源

| 来源 | 借鉴内容 |
|------|---------|
| **Yixiang-Wu-LearningAgent** | 三层 Agent 架构、双模式学习、FileManager |
| **melxy1997-ColumnWriter** | Orchestrator 协调模式、质量闭环、多 Agent 模式 |
| **Apricity-InnocoreAI** | Agent 命名风格、专业分工思路 |
| **我的两周学习计划** | RAG + Eval + Trace + Tool Calling 需求 |

## 1.3 解决的核心需求

| 需求 | 解决方案 |
|------|---------|
| 学习资料分散 | GitHub/PDF 自动分析，统一入库 |
| 缺乏学习路径 | Planner Agent 自动生成计划 |
| 知识易遗忘 | RAG 知识库 + Quiz 验证 |
| 没有答疑老师 | Tutor Agent 互动教学 |
| 进度难追踪 | Validator Agent + 进度报告 |
| 调试困难 | LangSmith 全链路追踪 |

---

# 2. 技术栈全景

## 2.1 核心技术栈

```
┌─────────────────────────────────────────────────────────────┐
│                        展示层                                │
│  Streamlit (Web UI)                                         │
│  • st.chat_message (对话组件)                                │
│  • st.file_uploader (文件上传)                               │
│  • st.progress / st.metric (可视化)                          │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                       可观测层                               │
│  LangSmith / Phoenix                                        │
│  • Trace 调用链追踪                                          │
│  • Token 消耗统计                                            │
│  • 延迟监控                                                  │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                       Agent 层                               │
│  HelloAgents Framework                                       │
│  • ReActAgent (规划)                                         │
│  • SimpleAgent (教学/验证)                                   │
│  • ReflectionAgent (自我评估) [可选]                         │
│                                                              │
│  [可选] LangGraph                                            │
│  • StateGraph (状态机)                                       │
│  • Node + Edge (工作流)                                      │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                       RAG 层                                 │
│  ChromaDB (向量存储)                                         │
│  • OpenAI Embeddings / HuggingFace                          │
│  • 相似度检索 Top-K                                          │
│  • 文档切分 (RecursiveCharacterTextSplitter)                 │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                      Provider 层                             │
│  LLM Provider 抽象（工厂模式）                                   │
│  • Tongyi/Qwen (qwen-turbo) ← 实际实现                      │
│  • OpenAI (gpt-4o-mini) [接口预留，不实现]                    │
│  • DeepSeek [接口预留，不实现]                                 │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                      持久化层                                │
│  FileManager (~/.learningAgent/)                            │
│  • plan.md (学习计划)                                        │
│  • knowledge/ (知识笔记)                                     │
│  • sessions/ (会话记录)                                      │
│                                                              │
│  [可选] SQLite (结构化数据)                                  │
└─────────────────────────────────────────────────────────────┘
```

## 2.2 技术栈版本锁定

```txt
# requirements.txt
python>=3.10

# LangChain 核心（简历关键词 ✔️）
langchain>=0.2.0
langchain-core>=0.2.0
langchain-community>=0.2.0       # ChatTongyi, DashScopeEmbeddings
langchain-text-splitters>=0.2.0  # RecursiveCharacterTextSplitter
langchain-chroma>=0.1.0          # Chroma 向量存储

# LangGraph（必做）
langgraph>=0.0.40

# LangSmith 可观测性（必做）
langsmith>=0.1.0

# 向量存储
chromadb>=0.4.0

# Tongyi/DashScope
dashscope>=1.14.0

# UI
streamlit>=1.30.0

# PDF 解析
pymupdf>=1.23.0

# 工具
python-dotenv>=1.0.0
pydantic>=2.0.0
rich>=13.0.0
httpx>=0.25.0
```

## 2.3 环境变量配置（重要！）

```bash
# .env 文件

# Tongyi/DashScope
DASHSCOPE_API_KEY=sk-xxx

# LangSmith 追踪（必须配置！兼容写法）
LANGCHAIN_TRACING_V2=true

# 认证 Key（两个都写，值相同，兼容性最好）
LANGCHAIN_API_KEY=lsv2_xxx
LANGSMITH_API_KEY=lsv2_xxx

# 项目名（两个都写，值相同）
LANGCHAIN_PROJECT=xlearning-agent
LANGSMITH_PROJECT=xlearning-agent
```

> ⚠️ **注意**：`LANGCHAIN_TRACING_V2=true` 是开启追踪的开关。两套 Key/Project 同时写是为了兼容不同环境，避免"明明配了却不出 trace"。

---

# 3. 系统架构

## 3.1 七层架构图

```
┌─────────────────────────────────────────────────────────────────┐
│  Layer 7: 展示层 (Presentation)                                  │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │  Streamlit Web UI                                           ││
│  │  • 对话界面（流式输出）                                      ││
│  │  • 文件上传（PDF/Markdown）                                  ││
│  │  • 进度可视化（图表/进度条）                                  ││
│  │  • 模式切换（单独/协调）                                      ││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
                                   ↓
┌─────────────────────────────────────────────────────────────────┐
│  Layer 6: 可观测层 (Observability)                               │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │  LangSmith / Phoenix                                        ││
│  │  • 调用链追踪（每次 LLM 调用）                                ││
│  │  • Token 统计（成本监控）                                     ││
│  │  • 延迟监控（性能优化）                                       ││
│  │  • 错误追踪（问题定位）                                       ││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
                                   ↓
┌─────────────────────────────────────────────────────────────────┐
│  Layer 5: 协调层 (Coordinator)                                   │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │  Orchestrator / MainAgent                                   ││
│  │  • 意图识别（用户想做什么）                                   ││
│  │  • 模式选择（单独/协调）                                      ││
│  │  • Agent 调度（按顺序/条件调用）                              ││
│  │  • 状态管理（当前进度、上下文）                               ││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
                                   ↓
┌─────────────────────────────────────────────────────────────────┐
│  Layer 4: 功能 Agent 层 (Functional Agents)                      │
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐       │
│  │ 📋 Planner    │  │ 🎓 Tutor      │  │ ✅ Validator  │       │
│  │ (ReActAgent)  │  │ (SimpleAgent) │  │ (SimpleAgent) │       │
│  │               │  │               │  │               │       │
│  │ 输入类型识别  │  │ Free 对话     │  │ Quiz 生成     │       │
│  │ GitHub 分析   │  │ Quiz 模式     │  │ 答案评分      │       │
│  │ PDF 分析      │  │ 知识讲解      │  │ 进度评估      │       │
│  │ 计划生成      │  │ RAG 检索      │  │ 报告生成      │       │
│  └───────────────┘  └───────────────┘  └───────────────┘       │
└─────────────────────────────────────────────────────────────────┘
                                   ↓
┌─────────────────────────────────────────────────────────────────┐
│  Layer 3: 专业处理层 (Specialists)                               │
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐       │
│  │ResourceSearcher│  │ RepoAnalyzer  │  │ PDFAnalyzer   │       │
│  │ 多源资源搜索  │  │ GitHub 仓库   │  │ PDF 论文      │       │
│  │ Bilibili/YT   │  │ README 提取   │  │ 结构提取      │       │
│  │ Google/GitHub  │  │ 技术栈识别    │  │ 关键信息      │       │
│  └───────────────┘  └───────────────┘  └───────────────┘       │
│  ┌───────────────┐                                              │
│  │ QuizMaker     │  ← 可选功能                                  │
│  │ 题目生成      │                                              │
│  │ 难度控制      │                                              │
│  └───────────────┘                                              │
└─────────────────────────────────────────────────────────────────┘
                                   ↓
┌─────────────────────────────────────────────────────────────────┐
│  Layer 2: RAG 知识层 (Knowledge)                                 │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │  ChromaDB 向量存储                                          ││
│  │  • Embedding（OpenAI / HuggingFace）                        ││
│  │  • 文档切分（chunk_size=1000, overlap=200）                  ││
│  │  • 相似度检索（Top-5）                                       ││
│  │  • 元数据过滤（按领域/来源）                                  ││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
                                   ↓
┌─────────────────────────────────────────────────────────────────┐
│  Layer 1: 基础设施层 (Infrastructure)                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ Provider     │  │ FileManager  │  │ Config       │          │
│  │ LLM 抽象     │  │ 文件管理     │  │ 配置管理     │          │
│  │ 工厂模式     │  │ 持久化       │  │ 环境变量     │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
```

## 3.2 为什么是七层？

| 层级 | 职责 | 设计原则 |
|------|------|---------|
| 展示层 | 用户交互 | 关注点分离，UI 不依赖业务逻辑 |
| 可观测层 | 监控追踪 | 横切关注点，不侵入业务代码 |
| 协调层 | 流程编排 | 单一职责，只负责调度 |
| 功能层 | 核心业务 | 每个 Agent 职责明确 |
| 专业层 | 特定任务 | 可复用，可独立测试 |
| 知识层 | 数据检索 | 存储与检索分离 |
| 基础层 | 通用能力 | 抽象复用，易于替换 |

---

# 4. 模块拆分与能力要求

## 4.1 模块能力矩阵

| 模块 | 核心文件 | 需要的知识 | 难度 | 预计时间 |
|------|---------|-----------|------|---------|
| **Provider 层** | `providers/` | 工厂模式、OpenAI API | ⭐⭐ | 0.5天 |
| **RAG 层** | `rag/` | 向量数据库、Embedding、检索 | ⭐⭐⭐ | 1天 |
| **Planner Agent** | `agents/planner.py` | ReAct 模式、Prompt Engineering | ⭐⭐⭐⭐ | 1天 |
| **Tutor Agent** | `agents/tutor.py` | 对话管理、流式输出 | ⭐⭐⭐ | 1天 |
| **Validator Agent** | `agents/validator.py` | 评分逻辑、报告生成 | ⭐⭐⭐ | 0.5天 |
| **Orchestrator** | `agents/orchestrator.py` | 状态机思维、流程编排 | ⭐⭐⭐⭐ | 1天 |
| **ResourceSearcher** | `specialists/resource_searcher.py` | 多平台 API、搜索聚合 | ⭐⭐⭐ | 1天 |
| **PDF 解析** | `specialist/pdf_analyzer.py` | PyMuPDF、文本提取 | ⭐⭐⭐ | 0.5天 |
| **GitHub 分析** | `specialist/repo_analyzer.py` | GitHub API、代码理解 | ⭐⭐⭐ | 0.5天 |
| **Quiz 生成** | `specialist/quiz_maker.py` | 题目设计、难度控制 | ⭐⭐⭐ | 0.5天 |
| **LangSmith** | `observability/tracing.py` | 追踪原理、装饰器 | ⭐⭐ | 0.5天 |
| **Streamlit UI** | `app.py` | Streamlit 组件、状态管理 | ⭐⭐⭐ | 1.5天 |
| **[可选] LangGraph** | `orchestrator_langgraph.py` | 状态机、LangGraph API | ⭐⭐⭐⭐ | 1天 |

## 4.2 每个模块的核心能力

### Provider 层

```python
# 需要掌握：
# 1. 抽象基类设计
# 2. 工厂模式
# 3. OpenAI API 调用

from abc import ABC, abstractmethod

class LLMProvider(ABC):
    @abstractmethod
    def chat(self, messages: list) -> str: ...
    
    @abstractmethod
    def stream(self, messages: list): ...

class ProviderFactory:
    @classmethod
    def create(cls, name: str) -> LLMProvider:
        providers = {"openai": OpenAIProvider, "deepseek": DeepSeekProvider}
        return providers[name]()
```

### RAG 层

```python
# 需要掌握：
# 1. 文本切分策略
# 2. 向量化原理
# 3. 相似度检索

from chromadb import Client
from langchain_text_splitters import RecursiveCharacterTextSplitter

class RAGEngine:
    def __init__(self):
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
        self.db = Client()
        
    def add_document(self, text: str, metadata: dict):
        chunks = self.splitter.split_text(text)
        # 向量化并存储...
        
    def retrieve(self, query: str, k: int = 5) -> list:
        # 相似度检索...
```

### Planner Agent

```python
# 需要掌握：
# 1. ReAct 模式（Thought → Action → Observation）
# 2. 工具调用
# 3. Prompt Engineering

class PlannerAgent(ReActAgent):
    """
    ReAct 工作流程：
    1. Thought: 分析用户输入类型
    2. Action: 调用相应工具（GitHub/PDF分析）
    3. Observation: 获取分析结果
    4. Thought: 规划学习路径
    5. Finish: 输出学习计划
    """
```

---

# 5. 设计决策与借鉴来源

## 5.1 关键设计决策

### 决策1：为什么用 HelloAgents 而不是 LangChain？

| 考量因素 | HelloAgents | LangChain | 决策 |
|---------|-------------|-----------|------|
| 学习曲线 | 简单 | 复杂 | ✅ HelloAgents |
| 代码可读性 | 高 | 中 | ✅ HelloAgents |
| 面试知名度 | 低 | 高 | ⚠️ LangChain |
| 概念理解深度 | 能看懂源码 | 被抽象层遮蔽 | ✅ HelloAgents |

**最终决策**：使用 HelloAgents，但在简历上写"基于 ReAct 模式"而非框架名

**面试话术**：
> "我选择 HelloAgents 是因为它的源码只有几百行，我能完全理解 ReActAgent 是如何实现 Thought-Action-Observation 循环的。这比用 LangChain 调 API 更能展示我对 Agent 原理的理解。当然，这两个框架的核心概念是一致的。"

### 决策2：为什么用 Orchestrator 而不是 LangGraph？

| 考量因素 | 手写 Orchestrator | LangGraph |
|---------|------------------|-----------|
| 实现复杂度 | 简单 | 需要学习 API |
| 灵活性 | 完全可控 | 受框架约束 |
| 可视化 | 无 | 有流程图 |
| 14天能否完成 | ✅ 能 | ⚠️ 可能超时 |

**最终决策**：主要用 Orchestrator，LangGraph 作为可选扩展

**面试话术**：
> "我实现了一个 Orchestrator 来编排多 Agent 工作流，本质上就是 LangGraph 状态机的简化版。后来我又用 LangGraph 重写了一遍，对比发现两者的核心思想一致：都是把复杂任务拆成节点，用边定义执行顺序。"

### 决策3：为什么三层 Agent 架构？

**借鉴来源**：Yixiang-Wu-LearningAgent

| 层级 | 职责 | 好处 |
|------|------|------|
| 协调层 | 意图识别、调度 | 单一职责，易于扩展 |
| 功能层 | 核心业务 | 职责明确，独立测试 |
| 专业层 | 特定任务 | 可复用，可替换 |

**面试话术**：
> "三层架构实现了关注点分离。协调层只负责'谁来做'，不关心'怎么做'；功能层封装核心逻辑；专业层处理具体任务。这样我可以独立测试每一层，也方便后续扩展新功能。"

## 5.2 从其他项目借鉴的内容

### 从 Yixiang-Wu-LearningAgent 借鉴

| 借鉴内容 | 原始实现 | 我的改进 |
|---------|---------|---------|
| 三层 Agent 架构 | 协调→功能→专业 | 保持不变 |
| 双模式学习 | Free/Quiz | 保持不变 |
| FileManager | 文件管理 | 增加 RAG 集成 |
| 会话状态管理 | 临时文件 | 保持不变 |
| 流式输出 | should_stream() | 保持不变 |

### 从 melxy1997-ColumnWriter 借鉴

| 借鉴内容 | 原始实现 | 我的改进 |
|---------|---------|---------|
| Orchestrator 协调 | 规划→写作→评审→修订 | 改为 规划→学习→验证→总结 |
| 多 Agent 模式 | Plan-and-Solve + ReAct + Reflection | 主要用 ReAct，Reflection 可选 |
| 质量闭环 | 评分<75 重新修改 | Quiz 评分 + 进度报告 |
| 错误恢复 | 降级处理 | 采用相同策略 |
| 缓存机制 | 规划结果缓存 | 计划文件持久化 |

### 从 Apricity-InnocoreAI 借鉴

| 借鉴内容 | 原始实现 | 我的改进 |
|---------|---------|---------|
| Agent 命名风格 | Hunter/Miner/Coach/Validator | 改为 Planner/Tutor/Validator |
| 四大 Agent 分工 | 搜索/分析/写作/校验 | 改为 规划/教学/验证 |
| PDF 解析 | 结构化提取 | 采用相同思路 |

---

# 6. 用户使用流程

## 6.1 完整用户旅程

> **v0.4.0 更新**：核心流程从 Plan→Study→Quiz 简化为 Plan→Study，Quiz 降级为可选。
> 新增资源聚合能力，学习计划包含真实学习资源。

```
┌─────────────────────────────────────────────────────────────────┐
│                      用户使用流程图 (v0.4.0)                     │
└─────────────────────────────────────────────────────────────────┘

用户打开应用
     │
     ▼
┌─────────────┐
│ 首页        │
│ 上传 PDF /  │
│ 粘贴 URL /  │
│ 输入主题    │
└─────────────┘
     │
     ▼
┌──────────────────────────────────────────────────────────────┐
│                    Plan (学习路径)                            │
│  • Planner 分析输入 → 生成 3-5 阶段学习计划                  │
│  • ResourceSearcher 为每个阶段搜索真实资源                    │
│  • 输出：结构化学习路径 + Bilibili/YouTube/Google/GitHub 资源 │
└──────────────────────────────────────────────────────────────┘
     │
     ▼
┌──────────────────────────────────────────────────────────────┐
│                    Study (学习 + 资源探索)                    │
│  • Tutor Agent 互动教学（RAG 增强）                          │
│  • 会话级进度追踪（ProgressTracker）                         │
│  • 动态调整学习大纲                                          │
│  • 可随时搜索更多资源                                        │
│  • [可选] 自测一下 → Quiz                                    │
└──────────────────────────────────────────────────────────────┘
     │
     ▼
┌─────────────────────┐
│ 完成！查看总结      │
│ • 学习路径 + 资源   │
│ • 学习进度          │
│ • [可选] 测验报告   │
└─────────────────────┘
```

## 6.2 典型场景示例

### 场景1：学习一个 GitHub 项目

```
用户：我想学习 https://github.com/langchain-ai/langchain

系统：
📋 Planner Agent 开始工作...
   • 识别输入类型：GitHub URL
   • 调用 RepoAnalyzer 分析仓库
   • 提取技术栈：Python, LLM, Agent
   
🎯 请问你想达到什么学习程度？
   1. 能看懂源码
   2. 能用它开发项目
   3. 能给它贡献代码

用户：2. 能用它开发项目

系统：
📝 正在生成学习计划...
   
# LangChain 学习计划

## 阶段1：基础概念（3天）
- LLM 调用
- Prompt Template
- Chain 基础

## 阶段2：核心组件（4天）
- Agent
- Tool
- Memory

...
```

### 场景2：通过 PDF 论文学习

```
用户：[上传 attention_is_all_you_need.pdf]

系统：
📋 Planner Agent 开始工作...
   • 识别输入类型：PDF 论文
   • 调用 PDFAnalyzer 解析
   • 提取标题：Attention Is All You Need
   • 提取核心概念：Self-Attention, Multi-Head, Transformer
   
🎯 请问你想达到什么学习程度？

用户：能理解并实现 Transformer

系统：
📝 正在生成学习计划...
[计划内容自动入 RAG 库]
```

---

# 7. 数据流向

## 7.1 数据流向图

```
┌─────────────────────────────────────────────────────────────────┐
│                        数据流向图                                │
└─────────────────────────────────────────────────────────────────┘

                    用户输入
                       │
        ┌──────────────┼──────────────┐
        ▼              ▼              ▼
   ┌─────────┐   ┌─────────┐   ┌─────────┐
   │ 领域描述 │   │GitHub URL│   │PDF 文件 │
   └─────────┘   └─────────┘   └─────────┘
        │              │              │
        └──────────────┼──────────────┘
                       ▼
              ┌─────────────────┐
              │  Planner Agent  │
              │  (类型识别)     │
              └─────────────────┘
                       │
        ┌──────────────┼──────────────┐
        ▼              ▼              ▼
   ┌─────────┐   ┌─────────┐   ┌─────────┐
   │直接分析  │   │RepoAnalyzer│  │PDFAnalyzer│
   └─────────┘   └─────────┘   └─────────┘
        │              │              │
        └──────────────┼──────────────┘
                       ▼
              ┌─────────────────┐
              │  分析结果       │
              │  {domain, tech_stack, prerequisites}
              └─────────────────┘
                       │
                       ▼
              ┌─────────────────┐
              │  LLM 生成计划   │◄───── Provider 层
              └─────────────────┘
                       │
        ┌──────────────┼──────────────┐
        ▼              ▼              ▼
   ┌─────────┐   ┌─────────┐   ┌─────────┐
   │FileManager│  │ChromaDB │   │LangSmith│
   │(保存计划) │  │(向量化)  │   │(Trace)  │
   └─────────┘   └─────────┘   └─────────┘
        │              │
        ▼              ▼
   ┌────────────────────────────────────┐
   │  ~/.learningAgent/{domain}/       │
   │  ├── plan.md                      │
   │  ├── knowledge/                   │
   │  │   ├── knowledge_summary.md     │
   │  │   └── *.md (用户笔记)          │
   │  └── sessions/                    │
   │      └── session_*.md (会话记录)  │
   └────────────────────────────────────┘
```

## 7.2 关键数据结构

```python
# 学习计划
class LearningPlan(BaseModel):
    domain: str                    # 学习领域
    goal: str                      # 学习目标
    duration: str                  # 预计时长
    phases: List[LearningPhase]    # 阶段列表
    prerequisites: List[str]       # 前置知识
    resources: List[Resource]      # 推荐资源

# Quiz 题目
class Quiz(BaseModel):
    questions: List[Question]      # 问题列表
    difficulty: float              # 难度 0-1
    topics: List[str]              # 知识点覆盖

# 评估报告
class ProgressReport(BaseModel):
    domain: str                    # 学习领域
    total_sessions: int            # 总会话数
    quiz_accuracy: float           # Quiz 准确率
    mastered_topics: List[str]     # 掌握的知识点
    suggestions: List[str]         # 改进建议
```

---

# 8. 面试技术点与逻辑链

## 8.1 核心技术点逻辑链

### 逻辑链1：为什么需要 RAG？

```
问题：LLM 知识有时效性和局限性
  ↓
解决方案：引入外部知识库（RAG）
  ↓
实现方式：用户上传资料 → 切分 → 向量化 → 存储
  ↓
使用时：用户提问 → 相似度检索 → 组装上下文 → LLM 生成
  ↓
效果：答案基于用户自己的学习材料，更准确、更个性化
```

**面试问答**：
> **Q: 为什么要集成 RAG？**
> 
> A: LLM 的知识有时效性，而且不了解用户自己的学习材料。通过 RAG，用户上传的 PDF 论文、GitHub 项目都会被向量化存储。当用户提问时，先检索相关内容作为上下文，再让 LLM 基于这些内容回答。这样既利用了 LLM 的推理能力，又保证了答案的准确性和个性化。

### 逻辑链2：为什么需要三层 Agent 架构？

```
问题：单个 Agent 职责过多，难以维护
  ↓
解决方案：分层设计，职责单一
  ↓
协调层：只负责"谁来做"，不关心"怎么做"
  ↓
功能层：封装核心业务（规划/教学/验证）
  ↓
专业层：处理具体任务（PDF解析/GitHub分析/Quiz生成）
  ↓
好处：
  • 每层可独立测试
  • 方便扩展新功能
  • 代码可读性高
```

**面试问答**：
> **Q: 三层架构的设计思路是什么？**
> 
> A: 我借鉴了软件工程的分层设计原则。协调层是"调度员"，只负责识别用户意图、选择执行模式、调度合适的 Agent；功能层是"执行者"，每个 Agent 负责一个核心业务；专业层是"工具箱"，提供可复用的能力。这样设计的好处是职责单一、易于测试、方便扩展。

### 逻辑链3：为什么需要 LangSmith？

```
问题：Agent 系统难以调试
  ↓
原因：多次 LLM 调用 + 工具调用，出错难以定位
  ↓
解决方案：全链路追踪（LangSmith）
  ↓
追踪内容：
  • 每次 LLM 调用的输入/输出
  • Token 消耗
  • 响应时间
  • 错误堆栈
  ↓
效果：
  • 问题定位：可以看到哪一步出错
  • 成本优化：知道哪个 Agent 消耗最多
  • 性能优化：找到延迟瓶颈
```

**面试问答**：
> **Q: 为什么要集成 LangSmith？**
> 
> A: Agent 系统的调试非常困难，因为一次用户请求可能触发多次 LLM 调用和工具调用。如果出了问题，很难定位是哪一步出错的。LangSmith 可以记录每次调用的完整信息，我可以在控制台看到调用链、耗时、Token 消耗。有一次我发现生成计划特别慢，通过 Trace 发现是 GitHub API 超时了，而不是 LLM 的问题。

### 逻辑链4：为什么需要双模式（单独/协调）？

```
问题：用户需求多样
  ↓
场景1：用户只想生成计划，不想立即学习
  → 需要"单独模式"，精细控制
  ↓
场景2：用户想一键完成完整流程
  → 需要"协调模式"，自动编排
  ↓
解决方案：双模式设计
  ↓
实现：Orchestrator 统一入口，根据模式选择执行路径
```

**面试问答**：
> **Q: 双模式设计有什么好处？**
> 
> A: 这是借鉴 InnocoreAI 的设计。单独模式适合想精细控制的用户，比如只想生成计划、或者只想做 Quiz；协调模式适合想一键完成全流程的用户，从规划到学习到验证一气呵成。这种设计增加了灵活性，覆盖了更多使用场景。

### 逻辑链5：Provider 抽象层的设计思路

```
问题：业务代码直接依赖具体的 LLM 服务商
  ↓
问题后果：
  • 切换模型要改很多代码
  • 无法根据任务选择不同模型
  • 测试困难（需要真实 API）
  ↓
解决方案：抽象层 + 工厂模式
  ↓
实现：
  • LLMProvider 抽象基类
  • OpenAIProvider / DeepSeekProvider 具体实现
  • ProviderFactory 根据配置创建
  ↓
好处：
  • 一行配置切换模型
  • 不同任务用不同模型（成本优化）
  • 可以 Mock 测试
```

**面试问答**：
> **Q: Provider 抽象层解决了什么问题？**
> 
> A: 解决了 LLM 调用的强耦合问题。通过抽象基类定义统一接口，工厂模式根据配置创建具体 Provider。这样业务代码不依赖具体服务商，我可以一行配置切换 OpenAI 和 DeepSeek。而且可以根据任务复杂度选择模型——简单任务用便宜的 deepseek-chat，复杂推理用 gpt-4o。

## 8.2 技术细节追问预测

| 追问 | 参考回答 |
|------|---------|
| RAG 检索效果怎么评估？ | 用 hit@k 评估召回率，人工抽检 10 条评估准确性 |
| 分块大小怎么确定的？ | chunk_size=1000 是经验值，太大上下文放不下，太小丢失语义 |
| Quiz 难度怎么控制？ | difficulty 参数 0-1，影响 Prompt 要求的问题复杂度 |
| 多 Agent 怎么保证一致性？ | 共享 FileManager，统一管理领域数据 |
| 会话状态怎么管理？ | 用临时文件 .current_session.txt 存储当前状态 |

---

# 9. 可选技术扩展

## 9.1 可选项1：LangGraph 重写 Orchestrator

### 什么时候做？
- Day 13 作为可选任务
- 如果面试要求强调 LangChain 生态

### 实现方式

```python
# orchestrator_langgraph.py
from langgraph import StateGraph
from typing import TypedDict

class LearningState(TypedDict):
    domain: str
    plan: str
    current_topic: str
    quiz_score: float
    status: str  # planning | learning | validating | done

def planner_node(state: LearningState) -> LearningState:
    plan = planner_agent.run(state["domain"])
    return {**state, "plan": plan, "status": "learning"}

def tutor_node(state: LearningState) -> LearningState:
    # 教学逻辑...
    return {**state, "status": "validating"}

def validator_node(state: LearningState) -> LearningState:
    score = validator_agent.evaluate(...)
    return {**state, "quiz_score": score, "status": "done"}

# 构建状态图
graph = StateGraph(LearningState)
graph.add_node("planner", planner_node)
graph.add_node("tutor", tutor_node)
graph.add_node("validator", validator_node)

graph.add_edge("planner", "tutor")
graph.add_edge("tutor", "validator")

graph.set_entry_point("planner")
graph.set_finish_point("validator")

# 编译并运行
app = graph.compile()
result = app.invoke({"domain": "Python", "status": "planning"})
```

### 面试话术

> "我实现了两个版本的 Orchestrator：一个是手写的顺序调用，一个是用 LangGraph 的状态机。对比下来，LangGraph 的优势是有标准化的抽象和可视化，但手写版更灵活、更容易理解底层原理。两者的核心思想是一致的。"

## 9.2 可选项2：FastAPI 服务化

### 什么时候做？
- Day 13-14 作为可选任务
- 如果想展示后端能力

### 实现方式

```python
# api/main.py
from fastapi import FastAPI, UploadFile
from pydantic import BaseModel

app = FastAPI()

class CreatePlanRequest(BaseModel):
    domain: str
    goal: str

@app.post("/api/plan")
async def create_plan(request: CreatePlanRequest):
    plan = await planner_agent.run(request.domain)
    return {"plan": plan}

@app.post("/api/upload")
async def upload_document(file: UploadFile):
    # 保存文件 → PDF 解析 → 入 RAG 库
    return {"status": "success"}

@app.get("/api/progress/{domain}")
async def get_progress(domain: str):
    report = validator_agent.assess_progress(domain)
    return report
```

## 9.3 可选项总览

| 可选项 | 预计时间 | 面试价值 | 建议 |
|--------|---------|---------|------|
| LangGraph 重写 | 1天 | ⭐⭐⭐⭐⭐ | 强烈建议 |
| FastAPI 服务化 | 1天 | ⭐⭐⭐ | 时间充裕可做 |
| Reflection Agent | 0.5天 | ⭐⭐⭐ | 可选 |
| 更多 Provider | 0.5天 | ⭐⭐ | 可选 |

---

# 10. 14天开发计划

## 10.1 完整日程表

| 阶段 | 日期 | 主要任务 | 产出 |
|------|------|---------|------|
| **基础搭建** | Day 1 | 源码阅读 + 项目初始化 | 项目骨架 |
| | Day 2 | Provider 抽象层 | 2个 Provider |
| | Day 3 | RAG 知识层 | ChromaDB 可用 |
| **核心 Agent** | Day 4 | Planner + LangSmith | 计划生成 + Trace |
| | Day 5 | Tutor + RAG 集成 | 互动教学可用 |
| | Day 6 | Validator + Quiz | 测验评分可用 |
| | Day 7 | Orchestrator 双模式 | 协调模式可用 |
| **专业处理** | Day 8 | PDF 解析增强 | PDF 可分析 |
| | Day 9 | GitHub 分析增强 | 仓库可分析 |
| | Day 10 | Streamlit UI 基础 | 界面骨架 |
| | Day 11 | Streamlit UI 完善 | 完整界面 |
| **优化收尾** | Day 12 | Eval 评测 + 优化 | 评测报告 |
| | Day 13 | 文档 + **[可选]LangGraph** | README + 可选扩展 |
| | Day 14 | 简历化 + 演示 | 简历 + 视频 |

## 10.2 每日 Checklist

### Day 13 可选任务详情

**必做**：
- [ ] Bug 修复
- [ ] README 文档
- [ ] 使用说明

**可选**：
- [ ] LangGraph 版本 Orchestrator（强烈建议）
- [ ] FastAPI 基础接口

---

# 11. 简历写法

## 11.1 中文版（推荐）

**AI 智能学习助手** | Python, LangChain/LangGraph, RAG, Streamlit

- 基于 **ReAct 推理模式**构建，采用**三层 Agent 架构**（协调层→功能层→专业层），实现学习规划、互动教学、资源聚合的完整闭环
- 实现**多源资源聚合引擎**（ResourceSearcher），从 Bilibili、YouTube、Google、GitHub 等平台搜索真实学习资源，自动关联到学习路径
- 支持**动态学习路径**：会话级进度追踪，根据学习反馈动态调整学习大纲和资源推荐
- 集成 **RAG 知识检索**（ChromaDB），支持 **PDF 论文解析**和 **GitHub 仓库分析**，实现个性化知识问答
- 设计 **Provider 抽象层**，通过工厂模式支持 Tongyi/Qwen 等模型无缝切换
- 接入 **LangSmith** 实现 Agent 全链路追踪，支持 Token 消耗统计和调用链可视化
- 使用 **LangGraph** 实现状态机版本 Orchestrator，对比两种工作流编排方式

## 11.2 英文版

**AI Learning Assistant** | Python, LangChain/LangGraph, RAG, Streamlit

- Built on **ReAct reasoning pattern** with a **3-layer Agent architecture** (Coordinator → Functional → Specialist) for end-to-end learning workflow
- Implemented **multi-source resource aggregation engine** (ResourceSearcher) that searches real learning resources from Bilibili, YouTube, Google, and GitHub, auto-linking them to learning paths
- Supported **dynamic learning paths**: session-level progress tracking with adaptive syllabus adjustment based on learner feedback
- Integrated **RAG-based retrieval** (ChromaDB) with **PDF parsing** and **GitHub repo analysis** for personalized Q&A
- Designed **Provider abstraction layer** with factory pattern, supporting multiple LLM providers seamlessly
- Enabled **LangSmith observability** for full-stack tracing, token tracking, and call chain visualization
- Implemented **LangGraph** version of Orchestrator for comparison of workflow orchestration approaches

---

# 12. 原两周计划价值提取

## 12.1 保留的有价值内容

| 原计划内容 | 在本项目中的体现 | 状态 |
|-----------|-----------------|------|
| **ReAct 模式** | Planner Agent 使用 ReActAgent | ✅ 完全保留 |
| **Tool Calling** | RepoAnalyzer / PDFAnalyzer / QuizMaker | ✅ 完全保留 |
| **RAG + Chroma** | RAG 知识层，ChromaDB | ✅ 完全保留 |
| **Eval 评测** | Quiz 评分 + 进度报告 | ✅ 完全保留 |
| **Trace 日志** | LangSmith 集成 | ✅ 完全保留 |
| **Memory 记忆** | FileManager 会话持久化 | ✅ 完全保留 |
| **LangGraph Workflow** | Orchestrator（可选 LangGraph 版本） | ✅ 可选保留 |
| **FastAPI 服务化** | 可选扩展 | ⚠️ 可选保留 |

## 12.2 不再需要的内容

| 原计划内容 | 原因 |
|-----------|------|
| 400+ 文档切片的知识库构建 | 项目主题改变，改为用户自己上传资料 |
| 4 个领域工具（代码示例/概念对比/自测题/通俗解释） | 简化为 3 个专业处理器 |
| 人工抽检 10 条 + 回归测试 | 简化评测流程，保留核心指标 |
| 15+ 字段的 Trace 日志 | LangSmith 自动处理 |
| report.md 详细评测报告 | 简化为进度报告 |

## 12.3 核心理念延续

| 原计划理念 | 在本项目中的延续 |
|-----------|-----------------|
| "先证据后结论" | RAG 检索后再回答 |
| "评测早介入" | Quiz 贯穿学习过程 |
| "能现场演示" | Streamlit 可视化界面 |
| "有数据说话" | Quiz 准确率、进度报告 |
| "口径清楚" | 面试逻辑链文档化 |

---

# 13. 结语

## 你现在拥有什么

1. ✅ **完整的技术规格书**：架构、模块、数据流
2. ✅ **14天详细计划**：每日任务和 Checklist
3. ✅ **面试逻辑链**：每个设计决策都有理由
4. ✅ **可选扩展**：LangGraph / FastAPI
5. ✅ **简历话术**：中英文双版本
6. ✅ **价值继承**：原两周计划的精华

## 下一步

1. **今天**：通读这份文档，确认理解
2. **明天**：开始 Day 1，阅读源码
3. **14天后**：拥有一个简历级项目！

---

> 📅 文档版本：v3.0 Final
> 🕐 创建时间：2026-02-05 02:00
> 🎯 目标：14天完成，简历加分！
> 💪 加油，你一定可以的！
