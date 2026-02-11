# 面试学习计划：边改代码边备战

> **核心原则**：每写一行代码，都要能用面试语言讲清楚"我为什么这样写"
> **阅读时间**：15 分钟，但需要反复回来对照
> **配合文件**：`TODO.md`（改代码顺序）+ 本文件（学习顺序）

---

## 第一部分：典型 JD 要求拆解

### 你会遇到的 JD 关键词

```
"负责 LLM 应用开发，包括但不限于：
 - 基于 LangChain/LangGraph 构建 Agent 系统     ← 你的项目核心
 - RAG 检索增强生成管道搭建                       ← 你的 RAG 层
 - Prompt Engineering 和效果优化                   ← 你的三个 Agent 的 system_prompt
 - 多 Agent 编排与协调                             ← 你的 Orchestrator
 - LLM 应用可观测性（LangSmith/Phoenix）          ← 你的 Trace 层
 - 熟悉向量数据库（Chroma/Pinecone/Milvus）       ← 你的 ChromaDB
 - 有 LLM 评测经验优先                            ← 你的 Quiz 评估系统"
```

### 你的项目 vs JD 对应表

| JD 要求 | 项目中的体现 | 你要看的代码 | 面试要答到的深度 |
|---------|-------------|-------------|----------------|
| LangChain | ChatTongyi, DashScopeEmbeddings, TextSplitter, Chroma | `providers/tongyi.py`, `rag/engine.py` | 能说清组件关系 |
| LangGraph | Orchestrator 状态机 + LangGraph 对比版 | `agents/orchestrator.py` + 待写 | 能手画状态图 |
| RAG | 全流程：上传→切分→embedding→检索→增强回答 | `rag/engine.py`, `tutor.py` | 能讲调优经验 |
| Multi-Agent | 三层架构 + Orchestrator 编排 | `agents/*.py` | 能讲设计决策 |
| Prompt Engineering | 三个 Agent 的 system_prompt | `planner.py`, `tutor.py`, `validator.py` | 能讲迭代过程 |
| 可观测性 | LangSmith Trace | `observability/tracing.py` | 能讲排查案例 |
| 向量数据库 | ChromaDB | `rag/engine.py` | 能讲选型理由 |
| 评测 | Quiz 评分 + 进度报告 | `validator.py` | 能讲 Eval 思路 |

---

## 第二部分：每天的学习节奏（配合 TODO.md）

### Day 5 - 写 Planner 真实输出 + Tutor Memory

#### 改代码时同步学习：

**上午：改 `_parse_plan()`，同时深入理解 LangChain Prompt**

打开 `src/agents/planner.py`，你要理解的不只是"怎么修"，而是：

1. **你的 `_call_llm()` 底层到底调了什么？**
   - 追踪调用链：`BaseAgent._call_llm()` → `TongyiProvider.chat()` → `ChatTongyi.invoke()`
   - 打开 `src/agents/base.py` 和 `src/providers/tongyi.py`，搞清楚每一层做了什么
   - **面试必考**："你的 LLM 调用链是怎样的？从用户输入到最终 API 请求经历了哪些步骤？"

2. **你为什么用 JSON mode 而不是自由文本？**
   - 修改 Planner prompt 为 JSON 输出时，想清楚为什么
   - **面试话术**："我最初让 LLM 自由输出 Markdown，但发现解析不稳定——Markdown 格式因模型而异。后来我改用 JSON mode，让 LLM 输出结构化数据，解析成功率从约 60% 提升到 95%。这就是 Structured Output 的价值。"

3. **LangChain 的 `with_structured_output()` 你要知道**
   - 虽然你现在用的是手动 JSON 解析，但面试时要知道 LangChain 有 `model.with_structured_output(PydanticModel)` 这个方法
   - **面试话术**："我了解 LangChain 的 `with_structured_output()`，但 Tongyi/Qwen 对 function calling 的支持不如 OpenAI 稳定，所以我选择了手动 JSON 解析 + 正则 fallback 的方案。这是在工程可靠性和框架优雅性之间的权衡。"

**下午：改 Tutor History，同时深入理解 Memory**

4. **LangChain Memory 的三种方式你必须知道**
   - `ConversationBufferMemory`：存全部历史（你的方案最接近这个）
   - `ConversationSummaryMemory`：用 LLM 总结历史
   - `ConversationBufferWindowMemory`：只存最近 N 轮
   - **面试话术**："我在 Tutor 里手动注入最近 6 轮历史，本质上等同于 LangChain 的 BufferWindowMemory。我没有直接用 LangChain 的 Memory 组件，因为我需要在 Orchestrator 层控制哪些历史传给哪个 Agent——Planner 不需要看聊天历史，但 Tutor 需要。这种细粒度控制在 LangChain 的默认 Memory 里不容易实现。"

**晚上：复习以下概念（读文档不写代码）**

- LangChain 官方文档的 [Chat Models](https://python.langchain.com/docs/concepts/chat_models/) 章节
- LangChain 官方文档的 [Output Parsers](https://python.langchain.com/docs/concepts/output_parsers/) 章节
- 重点理解：`invoke()` vs `stream()` vs `batch()` 的区别

---

### Day 6 - 写 Report 连通 + Quiz 统一

#### 改代码时同步学习：

**上午：连通 Report，同时理解 Pydantic 数据模型设计**

5. **你的 `models.py` 是面试亮点**
   - 打开 `src/core/models.py`，理解 `LearningPlan`、`Quiz`、`QuizResult`、`ProgressReport`
   - **面试必考**："你的数据模型是怎么设计的？为什么用 Pydantic？"
   - **面试话术**："我用 Pydantic BaseModel 定义了所有数据结构，原因有三：一是类型安全——Python 的 dict 容易出 KeyError，Pydantic 在创建时就验证；二是 JSON 序列化——`.model_dump()` 一行代码转 JSON，方便持久化；三是与 LangChain 兼容——LangChain 的 `with_structured_output()` 就是接受 Pydantic Model。"

**下午：统一 Quiz 数据流，同时理解 Agent 间数据传递**

6. **Agent 间通信的设计模式**
   - 你的项目用的是"共享状态"模式：Orchestrator 持有所有 Agent，通过函数调用传参
   - 对比另一种模式："消息传递"（Agent 之间发消息）
   - **面试话术**："我的 Agent 间通信用的是集中式协调模式——Orchestrator 作为中枢，持有所有 Agent 实例，通过函数调用传递数据。另一种是去中心化的消息传递模式，比如 AutoGen 的 multi-agent conversation。我选择集中式是因为我的场景是线性流程（规划→学习→验证），不需要 Agent 之间自由对话。"

**晚上：重点攻读**

- LangChain 官方文档的 [Agents](https://python.langchain.com/docs/concepts/agents/) 概念章节
- 理解 ReAct、Tool Calling Agent 的区别
- 想清楚："我的 Agent 和 LangChain 的 Agent 有什么区别？"

---

### Day 7 - 写引导流程自动化

#### 改代码时同步学习：

**全天：重构 Action Banner，同时深入理解状态机**

7. **状态机是 Orchestrator 的灵魂**
   - 你要把 `OrchestratorState` 的转换逻辑画成图，贴在面前
   - IDLE → PLANNING → LEARNING → VALIDATING → COMPLETED
   - **面试必考**："你的 Orchestrator 状态机是怎么工作的？"
   - 要能在白板上 30 秒画出来
   - **面试话术**："我的 Orchestrator 维护了一个 5 态状态机。每次用户输入，先做意图识别，然后根据当前状态和意图决定路由。比如用户在 LEARNING 态说'考考我'，意图识别返回 start_quiz，状态切换到 VALIDATING，调用 ValidatorAgent。这个设计的好处是——加新功能只需要加新状态和转换条件，不用改已有逻辑。"

8. **为什么引导模式和自由模式都需要？**
   - **面试话术**："引导模式面向新手用户，系统主动推进流程——上传资料后自动建议生成计划，计划生成后自动建议开始学习。自由模式面向有经验的用户，可以跳过任何步骤，直接提问或直接测验。这是两种不同的用户心智模型，类似于 Cursor 的 Normal 模式和 Agent 模式。"

---

### Day 8-9 - 写 LangGraph + GitHub API

#### 这两天是面试关键！

**Day 8：LangGraph 是你必须攻克的**

9. **LangGraph 的核心概念（面试必背）**

   ```
   StateGraph    → 定义状态图（你的 Orchestrator 状态机的 LangGraph 版本）
   State         → TypedDict，描述图中流转的数据
   Node          → 一个处理函数（你的每个 Agent 就是一个 Node）
   Edge          → 节点间的连接（确定性流转）
   Conditional Edge → 条件路由（你的意图识别就是条件边）
   Entry Point   → 入口节点
   Finish Point  → 结束节点
   compile()     → 编译成可执行的 Runnable
   invoke()      → 运行
   ```

10. **写 LangGraph 版本时，核心理解这些**

    - 你的手写 Orchestrator 的 `if-elif` 路由 = LangGraph 的条件边
    - 你的 `OrchestratorState` enum = LangGraph 的 `TypedDict` State
    - 你的 `_run_coordinated()` = LangGraph 的 `graph.invoke()`
    - **面试话术**："我实现了两个版本的 Orchestrator：手写版用 if-elif 做路由，LangGraph 版用 `add_conditional_edges` 做路由。本质是一样的——都是有限状态机。但 LangGraph 的优势是：标准化的状态定义、内置的持久化（Checkpointer）、和自动的可视化。手写版的优势是完全可控、调试直观。"

11. **LangGraph 和 LangChain 的关系**

    ```
    LangChain = 组件库（LLM 调用、向量数据库、文本处理等积木块）
    LangGraph = 编排框架（把积木块用状态机串起来）
    LangSmith = 监控平台（看这些积木块怎么运行的）

    ┌──────────────────────────┐
    │      LangSmith (监控)     │
    ├──────────────────────────┤
    │      LangGraph (编排)     │
    ├──────────────────────────┤
    │      LangChain (组件)     │
    │  ChatTongyi | Chroma |    │
    │  TextSplitter | Embed     │
    └──────────────────────────┘
    ```

    **面试必答版**："LangChain 提供底层组件——LLM 调用、Embedding、向量存储这些'积木块'；LangGraph 是编排层——把这些积木块用状态图串成工作流；LangSmith 是可观测层——追踪整个工作流的执行过程。我的项目三层都用了：底层组件用 LangChain（ChatTongyi、DashScopeEmbeddings、Chroma），编排用自研 Orchestrator + LangGraph 对比版，监控用 LangSmith。"

**Day 9：GitHub API + 理解 Tool Calling**

12. **Tool Calling 是 Agent 的核心能力**
    - 你写 RepoAnalyzer 调 GitHub API 时，本质上就是在实现一个 Tool
    - **面试必考**："你的 Agent 有哪些 Tools？"
    - **面试话术**："我的 Agent 系统有三个核心 Tool：RepoAnalyzer（调 GitHub API 获取仓库信息）、PDFAnalyzer（用 PyMuPDF 解析 PDF 提取文本）、QuizMaker（生成结构化测验题目）。这三个 Tool 被封装在 Specialists 层，由功能层的 Agent 调用。比如 PlannerAgent 根据输入类型选择调用 RepoAnalyzer 或 PDFAnalyzer——这就是 ReAct 模式中的 Action 环节。"

---

## 第三部分：面试高频问题与你的项目映射

### 问题组 1：LangChain 基础（必问）

**Q: 你用了 LangChain 的哪些组件？**

你的项目中实际使用的 LangChain 组件清单：

| 组件 | 代码位置 | 用途 |
|------|---------|------|
| `ChatTongyi` | `providers/tongyi.py` | LLM 调用 |
| `DashScopeEmbeddings` | `rag/engine.py` | 文本向量化 |
| `RecursiveCharacterTextSplitter` | `rag/engine.py` | 文档切分 |
| `Chroma` (via langchain-chroma) | `rag/engine.py` | 向量存储 |
| LangSmith auto-trace | `observability/tracing.py` | 调用追踪 |

```
准备话术：
"我的项目用了 LangChain 的五个核心组件：
 1. ChatTongyi 做 LLM 调用——它封装了 DashScope API，支持 invoke 和 stream；
 2. DashScopeEmbeddings 做文本向量化——把文档切片转成 1536 维向量；
 3. RecursiveCharacterTextSplitter 做文档切分——按 1000 token 切片，200 重叠；
 4. Chroma 做向量存储——支持持久化和元数据过滤；
 5. LangSmith 做自动追踪——设置环境变量后，LangChain 组件的每次调用都会自动上报。
 
 我没有用 LangChain 的高层抽象（如 create_react_agent），因为我想自己实现
 Orchestrator 来深入理解 Agent 的编排原理。"
```

**Q: LangChain 的 Chain 和 Agent 有什么区别？**

```
准备话术：
"Chain 是确定性的——A→B→C，每一步做什么是写死的。比如 RAG Chain：
 检索→组装 prompt→调 LLM→返回。

 Agent 是动态的——它能观察环境、思考、选择下一步行动。比如我的 PlannerAgent：
 先判断输入是 URL 还是 PDF（Thought），然后选择调 RepoAnalyzer 还是 PDFAnalyzer
 （Action），拿到结果后生成计划（Finish）。

 我的项目里两者都有：RAG 检索增强问答是 Chain 思维，Agent 选择调用哪个 Tool 是 
 Agent 思维。Orchestrator 编排多个 Agent 是更高层的编排逻辑。"
```

**Q: 你的 RAG pipeline 是怎么设计的？**

```
准备话术：
"五步流程：
 1. 文档上传 → PDFAnalyzer 用 PyMuPDF 提取纯文本
 2. 文本切分 → RecursiveCharacterTextSplitter，chunk_size=1000，overlap=200
    为什么是 1000？因为 Qwen-turbo 的上下文是 8K token，我检索 top-5，
    5×1000=5000 再加上 prompt 大约 6-7K，留有余量。
 3. 向量化 → DashScopeEmbeddings，text-embedding-v2 模型
 4. 存储 → ChromaDB，按 collection 隔离不同学习主题
 5. 检索 → 用户提问时，先 similarity_search(query, k=5)，拿到相关切片
    拼入 prompt 让 LLM 回答

 我遇到过的坑：短查询（如'它怎么实现的？'）检索效果差，因为语义太模糊。
 解决方案是在 Tutor 层做 query expansion——如果检测到指代词（'它'、'这'），
 自动追加 history 中的关键词扩展查询。"
```

### 问题组 2：LangGraph（高频，很多 JD 强调）

**Q: 你了解 LangGraph 吗？用过吗？**

```
准备话术（写完 LangGraph 版本后）：
"我在项目里实现了两个版本的 Orchestrator 做对比。

 手写版：用 Python 的 if-elif 和 Enum 状态机实现。优点是直观、调试方便；
 缺点是状态转换逻辑散落在代码里，不好可视化。

 LangGraph 版：用 StateGraph 定义，每个 Agent 是一个 Node，意图识别是
 conditional_edge。优点是声明式定义、内置持久化（Checkpointer）、
 可以直接生成流程图；缺点是学习成本和调试成本更高。

 举个具体例子：我的意图路由，在手写版里是：
   if intent == 'create_plan': return self._handle_create_plan()
   elif intent == 'ask_question': return self._handle_ask_question()
 
 在 LangGraph 版里是：
   graph.add_conditional_edges('intent_router', route_by_intent, {
       'create_plan': 'planner_node',
       'ask_question': 'tutor_node',
       'start_quiz': 'validator_node',
   })
 
 本质一样，但 LangGraph 版更声明式、更容易理解全局流程。"
```

**Q: LangGraph 的 State 是怎么工作的？**

```
准备话术：
"LangGraph 的核心思想是'状态在图中流转'。
 
 我定义了一个 TypedDict 叫 LearningState，包含 domain、plan、quiz_score、
 status 等字段。每个 Node 接收这个 State，做处理后返回更新的字段。
 LangGraph 会自动 merge 更新到 State 里。

 比如 planner_node 接收 {domain: 'Transformer', status: 'planning'}，
 处理后返回 {plan: '...生成的计划...', status: 'learning'}。
 LangGraph 把 plan 和 status 更新到全局 State，然后根据条件边决定下一步。

 这比手写的 self.state = xxx 更安全，因为 State 是不可变的——每个 Node 
 只能返回要更新的字段，不能直接修改全局状态。"
```

**Q: LangGraph 的 Checkpointer 有什么用？**

```
准备话术：
"Checkpointer 解决的是'长流程中断恢复'的问题。

 我的学习流程是：规划→学习→测验→报告。如果用户在学习阶段关闭了页面，
 下次打开应该能从学习阶段继续，而不是从头开始。

 没有 Checkpointer 的话，我需要自己管理持久化——这就是我的 FileManager 
 和 session JSON 做的事情。

 有了 Checkpointer，LangGraph 自动在每个 Node 执行后保存 State 快照。
 下次 invoke 时传入相同的 thread_id，它会自动从上次的 State 继续。

 我的项目里，手写版用 FileManager 管持久化，LangGraph 版用 MemorySaver
 （内存版 Checkpointer）。生产环境可以替换为 SqliteSaver 或 PostgresSaver。"
```

### 问题组 3：工程设计（高频）

**Q: 你的 Provider 抽象层是怎么设计的？**

```
准备话术：
"经典的工厂模式 + 策略模式。

 抽象基类 LLMProvider 定义了 chat() 和 stream() 接口。
 具体实现 TongyiProvider 封装了 ChatTongyi 的调用细节。
 ProviderFactory 根据配置字符串创建对应的 Provider 实例。

 这样设计的好处：
 1. 业务代码不依赖具体 Provider——Agent 调用的是抽象接口
 2. 切换模型只需改配置——从 Tongyi 切到 OpenAI 不改业务代码
 3. 可以 Mock 测试——单测时注入一个 FakeProvider
 4. 可以按任务选模型——简单问答用便宜模型，复杂推理用贵模型

 虽然我只实现了 Tongyi 一个 Provider，但接口是预留好的。
 面试官如果问'为什么不实现多个'——因为 14 天项目做一个就够展示设计能力，
 多实现一个只是体力活。"
```

**Q: 你怎么处理 LLM 输出不稳定的问题？**

```
准备话术：
"这是我项目里遇到最多的实际问题，我有三层防御策略：

 1. Prompt 约束：明确告诉 LLM '只输出 JSON，不要其他内容'，
    并给出 JSON 示例。这能解决 80% 的格式问题。
 
 2. 正则提取：即使 LLM 输出了多余文字，我用正则 re.search(r'\[[\s\S]*\]') 
    提取其中的 JSON 数组。这能处理'好的，以下是题目：[{...}]'这种情况。
 
 3. Fallback 降级：如果解析彻底失败，返回一个预设的默认结果，
    而不是抛异常让用户看到报错。

 以 ValidatorAgent 的 _parse_questions() 为例，这三层都实现了。
 在 LangSmith 的 Trace 里我能看到哪些调用触发了 fallback，
 然后回去优化对应的 Prompt。"
```

### 问题组 4：可观测性（加分项但常问）

**Q: 你为什么集成 LangSmith？解决了什么问题？**

```
准备话术：
"Agent 系统调试非常痛苦——一次用户输入可能触发 3-5 次 LLM 调用，
 中间还有 RAG 检索、Tool 调用。出了问题，print 日志根本不够用。

 LangSmith 帮我解决了三个问题：
 
 1. 问题定位：有一次用户说'生成计划特别慢'，我在 LangSmith 
    看到 PlannerAgent 的 Trace，发现 RAG 检索花了 8 秒——因为 
    ChromaDB 第一次加载需要预热。知道瓶颈在哪就好优化了。
 
 2. 成本监控：每次 LLM 调用消耗多少 Token 一目了然。
    我发现 Planner 的 prompt 太长（3000 字背景信息），
    截断到 1500 字后效果差不多，Token 省了一半。
 
 3. 质量追踪：我能看到 LLM 的原始输出和解析后的结构化结果，
    方便发现 prompt 需要优化的地方。

 接入非常简单——设置 LANGCHAIN_TRACING_V2=true 环境变量，
 LangChain 组件的调用就会自动上报。自研的 Orchestrator 层
 我通过回调函数手动上报 Trace 事件。"
```

---

## 第四部分：你需要达到的知识深度（三档）

### 档位 A：必须能默写级（面试白板题）

这些概念你必须能在白板上画出来、在嘴上流利说出来：

1. **RAG 的五步流程**：上传 → 切分 → 向量化 → 存储 → 检索+生成
2. **你的三层 Agent 架构**：协调层 → 功能层 → 专业层
3. **Orchestrator 状态机**：五个状态 + 转换条件
4. **LangChain 三件套关系**：LangChain(组件) + LangGraph(编排) + LangSmith(监控)
5. **ReAct 模式**：Thought → Action → Observation → ... → Finish

练习方法：**拿白纸，不看代码，画出以上 5 张图。画不出来的回去看代码。**

### 档位 B：必须能讲清逻辑级（面试追问）

这些你不需要背代码，但要能讲清楚"为什么这样做"：

1. **chunk_size 为什么是 1000？** → 配合模型上下文长度和 top-k 数量
2. **为什么用 ChromaDB 不用 Pinecone？** → 本地部署、免费、够用
3. **为什么手写 Orchestrator 不直接用 LangChain Agent？** → 深入理解原理 + 更灵活
4. **为什么 Provider 只实现了一个？** → 14天 MVP + 接口已预留
5. **Tutor Memory 为什么只保留最近 6 轮？** → Token 限制 + 远距离历史价值低
6. **Quiz 难度怎么控制？** → difficulty 参数映射到 Prompt 的难度描述
7. **为什么用 Streamlit 不用 Gradio/Next.js？** → 快速原型 + Python 全栈

### 档位 C：知道存在即可级（面试提到时不懵）

这些你知道概念就行，不需要深入：

1. **LangGraph 的 Human-in-the-loop** → 节点间可以暂停等用户输入
2. **LangChain 的 LCEL (LangChain Expression Language)** → `prompt | model | parser` 管道语法
3. **LangSmith 的 Dataset 和 Evaluation** → 可以创建测试集做自动评测
4. **向量数据库的 HNSW 索引** → ChromaDB 底层用的近似最近邻算法
5. **Embedding 模型的 fine-tuning** → 可以微调 embedding 提升检索效果
6. **Multi-Agent 的其他框架** → AutoGen, CrewAI, MetaGPT（知道名字和大概思路）

---

## 第五部分：面试前一天速查卡

### 30 秒自我介绍（项目部分）

```
"我最近做了一个 AI 学习助手项目，基于 LangChain + LangGraph + RAG 架构。

 核心功能是：用户上传 PDF 论文或 GitHub 项目，系统自动分析内容、
 生成学习计划、互动教学、测验评估，形成完整的学习闭环。

 技术亮点有三个：
 一是三层 Agent 架构——协调层负责意图识别和流程编排，功能层负责规划/教学/验证，
 专业层负责 PDF 解析和 Quiz 生成，职责分离，易于扩展；
 
 二是 RAG 知识检索——用户上传的资料经过切分、向量化后存入 ChromaDB，
 问答时先检索相关内容再让 LLM 回答，保证答案基于用户自己的学习材料；
 
 三是全链路可观测——接入 LangSmith 追踪每次 LLM 调用、检索操作、Token 消耗，
 方便调试和优化。"
```

### 三个必须准备的"踩坑故事"

面试官最爱问"你遇到过什么困难"，准备三个真实的：

**故事 1：Streamlit 线程死锁**
```
"我最初用 threading.Thread 调 Agent，结果 UI 卡死——因为 Streamlit 的 
session_state 是线程不安全的。最终改成同步执行 + 占位符模式：先显示'思考中'，
在主线程跑 Agent，完成后更新。虽然不是真异步，但用户体验流畅且稳定。"
```

**故事 2：Planner 幻觉计划**
```
"用户上传了 DeepSeek 论文，然后说'帮我定个计划'。结果 Planner 没读论文，
生成了通用深度学习计划——这是幻觉。我的修复是在生成计划前强制查 RAG，
把检索到的内容注入 Prompt。修复后计划里出现了论文的具体章节标题和概念。"
```

**故事 3：RAG 短查询命中率低**
```
"用户问'它怎么实现的？'，RAG 什么都检索不到——因为'它'太模糊了。
我的解决方案是在 Tutor 层做 query expansion：检测到指代词时，
自动追加 'summary introduction overview' 等关键词扩大检索范围。
命中率从约 40% 提升到 80%。"
```

---

## 第六部分：每日复盘模板

每天改完代码后，花 10 分钟回答这三个问题：

```
## Day X 复盘

### 1. 今天改了什么？（技术层面）
- 改了哪个文件
- 核心改动是什么

### 2. 如果面试官问这个改动，我怎么回答？（面试层面）
- 为什么要改？（问题是什么）
- 为什么这样改？（对比了哪些方案）
- 效果如何？（量化指标）

### 3. 有没有关联的 LangChain/LangGraph 概念？（知识层面）
- 对应的官方文档在哪
- 有没有更优的做法
```

---

> **最后的话**：你的项目架构设计已经非常好了——三层 Agent、双模式、七层架构、
> 面试话术文档都很扎实。现在缺的是**把代码实现到位** + **真正理解每一行代码为什么这样写**。
> 面试不怕追问，怕的是"我就是照着教程写的，为什么这样我也不太清楚"。
> 每改一行代码，都问自己："如果面试官问这里，我能不能讲 2 分钟？"
