<p align="center">
  <!-- TODO: 替换为项目 Logo -->
  <img src="docs/assets/logo.png" alt="LearningIN28 Logo" width="120" />
</p>

<h1 align="center">LearningIN28</h1>

<p align="center">
  <strong>28 天，掌握任何技能。</strong><br/>
  一个 AI 驱动的学习助手，把任何主题变成结构化的每日学习计划——智能资源发现、自适应辅导、每日打卡反馈，帮你保持节奏。
</p>

<p align="center">
  <!-- TODO: 替换为实际 GitHub 地址 -->
  <a href="#"><img src="https://img.shields.io/github/stars/your-username/LearningIN28?style=social" alt="GitHub Stars" /></a>
  <a href="#"><img src="https://img.shields.io/github/license/your-username/LearningIN28" alt="License" /></a>
  <a href="#"><img src="https://img.shields.io/badge/python-3.10+-blue.svg" alt="Python" /></a>
  <a href="#"><img src="https://img.shields.io/badge/react-18-61dafb.svg" alt="React" /></a>
  <a href="#"><img src="https://img.shields.io/badge/PRs-welcome-brightgreen.svg" alt="PRs Welcome" /></a>
</p>

<p align="center">
  <a href="README.md">English</a> | <strong>中文</strong>
</p>

<p align="center">
  <a href="#-快速开始">快速开始</a> •
  <a href="#-用户旅程">用户旅程</a> •
  <a href="#-功能特性">功能特性</a> •
  <a href="#-系统架构">系统架构</a> •
  <a href="#-开发路线">开发路线</a> •
  <a href="#-参与贡献">参与贡献</a>
</p>

---

<!-- TODO: 替换为产品全貌截图或 GIF -->
<p align="center">
  <img src="docs/assets/hero-screenshot.png" alt="LearningIN28 三栏布局全貌" width="900" />
</p>


## 💡 为什么选择 LearningIN28？

大多数 AI 学习工具止步于"和文档聊天"。LearningIN28 更进一步——它给你的学习一个**截止日期、一套结构、一个每日节奏**。

| 痛点 | LearningIN28 怎么解决 |
|---|---|
| 🗓️ "改天再学"综合症 | **3–28 天有限周期计划**——选一个截止日，AI 生成每日路线图 |
| 📚 学习资源散落各处 | **6 平台搜索聚合**——小红书、B站、YouTube、GitHub、Google、知乎，两阶段质量漏斗筛选 |
| 🤖 AI 回答千篇一律 | **材料感知聊天**——把 PDF 拖进对话框，AI 基于你的材料回答 |
| 🧠 AI 记不住你说过什么 | **Episodic Memory**——AI 跨会话记住你的困惑点，清空对话也不丢失 |
| 📊 学了多少心里没数 | **每日打卡 + AI 总结**——完成当天任务，获得鼓励和跨天知识关联分析 |

---

## 🎬 用户旅程

> 小明，大三学生，准备前端面试。他给自己 **14 天** 时间掌握 React。

### Day 0 — 创建计划（2 分钟）

小明新建一个学习计划，设置画像：14 天周期、每天 2 小时、中级水平、目标是面试准备。他上传了 React 官方文档 PDF，然后在 B站和 YouTube 搜索高质量 React 教程——搜索引擎自动翻译关键词、跨平台聚合、两阶段漏斗筛选，最终推荐 10 个精选资源。

<!-- TODO: 替换为创建计划 + 设置画像的截图 -->
<p align="center">
  <img src="docs/assets/journey-01-setup.png" alt="创建学习计划" width="700" />
</p>

### Day 1 — 第一天学习

AI 根据他的画像生成了 14 天学习计划。Day 1：JSX 基础。小明阅读材料，遇到 JSX 表达式和语句的区别时和 AI 聊天答疑。完成当天任务后，他点击"日总结"——AI 生成个性化回顾和鼓励：

> *"Day 1 搞定——JSX 语法已经拿下了。明天的组件组合会直接用到今天学的内容，承上启下。"*

<!-- TODO: 替换为 Day 1 学习界面截图（三栏布局：材料 | 聊天 | Studio） -->
<p align="center">
  <img src="docs/assets/journey-02-day1.png" alt="Day 1 学习界面" width="700" />
</p>

### Day 7 — 中期回顾

学到一半了。小明生成进度报告——AI 分析完成率，识别出薄弱点（Day 5 的 `useEffect` 清理函数他搞了很久），给出针对性复习建议。他生成闪卡——AI 自动把聊天历史中他困惑过的知识点加权，生成更多相关卡片。

<!-- TODO: 替换为进度报告 + 闪卡截图 -->
<p align="center">
  <img src="docs/assets/journey-03-midreview.png" alt="中期回顾" width="700" />
</p>

### Day 14 — 学习完成

小明完成了全部 14 天。他生成思维导图可视化整个知识体系，做一套综合测验（AI 针对他历史薄弱点重点出题），导出学习指南作为面试复习材料。

<!-- TODO: 替换为完成状态截图（思维导图 + 测验） -->
<p align="center">
  <img src="docs/assets/journey-04-complete.png" alt="学习完成" width="700" />
</p>


---

## ✨ 功能特性

### 📋 结构化学习计划
AI 根据你的画像、材料和可用时间生成逐日学习计划（3–28 天）。短周期（3–7 天）聚焦核心概念；中周期（8–14 天）正常节奏含练习日；长周期（15–28 天）包含复习日和实践日。

### 🔍 多源搜索聚合
同时搜索 6 个平台，**两阶段质量漏斗**筛选：
1. **互动数据初筛**——按点赞、评论、相关性排序
2. **LLM 质量评估**——AI 打分并生成摘要和推荐理由

支持平台：小红书 · B站 · YouTube · GitHub · Google · 知乎

<!-- TODO: 替换为搜索界面截图 -->
<p align="center">
  <img src="docs/assets/feature-search.png" alt="多源搜索" width="700" />
</p>

### 💬 材料感知聊天
把材料拖进聊天输入框——AI 基于你的文档回答，而不是泛泛而谈。Studio 工具使用全局 RAG 做综合内容生成。

### 🧠 Episodic Memory（情景记忆）
AI 自动将长对话压缩为情景摘要。清空对话、重新开始——但 AI 仍然记得你上次困惑的地方。这让闪卡、测验、学习指南都更智能。

### 🎯 7 个 Studio 工具

| 工具 | 功能 |
|------|------|
| 📖 学习指南 | 战略层面的知识体系路线图 |
| 📅 学习计划 | 逐日任务分解（严格 JSON，渲染为时间线） |
| 🃏 闪卡 | 问答卡片，自动加权你的困惑点 |
| 📝 测验 | 多题型测试，针对薄弱知识点出题 |
| 🗺️ 思维导图 | 知识结构可视化（markmap.js 渲染） |
| 📊 进度报告 | 数据驱动的学习分析 |
| 📓 日总结 | 每日回顾 + AI 鼓励 + 跨天知识关联 |

所有工具都是**上下文感知**的——根据聊天历史、情景记忆、学习者画像和当前进度自适应调整。

### 🔌 多 Provider 支持
一个 `OpenAICompatibleProvider` 类覆盖所有兼容服务商，无需改代码即可切换：

| Provider | 默认模型 |
|----------|---------|
| DeepSeek（默认） | deepseek-chat (V3, 64K context) |
| OpenAI | gpt-4o-mini |
| 智谱 (GLM) | glm-4-flash |
| Moonshot | moonshot-v1-8k |


---

## 🏗️ 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│  前端：React + TypeScript + Zustand + TailwindCSS            │
│  三栏布局：资源面板 | 聊天区 | Studio 面板                    │
└──────────────────────────┬──────────────────────────────────┘
                           │ REST API + SSE（流式传输）
┌──────────────────────────┴──────────────────────────────────┐
│  后端 API：FastAPI                                           │
│  路由：plans / chat / studio / search / resource / upload     │
├──────────────────────────────────────────────────────────────┤
│  核心逻辑层（src/）                                           │
│  ├── agents/       TutorAgent + Episodic Memory               │
│  ├── providers/    OpenAI 兼容协议抽象（4 家服务商）            │
│  ├── specialists/  搜索模块（6 平台 + 两阶段漏斗）             │
│  └── rag/          ChromaDB 向量存储                           │
├──────────────────────────────────────────────────────────────┤
│  持久化层                                                     │
│  ├── SQLite（WAL 模式）— 8 张表，级联删除                      │
│  └── ChromaDB — text-embedding-v2（DashScope）                │
├──────────────────────────────────────────────────────────────┤
│  可观测层：LangSmith（@traceable 装饰器）                      │
└──────────────────────────────────────────────────────────────┘
```

<!-- TODO: 替换为更精美的架构图（draw.io / Excalidraw 导出） -->

### 搜索流水线详解

搜索模块是整个系统最复杂的部分：

```
用户输入关键词 + 选择平台
  → SearchOrchestrator（三批并发调度）
    → 第一批：API 平台（B站、知乎）— 并行
    → 第二批：需登录平台（小红书）— 串行
    → 第三批：浏览器平台（YouTube、GitHub、Google）— Playwright 无头浏览器
  → EngagementRanker（互动数据初筛）
  → PipelineExecutor（详情提取 → LLM 质量评估）
  → SlotAllocator（按比例选 top-k）
  → SSE 实时推送进度到前端
```

### Prompt 策略

每个 Studio 工具都使用**动态指令拼接**而非静态模板：

```python
# Python 层做条件分支——LLM 收到的是明确、无歧义的指令
def _build_study_guide_instruction(self, all_days, rag_context, profile_text, 
                                     chat_history, current_day_number, episodic_summary):
    parts = [BASE_INSTRUCTION]
    
    if rag_context:
        parts.append("材料为骨架——围绕上传材料组织学习指南结构。")
    else:
        parts.append("无材料模式——生成通用指南并建议上传材料。")
    
    if chat_history and episodic_summary:
        parts.append("结合近期对话和长期记忆作为上下文线索。")
    elif episodic_summary:
        parts.append("无近期对话，但使用情景记忆保持连续性。")
    # ... 更多分支：画像、进度、场景检测
    
    return "\n".join(parts)
```

---

## 🚀 快速开始

### 环境要求

- Python 3.10+
- Node.js 18+
- 至少一个 LLM API Key（推荐 DeepSeek）
- DashScope API Key（用于 text-embedding-v2）

### 1. 克隆 & 安装

```bash
git clone https://github.com/your-username/LearningIN28.git
cd LearningIN28

# 后端
python -m venv venv
# Windows: .\venv\Scripts\activate
# macOS/Linux: source venv/bin/activate
pip install -r requirements.txt

# 前端
cd frontend
npm install
cd ..
```

### 2. 配置

```bash
cp .env.example .env
# 编辑 .env，填入 API Key：
#   DEEPSEEK_API_KEY=sk-xxx
#   DASHSCOPE_API_KEY=sk-xxx
#   LANGSMITH_API_KEY=lsv2-xxx（可选，用于调用追踪）
```

### 3. 启动

```powershell
# Windows 一键启动
.\start_dev.ps1

# 或手动分别启动：
# 终端 1 — 后端
uvicorn backend.main:app --port 8000 --reload

# 终端 2 — 前端
cd frontend && npm run dev
```

打开 `http://localhost:5173`，创建你的第一个学习计划。


---

## 🗺️ 开发路线

- [x] NotebookLM 风格三栏布局 UI
- [x] 多源搜索聚合（6 平台）
- [x] 两阶段质量漏斗（互动数据 + LLM 评估）
- [x] 材料感知聊天（显式附加模式）
- [x] SQLite 统一持久化（8 张表 + WAL 模式）
- [x] Episodic Memory（工作记忆 + 情景摘要）
- [x] PromptBuilder 动态指令拼接
- [x] 多 Provider 支持（4 家 LLM 服务商）
- [x] LangSmith 全链路追踪
- [ ] 全部 7 个 Studio 工具的动态 Prompt 优化
- [ ] 进度环 UI 组件（Day X/N 可视化）
- [ ] LangGraph 版聊天编排器
- [ ] RAG 评测流水线（hit@k 指标）
- [ ] 多模态材料理解（PDF 图片 + VL 模型）
- [ ] 演示视频 & 新手引导优化

---

## 🧪 测试

```bash
# 后端（Pytest + Hypothesis 属性测试）
pytest tests/ -v

# 前端（Vitest）
cd frontend && npx vitest --run
```

项目使用 **Hypothesis 属性测试**覆盖核心模块：搜索配额分配、情景记忆压缩、资源聚合等。

---

## 🤝 参与贡献

欢迎任何形式的贡献——Star、Bug 报告、功能建议、Pull Request 都行。

<!-- TODO: 创建 CONTRIBUTING.md 后取消注释 -->
<!-- 详见 [CONTRIBUTING.md](CONTRIBUTING.md) -->

### 开发须知

- 改后端代码（Python / `.env`）需要重启服务
- 改前端代码通过 Vite HMR 热更新，无需重启
- 数据库字段 snake_case，API 返回 camelCase（自动转换）
- Embedding 模型**固定**为 text-embedding-v2——更换会导致 ChromaDB 向量不兼容

---

## 📜 开源协议

[MIT](LICENSE)

---

## 🙏 致谢

- [LangChain](https://langchain.com) — LLM 框架
- [LangSmith](https://smith.langchain.com) — 可观测性平台
- [ChromaDB](https://www.trychroma.com/) — 向量存储
- [markmap](https://markmap.js.org/) — 思维导图渲染
- [Yixiang-Wu/LearningAgent](https://github.com/Lorry-LY/LearningAgent) — 架构灵感

---

<p align="center">
  <strong>给学习一个截止日期，给自己一个节奏。</strong><br/>
  如果 LearningIN28 帮你学到了新东西，考虑给个 ⭐
</p>
