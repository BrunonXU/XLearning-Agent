# Day 4：赋予 Agent "脑子"与"记忆"

> 📅 **计划**：Day 4 - UI 对接与 Orchestrator 增强
> 📦 **产出**：不仅能"动"，还能"思考"的完整应用
> ⏱️ **阅读时间**：30-40 分钟

---

## 写在前面：从"脚本"到"智能体"

前三天的代码更像是一个 **"高级脚本"**：你问一句，它答一句，没有记忆，不懂上下文，经常"一本正经地胡说八道"。

Day 4 我们做了两件大事，让它变成了真正的 **Agent**：
1.  **装上脑子（Orchestrator 增强）**：它现在能记住你之前说的话（Memory），做计划前会先查资料（RAG-Enhanced Planning），还能自己决定下一步该干嘛（Dynamic Routing）。
2.  **打通经脉（UI/Backend 对接）**：解决了 Streamlit 线程死锁的"千古难题"，用最稳妥的同步模式实现了"思考中..."的流畅体验。

> ⚠️ **用户提示**：本篇重点在 **Agent 逻辑**，前端 UI 部分通过简单配置实现，不作深究。

---

## 第一章：Orchestrator 的"脑子" (The Brain)

### 1.1 让 Agent 拥有记忆 (Context Awareness)

之前的 `tutor.run(question)` 是无状态的。用户问："它怎么实现的？"，Agent 会懵："它可以是谁？"。

**解决方案**：在 Orchestrator 层面注入 `history`。

```python
# src/ui/logic.py (UI 层)
# 提取最近 10 条对话记录
history = []
if st.session_state.current_session:
    all_msgs = st.session_state.current_session.get("messages", [])
    # 排除最后一条正在生成的占位符
    raw_history = all_msgs[:-2] if len(all_msgs) >= 2 else []
    for m in raw_history[-10:]:
        history.append({"role": m["role"], "content": m["content"]})

# 调用 Orchestrator
response = orchestrator.run(user_input, history=history)
```

**接收端**：

```python
# src/agents/orchestrator.py
def run(self, user_input, history=None):
    # 将 history 传给 TutorAgent
    return self.tutor.run(user_input, history=history)
```

这样，当用户问"它"时，LLM 能通过 history 知道"它"指的是上一轮聊到的 "Transformer"。

### 1.2 拒绝幻觉：RAG-Enhanced Planning

**问题**：用户上传了 PDF《DeepSeek 论文》，然后说"帮我定个计划"。Planner 没读 PDF，直接生成了一个通用的深度学习计划 —— **这是幻觉**。

**修复逻辑**：在生成计划前，**强制**先查 RAG。

```python
# src/agents/orchestrator.py -> _handle_create_plan
def _handle_create_plan(self, user_input: str) -> str:
    # 0. 尝试从 RAG 获取上下文
    rag_context = ""
    if self.rag_engine:
        if len(user_input) < 20: 
            # 如果用户只说"生成计划"，则获取全库摘要
            rag_context = self.rag_engine.build_context("summary overview", k=5)
        else:
            # 如果从具体需求出发，检索相关片段
            rag_context = self.rag_engine.build_context(user_input, k=5)
            
    # 1. 将 RAG 内容注入 Prompt
    planner_input = user_input
    if rag_context:
        planner_input = f"用户目标: {user_input}\n\n参考资料内容:\n{rag_context}"

    # 2. 生成计划
    plan = self.planner.run(planner_input)
    return plan
```

**效果**：现在生成的计划会明确包含 PDF 里的章节标题和核心概念，而不是泛泛而谈。

### 1.3 动态路由 (Dynamic Routing)

Orchestrator 不再是一根筋执行。它维护了一个**状态机**。

```python
class OrchestratorState(str, Enum):
    IDLE = "idle"              # 空闲
    PLANNING = "planning"      # 规划中
    LEARNING = "learning"      # 学习中
    VALIDATING = "validating"  # 验证中
```

**调度逻辑 (`_run_coordinated`)**：
1.  **IDLE 态**：用户进来不管问啥，先引导去 `PLANNING`（除非只是简单闲聊）。
2.  **PLANNING 态**：计划生成完，自动切到 `LEARNING`，并把计划存入 RAG。
3.  **LEARNING 态**：用户如果问"考考我"，自动切到 `VALIDATING` 调用 Quiz Agent。

---

## 第二章：工程化落地的"坑"与"解"

### 2.1 Streamlit 的线程死锁陷阱

**现象**：前几天尝试用 `threading.Thread` 去跑 Agent，结果点击"发送"后，UI 直接卡死，或者报错 `SessionContext missing`。

**原因**：Streamlit 的 `st.session_state` 是**线程不安全**的。子线程无法正确更新主线程 UI 的状态，导致死锁。

**最终方案：同步执行 + 状态占位符**

我们回归了最稳妥的**同步模式 (Synchronous)**，但通过一个小技巧实现了"假异步"体验：

1.  **用户点击发送**：UI 立刻插入一条 User Message。
2.  **插入占位符**：UI 插入一条 Assistant Message，内容是 `正在思考中...`，状态设为 `streaming`。
3.  **强制刷新**：`st.experimental_rerun()`。
4.  **后台计算**：在下一次渲染时，检测到有 `pending` 消息，在**主线程**调用 Agent。
5.  **更新结果**：Agent 跑完，更新那条占位符的内容，再次刷新。

```python
# src/ui/logic.py
def handle_chat_input(user_input):
    # 1. 占位
    add_message(role="assistant", content="正在思考中...", status="streaming")
    # 2. 标记需要处理
    st.session_state.pending_chat_query = user_input
    # 3. 刷新
    st.experimental_rerun()

# 页面入口
def main():
    # 渲染 UI...
    
    # 最后检查是否有待处理的任务
    if st.session_state.pending_chat_query:
        process_pending_chat() # 主线程执行，安全！
```

### 2.2 面试考点：状态管理

> **面试官：在 Web Agent 中，你是怎么处理长耗时任务的？**
>
> **回答**："在 Streamlit 这种响应式框架里，由于 session_state 的线程限制，我采用了**同步执行+占位符**的模式。
> 用户操作触发 UI更新（显示'思考中'）-> 触发 Rerun -> 在主线程执行 Agent 逻辑 -> 更新 State -> 再次 Rerun 显示结果。
> 这避免了多线程带来的 Context 丢失问题，同时也保证了用户界面有即时反馈，不会觉得卡死。"

---

## 第三章：UI/UX 的一点点优化 (Brief)

虽然重点是 Agent，但好用的 Agent 离不开好用的界面。

### 3.1 吸顶标题 (Sticky Header)
在长对话中，用户忘了当前在哪个阶段（Plan? Quiz?）。我们用 CSS 把进度条固定在顶部：

```python
# src/ui/styles.py
st.markdown("""
<style>
    div[data-testid="stVerticalBlock"] > div:has(div.step-container) {
        position: sticky;
        top: 0;
        z-index: 999;
        background: white;
    }
</style>
""", unsafe_allow_html=True)
```

### 3.2 可调节侧边栏
Orchestrator 的日志（Trace）和知识库状态放在侧边栏。为了不挤占聊天空间，我们加了一个 `st.slider` 控制侧边栏宽度，让用户自己决定是看重**过程**（宽侧边栏）还是看重**结果**（宽聊天框）。

---

## 总结：Day 4 产出

1.  **智能体 (Brain)**：
    *   ✅ **有记忆**：Orchestrator 注入 History。
    *   ✅ **不瞎编**：Plan 前先查 RAG。
    *   ✅ **懂变通**：基于状态机的动态路由。
2.  **稳定性 (Stability)**：
    *   ✅ **主线程同步模型**：彻底解决 Streamlit 假死问题。

**👉 下一步**：现在脑子和身体都有了，接下来的 Day 5-6 我们要打磨**工具层**，让 Validator 出题更准，并支持更复杂的 PDF 图表分析。
