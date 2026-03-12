# Studio Prompt V2 — 审查建议与改进方向

> 基于 README、技术文档、现有 prompt_builder 实现和 spec 的全面审查。
> 标注优先级：🔴 V2 必须解决 / 🟡 V2 建议做 / 🟢 P2+ 后续优化

---

## 1. 🔴 goal 字段策略：保持自由文本，放弃 Python 层分类

### 问题

spec 里多处 AC 写的是硬分支逻辑：
- flashcards AC 6：「求职者侧重面试常考概念，兴趣学习者侧重探索性」
- quiz AC 7：「求职者侧重实战应用题，兴趣学习者侧重理解和探索性题目」
- mind-map AC 4：「求职者侧重实用技能展开，兴趣学习者侧重探索性分支展开」

但 `LearnerProfileModal.tsx` 中 goal 是自由文本 textarea，placeholder 是"准备考研、转行学编程、提升工作技能..."。Python 层没法可靠地对自由文本做 `if goal_type == "求职"` 分支。

### 决策

**保持自由文本，不改为结构化选项。**

理由：
- goal 的组合太多（考研+跨专业、做毕设、工作中深入、副业学习…），预设选项无法穷举
- 自由文本 UX 更好，不限制用户表达，符合 10k star 项目的灵活度
- Python 层分类是伪需求——真正需要的条件是"有没有 goal"，不是"goal 是什么类型"
- LLM 本身擅长理解自由文本意图，让它自适应比硬编码分类更健壮

### 需要改的 AC

所有涉及"求职者侧重…兴趣学习者侧重…"的 AC 统一改为：

> WHEN Learner_Profile 存在且包含 goal 字段，THE Dynamic_Instruction SHALL 将 goal 原文注入指令，并指示 LLM 根据学习目的自适应调整内容侧重方向。

prompt 实现示例：
```python
if goal:
    parts.append(
        f"{n}. **学习目的为导向**：学习者的目的是「{goal}」，"
        "请根据这个目的调整内容的侧重方向、深度和实用性。"
    )
```

涉及的 AC 清单：
- 需求 2（flashcards）AC 6
- 需求 3（quiz）AC 7
- 需求 4（mind-map）AC 4
- 需求 5（day-summary）AC 6
- design.md 中 3.2/3.3/3.4/3.5 的 profile.goal 行

---

## 2. 🔴 7 个工具的衔接关系——spec 缺失的维度

### 问题

spec 里每个工具是独立的需求，没有显式定义工具之间的时序关系和职责边界。用户旅程（README 里的小明 14 天学 React）暗示了清晰的衔接，但 prompt 层没有体现。

### 工具时序关系图

```
Day 0（创建阶段）:
  learning-plan → 生成 N 天计划（战术：每日任务分解）
  study-guide   → 宏观路线图（战略：知识体系 + 里程碑）

Day 1-N（每日学习）:
  聊天答疑 → day-summary（当天回顾 + 鼓励 + 明日预告）
  flashcards（当天 + 最近几天的记忆卡片，高频低粒度）

阶段性回顾（中期/完成时）:
  quiz（阶段性测验，覆盖已完成天数，低频高粒度）
  progress-report（数据驱动分析，识别薄弱点）
  mind-map（知识结构可视化，全局视角）
```

### 需要在 prompt 中体现的边界

#### a) learning-plan vs study-guide（最容易混淆）

两者都在说"学什么、按什么顺序学"，输出有大量重叠风险。

**建议**：在 learning-plan 的动态指令中加硬约束：
```
你的职责是生成可执行的每日任务清单，不要写宏观路线图或知识体系概述（那是学习指南的职责）。
每天的 tasks 必须是具体的、可勾选的行动项，而不是抽象的学习方向。
```

#### b) flashcards vs quiz（定位互补但 spec 里太像）

当前 spec 中两者的 Three_Way_Branch 逻辑几乎一样（都是"把困惑点纳入"），缺乏区分。

**建议**：明确互补定位：
| 维度 | flashcards | quiz |
|------|-----------|------|
| 使用频率 | 每天 | 阶段性（中期/完成时） |
| 粒度 | 小（单概念问答） | 大（场景分析、多步推理） |
| 侧重 | 记忆和回忆（定义、术语、概念辨析） | 理解和应用（代码题、场景题、综合分析） |
| 覆盖范围 | 当前天 + 最近几天 | 所有已完成天数 |
| 困惑点利用 | 生成更多相关概念卡片 | 针对困惑点出综合题 |

#### c) day-summary 和 progress-report 的衔接

day-summary 是单天的，progress-report 是全局的。当前 progress-report 没有利用已有的 day-summary 历史。

**标记为 🟢 P3**：未来可以让 progress-report 参考 generated_contents 表中已有的 day-summary 记录，但 V2 不做。

---

## 3. 🔴 6 个工具的 role_instruction 需要重写

### 问题

study-guide 的 role_instruction 有完整的人设、职责边界、工具区分：

> "你是一位资深学习策略顾问。你的职责是分析学习者的背景、目标…你的输出是战略层面的指导——回答「学什么、按什么顺序学、怎么判断学会了」，而不是每日任务分解（那是学习计划的职责）。"

其他 6 个太弱了，比如 flashcards：

> "你是一个闪卡生成器。基于学习材料和用户提过的问题，生成适合快速记忆/回忆的问答对。"

没有人设深度、没有职责边界、没有和相邻工具的区分。

### 建议：每个 role_instruction 包含三要素

1. **人设**（你是谁，什么领域的专家）
2. **职责边界**（你负责什么，明确不负责什么）
3. **工具区分**（和相邻工具的输出如何互补，避免重叠）

### 重写方案

#### learning-plan（课程设计师）
```
你是一位课程设计师，擅长将学习目标拆解为可执行的每日任务序列。
你的职责是战术层面的任务分解——回答「每天具体做什么、做多少、怎么验证做完了」。
你不负责宏观知识体系梳理（那是学习指南的职责），也不负责知识点测验（那是测验的职责）。
你生成的每一天都必须是可执行的：有明确的任务列表、验证标准和预计时长。
```

#### flashcards（记忆训练师）
```
你是一位记忆训练师，擅长将知识点转化为高效的问答卡片，帮助学习者通过主动回忆巩固记忆。
你的职责是生成适合间隔重复的短问答对——每张卡片聚焦一个概念，问题精准，答案简洁。
你不负责综合测验（那是测验的职责），也不负责知识结构梳理（那是思维导图的职责）。
卡片应覆盖定义、概念辨析、关键术语、易混淆点，粒度要小，适合快速翻阅。
```

#### quiz（考试出题专家）
```
你是一位考试出题专家，擅长设计能检验真实理解程度的测验题目。
你的职责是生成阶段性综合测验——题目应覆盖已学知识点，侧重理解和应用而非死记硬背。
你不负责日常记忆训练（那是闪卡的职责），也不负责学习进度分析（那是进度报告的职责）。
题目应包含多种题型，难度梯度合理，每道题附带详细解析帮助学习者理解错误原因。
```

#### mind-map（知识结构化专家）
```
你是一位知识结构化专家，擅长将零散的知识点组织为层次清晰的树状结构。
你的职责是生成适合可视化的知识结构图——用 Markdown 标题层级表达概念的从属和关联关系。
你不负责学习路线规划（那是学习指南的职责），也不负责知识点测验（那是测验的职责）。
输出必须适配 markmap.js 渲染，层级不宜过深（建议 3-4 层），每个节点简洁有力。
```

#### day-summary（学习教练）
```
你是一位学习教练，擅长在每天学习结束后给予个性化的回顾、鼓励和前瞻性建议。
你的职责是总结当天学习成果、分析与之前知识的关联、给出真诚的鼓励和明日预告。
你不负责全局进度分析（那是进度报告的职责），也不负责知识点测验（那是测验的职责）。
你的语气应该像一个了解学习者的教练——肯定努力、指出亮点、温和提醒薄弱点。
```

#### progress-report（学习数据分析师）
```
你是一位学习数据分析师，擅长从进度数据中提取洞察并给出可执行的改进建议。
你的职责是基于 allDays 完成状态做纯数据分析——完成率、薄弱环节识别、学习节奏评估。
你不负责内容生成或知识讲解，只负责数据驱动的分析和建议。
分析必须基于实际数据，不要编造未发生的学习行为或虚构进度。
```

---

## 4. 🟡 prompt section 顺序优化

### 问题

当前 `_assemble` 的 section 顺序：
```
画像 → 记忆摘要 → RAG → 进度 → 对话历史 → 生成指令 → 输出格式
```

根据 LLM 的 recency bias（技术文档中也提到了材料放在 prompt 末尾的策略），最后面的内容权重最高。当前生成指令在倒数第二位，输出格式在最后——但输出格式是格式约束，不应该占据最高权重位置。

### 建议

调整为：
```
画像 → 记忆摘要 → RAG → 进度 → 对话历史 → 输出格式 → 生成指令
```

让生成指令（最重要的"你该怎么做"）占据 recency bias 的最高权重位置。

**更激进的方案（V3 考虑）**：把生成指令合并到 system_prompt（和 role_instruction 一起），user_prompt 只放数据。这样 system_prompt = "你是谁 + 你该怎么做 + 输出格式"，user_prompt = "这是你的输入数据"。但这个改动影响面大，V2 不做。

---

## 5. 🟢 RAG 查询策略对 quiz 可能不够好

### 问题

`_build_rag_query` 中 quiz 的查询是所有已完成天标题拼在一起：
```python
completed = [d.get("title", "") for d in all_days if d.get("completed") and d.get("title")]
return " ".join(completed) if completed else "测验 知识点"
```

当已完成天数多时（比如 10 天），query 变成一个很长的字符串，embedding 检索效果会很差——太散了，没有焦点。

### 建议（P2 优化）

quiz 改为多次 RAG 检索：每个已完成天单独检索 top-2，然后合并去重。比一个大 query 检索 top-5 效果好得多。

```python
# 伪代码
if content_type == "quiz":
    all_chunks = []
    for day in completed_days:
        chunks = rag_engine.build_context(day["title"], k=2)
        all_chunks.extend(chunks)
    rag_context = deduplicate_and_join(all_chunks)
```

---

## 6. 🟢 Three_Way_Branch prompt 文本可以更具体

### 问题

当前 study-guide 的对话线索原则写的是：
> "从最近对话和对话记忆摘要中提取用户提过的问题、困惑点、感兴趣的方向"

这对 LLM 来说偏抽象——它需要自己去 chat_history 和 episodic_summary 里找线索。

### 建议（P2 优化）

在 Python 层做简单的关键词提取，把具体线索列出来注入 prompt：
```python
# 从 episodic_summary 中提取前 200 字作为线索摘要
if episodic_summary:
    hint = episodic_summary[:200]
    parts.append(f"用户历史学习线索：{hint}")
```

V2 先不做，但 `_build_conversation_thread_principle` 辅助方法的接口设计应预留这个扩展点。

---

## 7. 🟢 day-summary 可参考历史 day-summary

### 问题

progress-report 做全局分析时，没有利用 generated_contents 表中已有的 day-summary 记录。如果用户已经生成过 Day 1-7 的 day-summary，progress-report 应该能参考这些历史总结来做更精准的分析。

### 建议（P3）

在 `_build_progress_report_instruction` 中，从 DB 查询该 plan 下所有 type="day-summary" 的 generated_contents，提取关键信息注入 prompt。

---

## 变更影响总结

| 优先级 | 改动项 | 影响文件 |
|--------|--------|---------|
| 🔴 | goal AC 统一改为自由文本注入 | requirements.md, design.md, tasks.md |
| 🔴 | 6 个 role_instruction 重写 | design.md, tasks.md（新增 task） |
| 🔴 | 工具衔接关系 + 职责边界写入 design.md | design.md |
| 🟡 | prompt section 顺序调整 | design.md（第 1 节 _assemble 设计） |
| 🟢 | quiz RAG 多次检索 | 记入 TODO.md |
| 🟢 | Three_Way_Branch 具体化 | 记入 TODO.md |
| 🟢 | progress-report 参考历史 day-summary | 记入 TODO.md |
