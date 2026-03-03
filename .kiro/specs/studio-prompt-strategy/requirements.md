# 需求文档：Studio Prompt 策略与动态学习路径

## 简介

当前 Studio 面板的 5 个工具（学习计划、学习指南、闪卡、测验、进度报告）使用静态 prompt 生成内容，缺乏上下文注入（学习进度、材料摘要、对话历史、用户目标等），导致生成质量差且无法随学习进度动态调整。本需求旨在为每个工具设计针对性的 prompt 策略，将前端的学习规划数据传递给后端，构建富上下文 prompt，并支持用户在学习过程中动态重新生成内容。

## 术语表

- **Studio_Panel**: 前端右侧面板，包含 5 个 AI 内容生成工具卡片和内容列表
- **Studio_Backend**: 后端 `/api/studio/{type}` 端点，负责接收请求、构建 prompt、调用 LLM 生成内容
- **TutorAgent**: 核心 LLM 调用代理，支持 RAG 检索和对话历史注入
- **Prompt_Builder**: 后端为每个工具类型构建富上下文 prompt 的模块（新增）
- **Learning_Context**: 前端传递给后端的学习上下文数据，包含 allDays（学习规划）、进度状态、用户目标等
- **RAG_Engine**: 检索增强生成引擎，从已上传材料中检索相关内容片段
- **Content_Version**: 同一工具类型生成的多个版本内容，旧版本保留，新版本追加到列表顶部
- **Progress_Report_Interface**: 进度报告模块的预留接口，本期不实现具体逻辑

## 需求

### 需求 1：前端传递学习上下文给后端

**用户故事：** 作为学习者，我希望 Studio 工具生成的内容能反映我当前的学习状态，以便获得个性化的学习内容。

#### 验收标准

1. WHEN 用户点击任意 Studio 工具卡片，THE Studio_Panel SHALL 将当前 Learning_Context（包含 allDays 数组、每天的完成状态、任务列表）作为 POST 请求体发送给 Studio_Backend
2. WHEN 用户点击 Studio 工具卡片且 studioStore 中存在 activePlanId，THE Studio_Panel SHALL 在请求体中包含 activePlanId 字段
3. THE Studio_Backend SHALL 将 HTTP 方法从 GET 改为 POST，接收 JSON 请求体中的 Learning_Context 数据
4. IF 前端发送的请求体为空或缺少 allDays 字段，THEN THE Studio_Backend SHALL 使用空数组作为默认值并继续生成内容

### 需求 2：后端 Prompt Builder 构建富上下文 Prompt

**用户故事：** 作为学习者，我希望 AI 生成的内容基于我的学习材料和进度，以便内容与我的学习状态高度相关。

#### 验收标准

1. THE Prompt_Builder SHALL 为每个工具类型（learning-plan、study-guide、flashcards、quiz、progress-report）维护独立的 prompt 模板
2. WHEN Studio_Backend 收到生成请求，THE Prompt_Builder SHALL 从 RAG_Engine 检索与当前学习主题相关的材料摘要片段，并注入到 prompt 中
3. WHEN Learning_Context 中包含 allDays 数据，THE Prompt_Builder SHALL 将学习规划结构（天数、主题、任务）和完成进度注入到 prompt 中
4. WHEN 会话中存在对话历史，THE Prompt_Builder SHALL 将最近的对话历史（最多最近 3 轮）注入到 prompt 中，提供对话上下文
5. THE Prompt_Builder SHALL 在 prompt 中包含明确的输出格式指令，确保每个工具类型的输出结构一致

### 需求 3：学习计划工具的上下文感知 Prompt

**用户故事：** 作为学习者，我希望生成的学习计划能基于我已上传的材料和当前进度来规划，以便计划切实可行。

#### 验收标准

1. WHEN 用户点击学习计划工具，THE Prompt_Builder SHALL 在 prompt 中注入已上传材料的标题和摘要信息
2. WHEN Learning_Context 中已有 allDays 数据（非首次生成），THE Prompt_Builder SHALL 在 prompt 中注入当前规划的完成进度，并指示 LLM 基于剩余未完成内容重新规划
3. THE Prompt_Builder SHALL 在学习计划 prompt 中指示 LLM 输出包含 dayNumber、title、tasks 数组的结构化 JSON，以便前端解析为 DayProgress 对象
4. IF RAG_Engine 未检索到任何材料内容，THEN THE Prompt_Builder SHALL 在 prompt 中提示 LLM 生成通用学习计划并建议用户上传材料

### 需求 4：学习指南工具的上下文感知 Prompt

**用户故事：** 作为学习者，我希望学习指南能聚焦于我当前阶段需要掌握的知识点，以便高效学习。

#### 验收标准

1. WHEN 用户点击学习指南工具，THE Prompt_Builder SHALL 在 prompt 中注入 RAG 检索到的材料核心内容片段
2. WHEN Learning_Context 中包含当前学习天数（currentDay），THE Prompt_Builder SHALL 在 prompt 中指示 LLM 重点覆盖当前天数对应主题的知识点
3. WHEN Learning_Context 中存在已完成的天数，THE Prompt_Builder SHALL 在 prompt 中提示 LLM 对已完成内容做简要回顾，对未完成内容做详细展开

### 需求 5：闪卡工具的上下文感知 Prompt

**用户故事：** 作为学习者，我希望闪卡能针对我当前学习阶段的重点知识生成，以便有效复习。

#### 验收标准

1. WHEN 用户点击闪卡工具，THE Prompt_Builder SHALL 在 prompt 中注入 RAG 检索到的材料内容，并指示 LLM 基于材料生成问答对
2. WHEN Learning_Context 中包含当前学习天数，THE Prompt_Builder SHALL 在 prompt 中指示 LLM 优先为当前天数和最近已完成天数的主题生成闪卡
3. THE Prompt_Builder SHALL 在闪卡 prompt 中指示 LLM 按照固定格式输出（Q/A 对，用分隔符分隔），确保前端可解析

### 需求 6：测验工具的上下文感知 Prompt

**用户故事：** 作为学习者，我希望测验能覆盖我已学习的内容，以便检验学习效果。

#### 验收标准

1. WHEN 用户点击测验工具，THE Prompt_Builder SHALL 在 prompt 中注入 RAG 检索到的材料内容
2. WHEN Learning_Context 中存在已完成的天数，THE Prompt_Builder SHALL 在 prompt 中指示 LLM 基于已完成天数的主题出题，覆盖已学知识点
3. WHEN Learning_Context 中所有天数均未完成，THE Prompt_Builder SHALL 在 prompt 中指示 LLM 基于材料整体内容生成基础测验
4. THE Prompt_Builder SHALL 在测验 prompt 中指示 LLM 输出包含题目、选项、正确答案和解析的结构化格式

### 需求 7：进度报告接口预留

**用户故事：** 作为开发者，我希望进度报告模块有清晰的接口定义，以便后续实现具体逻辑。

#### 验收标准

1. THE Studio_Backend SHALL 为 progress-report 类型定义与其他工具一致的 POST 端点接口
2. THE Prompt_Builder SHALL 为 progress-report 类型定义 prompt 模板占位符，包含进度数据注入点
3. WHEN 用户点击进度报告工具，THE Studio_Backend SHALL 返回基于 Learning_Context 中完成进度的基础统计文本（已完成天数/总天数、完成百分比）
4. THE Progress_Report_Interface SHALL 在代码中以注释或文档形式标注后续需要实现的功能点（掌握程度评估、薄弱环节分析、学习曲线图表数据）

### 需求 8：动态重新生成与版本保留

**用户故事：** 作为学习者，我希望在学习进度变化后能重新生成内容，同时保留旧版本以便对比。

#### 验收标准

1. WHEN 用户再次点击已生成过内容的工具卡片，THE Studio_Panel SHALL 发起新的生成请求，生成新版本内容
2. WHEN 新版本内容生成成功，THE Studio_Panel SHALL 将新内容追加到 generatedContents 列表顶部，保留所有旧版本
3. THE Studio_Panel SHALL 在内容列表中为同一工具类型的多个版本显示生成时间，以便用户区分版本

### 需求 9：聊天触发 Studio 内容重新生成

**用户故事：** 作为学习者，我希望在聊天中通过自然语言触发 Studio 工具重新生成，以便在对话流程中无缝更新学习内容。

#### 验收标准

1. WHEN 用户在聊天输入中包含触发关键词（如"更新学习计划""重新生成闪卡""刷新测验"等），THE Studio_Backend SHALL 识别意图并触发对应工具的内容重新生成
2. WHEN 聊天触发重新生成成功，THE Studio_Panel SHALL 将新生成的内容追加到 generatedContents 列表中，与手动点击工具卡片的行为一致
3. THE Studio_Backend SHALL 定义一组明确的触发关键词映射表，将关键词映射到对应的工具类型
