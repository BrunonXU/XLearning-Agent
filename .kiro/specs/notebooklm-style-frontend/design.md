# 设计文档：NotebookLM 风格前端重设计

## 概述

将 XLearning-Agent 的 Streamlit 前端迁移到 React + TypeScript + Tailwind CSS（前端）+ FastAPI（后端），实现 NotebookLM 风格的三区域布局。核心设计哲学：**以"学习材料"为中心**，AI 的所有回答锚定在用户上传的材料上。

现有 Python AI 核心逻辑（`src/agents/`、`src/specialists/`）保持不变，FastAPI 作为薄适配层将其暴露为 REST API。

---

## 系统架构

```
┌─────────────────────────────────────────────────────────────────┐
│                        浏览器（React SPA）                       │
│  ┌──────────────┐  ┌──────────────────┐  ┌──────────────────┐  │
│  │  Source Panel │  │    Chat Area     │  │  Studio Panel    │  │
│  │  (左 20%)    │  │    (中 50%)      │  │  (右 30%)        │  │
│  └──────┬───────┘  └────────┬─────────┘  └────────┬─────────┘  │
│         │                   │                      │            │
│         └───────────────────┴──────────────────────┘            │
│                         Zustand Store                           │
│                    React Query (HTTP cache)                      │
└─────────────────────────┬───────────────────────────────────────┘
                          │ HTTP / SSE
┌─────────────────────────▼───────────────────────────────────────┐
│                    FastAPI 后端 (Python)                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────────────┐  │
│  │ /api/chat│  │/api/upload│  │/api/search│  │/api/studio/{t}│  │
│  └────┬─────┘  └────┬──────┘  └────┬─────┘  └───────┬────────┘  │
│       │             │              │                 │           │
│  ┌────▼─────────────▼──────────────▼─────────────────▼────────┐ │
│  │              现有 Python 模块（不修改）                      │ │
│  │  TutorAgent  │  RAGEngine  │  ResourceSearcher              │ │
│  │  QualityScorer  │  ProgressTracker  │  Orchestrator         │ │
│  └──────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

---

## 前端项目结构

```
frontend/
├── src/
│   ├── app/
│   │   ├── layout.tsx          # 根布局（三列 ResizablePanels）
│   │   ├── page.tsx            # 首页（学习规划列表）
│   │   └── workspace/
│   │       └── [planId]/
│   │           └── page.tsx    # 工作区页面
│   ├── components/
│   │   ├── source-panel/       # 左侧材料面板
│   │   │   ├── SourcePanel.tsx
│   │   │   ├── MaterialList.tsx
│   │   │   ├── MaterialItem.tsx
│   │   │   ├── SearchPanel.tsx
│   │   │   └── SearchResultItem.tsx
│   │   ├── chat/               # 中间对话区
│   │   │   ├── ChatArea.tsx
│   │   │   ├── MessageList.tsx
│   │   │   ├── MessageBubble.tsx
│   │   │   ├── SourceCitation.tsx
│   │   │   ├── SuggestedQuestions.tsx
│   │   │   └── ChatInput.tsx
│   │   ├── studio/             # 右侧 Studio 面板
│   │   │   ├── StudioPanel.tsx
│   │   │   ├── TodayTasks.tsx
│   │   │   ├── ToolGrid.tsx
│   │   │   ├── ToolCard.tsx
│   │   │   ├── ContentLibrary.tsx
│   │   │   ├── NoteEditor.tsx
│   │   │   └── DevTools.tsx
│   │   ├── home/               # 首页组件
│   │   │   ├── PlanGrid.tsx
│   │   │   ├── PlanCard.tsx
│   │   │   ├── FeaturedPlans.tsx
│   │   │   └── NewPlanModal.tsx
│   │   └── ui/                 # 通用 UI 原子组件
│   │       ├── Button.tsx
│   │       ├── Badge.tsx
│   │       ├── Modal.tsx
│   │       ├── Spinner.tsx
│   │       └── ResizablePanel.tsx
│   ├── store/
│   │   ├── index.ts            # Zustand store 入口
│   │   ├── chatStore.ts
│   │   ├── sourceStore.ts
│   │   ├── studioStore.ts
│   │   └── planStore.ts
│   ├── hooks/
│   │   ├── useSSE.ts           # SSE 流式输出 hook
│   │   ├── useSearch.ts
│   │   └── useKeyboard.ts
│   ├── api/
│   │   └── client.ts           # API 请求封装
│   └── types/
│       └── index.ts            # 全局 TypeScript 类型
├── tailwind.config.ts
└── package.json
```

---

## 组件树与 Props 接口

### 工作区根组件

```typescript
// WorkspacePage.tsx
interface WorkspacePageProps {
  planId: string;
}
// 渲染三列布局：<SourcePanel> | <ChatArea> | <StudioPanel>
```

### 左侧材料面板

```typescript
// SourcePanel.tsx
interface SourcePanelProps {
  planId: string;
}

// MaterialList.tsx
interface MaterialListProps {
  materials: Material[];
  onRemove: (id: string) => void;
  onSelect: (id: string) => void;
  selectedId?: string;
}

// MaterialItem.tsx
interface MaterialItemProps {
  material: Material;
  isSelected: boolean;
  onRemove: () => void;
  onClick: () => void;
}

// SearchPanel.tsx
interface SearchPanelProps {
  onAddToMaterials: (results: SearchResult[]) => void;
}

// SearchResultItem.tsx
interface SearchResultItemProps {
  result: SearchResult;
  checked: boolean;
  onToggle: () => void;
}
```

### 中间对话区

```typescript
// ChatArea.tsx
interface ChatAreaProps {
  planId: string;
}

// MessageBubble.tsx
interface MessageBubbleProps {
  message: ChatMessage;
  isStreaming?: boolean;
}

// SourceCitation.tsx
interface SourceCitationProps {
  sources: CitationSource[];
}

// SuggestedQuestions.tsx
interface SuggestedQuestionsProps {
  questions: string[];
  onSelect: (q: string) => void;
}

// ChatInput.tsx
interface ChatInputProps {
  onSend: (text: string) => void;
  disabled?: boolean;
  placeholder?: string;
}
```

### 右侧 Studio 面板

```typescript
// StudioPanel.tsx
interface StudioPanelProps {
  planId: string;
  devMode?: boolean;
}

// TodayTasks.tsx
interface TodayTasksProps {
  currentDay: DayProgress | null;
  onTaskToggle: (taskIndex: number) => void;
  onCompleteDay: (dayNumber: number) => void;
}

// ToolCard.tsx
interface ToolCardProps {
  tool: StudioTool;
  onClick: () => void;
  isLoading?: boolean;
}

// ContentLibrary.tsx
interface ContentLibraryProps {
  planId: string;
  activeTab: 'ai-generated' | 'my-notes';
  onTabChange: (tab: 'ai-generated' | 'my-notes') => void;
}

// NoteEditor.tsx
interface NoteEditorProps {
  note: Note | null;
  onSave: (content: string, title: string) => void;
  onAiOrganize: () => void;
}
```

---

## 数据模型（TypeScript）

```typescript
// types/index.ts

export type PlatformType = 'bilibili' | 'youtube' | 'google' | 'github' | 'xiaohongshu' | 'other';

export interface Material {
  id: string;
  type: PlatformType;
  name: string;           // 截断至 20 字符显示
  url?: string;
  status: 'parsing' | 'chunking' | 'ready' | 'error';  // parsing=解析中, chunking=分块中
  addedAt: string;        // ISO 8601
}

export interface SearchResult {
  id: string;
  title: string;
  url: string;
  platform: PlatformType;
  description: string;    // 截断至 100 字符显示
  qualityScore: number;   // 0-1，显示时 ×10
  recommendationReason: string;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  sources?: CitationSource[];
  createdAt: string;
}

export interface CitationSource {
  materialId: string;
  materialName: string;
  snippet: string;        // 原始引用片段
}

export interface DayProgress {
  dayNumber: number;
  title: string;
  completed: boolean;
  tasks: DayTask[];
}

export interface DayTask {
  id: string;
  type: 'video' | 'reading' | 'exercise' | 'flashcard';
  title: string;
  qualityScore?: number;  // 视频资源显示评分
  completed: boolean;
}

export interface Note {
  id: string;
  title: string;
  content: string;        // Markdown 格式
  updatedAt: string;
}

export interface GeneratedContent {
  id: string;
  type: 'learning-plan' | 'study-guide' | 'flashcards' | 'quiz' | 'progress-report';
  title: string;
  content: string;        // Markdown 格式
  createdAt: string;
}

export interface LearningPlan {
  id: string;
  title: string;
  sourceCount: number;
  lastAccessedAt: string;
  coverColor: string;     // Tailwind 颜色类
  totalDays: number;
  completedDays: number;
}

export type StudioToolType = 'learning-plan' | 'progress-report' | 'quiz' | 'study-guide' | 'flashcards' | 'notes';

export interface StudioTool {
  type: StudioToolType;
  icon: string;
  label: string;
}
```

---

## 全局状态管理（Zustand）

```typescript
// store/chatStore.ts
interface ChatState {
  messages: ChatMessage[];
  isStreaming: boolean;
  suggestedQuestions: string[];
  // actions
  addMessage: (msg: ChatMessage) => void;
  appendStreamChunk: (chunk: string) => void;
  finalizeStream: (sources: CitationSource[]) => void;
  setSuggestedQuestions: (qs: string[]) => void;
  clearMessages: () => void;
}

// store/sourceStore.ts
interface SourceState {
  materials: Material[];
  searchResults: SearchResult[];
  isSearching: boolean;
  platformSearchStatus: Record<string, 'idle' | 'searching' | 'done' | 'timeout'>;  // 每平台独立进度
  selectedMaterialId: string | null;
  // actions
  addMaterials: (materials: Material[]) => void;
  removeMaterial: (id: string) => void;
  selectMaterial: (id: string | null) => void;
  setSearchResults: (results: SearchResult[]) => void;
  setSearching: (v: boolean) => void;
  setPlatformStatus: (platform: string, status: 'idle' | 'searching' | 'done' | 'timeout') => void;
  updateMaterialStatus: (id: string, status: Material['status']) => void;
}

// store/studioStore.ts
interface StudioState {
  currentDay: DayProgress | null;
  allDays: DayProgress[];
  generatedContents: GeneratedContent[];
  notes: Note[];
  activeLibraryTab: 'ai-generated' | 'my-notes';
  devMode: boolean;
  langGraphEnabled: boolean;
  // actions
  completeDay: (dayNumber: number) => void;
  toggleTask: (dayNumber: number, taskIndex: number) => void;
  addGeneratedContent: (content: GeneratedContent) => void;
  upsertNote: (note: Note) => void;
  deleteNote: (id: string) => void;
  setActiveLibraryTab: (tab: 'ai-generated' | 'my-notes') => void;
  toggleDevMode: () => void;
  toggleLangGraph: () => void;
}

// store/planStore.ts
interface PlanState {
  plans: LearningPlan[];
  currentPlanId: string | null;
  // actions
  setPlans: (plans: LearningPlan[]) => void;
  setCurrentPlan: (id: string) => void;
  upsertPlan: (plan: LearningPlan) => void;
  deletePlan: (id: string) => void;
}
```

**状态持久化策略**：`planStore` 和 `studioStore` 使用 `zustand/middleware` 的 `persist` 中间件持久化到 `localStorage`。`chatStore` 和 `sourceStore` 的状态从后端 API 恢复（刷新时调用 `GET /api/session/{planId}`）。

---

## Tailwind CSS 设计系统

### 颜色系统（对标 NotebookLM）

```typescript
// tailwind.config.ts
theme: {
  extend: {
    colors: {
      // 主背景
      surface: {
        DEFAULT: '#FFFFFF',
        secondary: '#F8F9FA',  // 面板背景
        tertiary: '#F1F3F4',   // 悬停背景
      },
      // 主强调色（深蓝）
      primary: {
        DEFAULT: '#1A73E8',
        hover: '#1557B0',
        light: '#E8F0FE',
      },
      // 辅助强调色（橙色，用于评分/徽章）
      accent: {
        DEFAULT: '#F97316',
        light: '#FFF7ED',
      },
      // 文字
      text: {
        primary: '#202124',
        secondary: '#5F6368',
        disabled: '#9AA0A6',
      },
      // 边框
      border: {
        DEFAULT: '#DADCE0',
        focus: '#1A73E8',
      },
      // 深色模式
      dark: {
        bg: '#1C1C1E',
        surface: '#2C2C2E',
        text: '#F5F5F7',
        border: '#3A3A3C',
      },
    },
  },
}
```

### 间距系统

| Token | 值 | 用途 |
|---|---|---|
| `p-2` | 8px | 紧凑内边距（图标按钮） |
| `p-3` | 12px | 卡片内边距 |
| `p-4` | 16px | 面板内边距 |
| `gap-2` | 8px | 列表项间距 |
| `gap-4` | 16px | 卡片网格间距 |

### 组件样式规范

```css
/* 面板容器 */
.panel {
  @apply bg-surface-secondary border border-border rounded-xl shadow-sm;
}

/* 卡片（工具卡片、材料卡片） */
.card {
  @apply bg-surface border border-border rounded-lg p-3
         hover:bg-surface-tertiary hover:shadow-md
         transition-all duration-150 ease-in-out cursor-pointer;
}

/* 主按钮 */
.btn-primary {
  @apply bg-primary text-white rounded-lg px-4 py-2
         hover:bg-primary-hover active:scale-95
         transition-all duration-150 ease-in-out;
}

/* 次要按钮 */
.btn-secondary {
  @apply bg-surface border border-border text-text-primary rounded-lg px-4 py-2
         hover:bg-surface-tertiary
         transition-all duration-150 ease-in-out;
}

/* 输入框 */
.input {
  @apply bg-surface border border-border rounded-lg px-3 py-2
         focus:outline-none focus:ring-2 focus:ring-primary focus:border-primary
         transition-all duration-150 ease-in-out;
}

/* 评分徽章 */
.score-badge {
  @apply text-accent font-semibold text-sm;
}

/* 消息气泡（AI） */
.message-ai {
  @apply bg-surface-secondary rounded-2xl rounded-tl-sm p-4 max-w-[85%];
}

/* 消息气泡（用户） */
.message-user {
  @apply bg-primary text-white rounded-2xl rounded-tr-sm p-4 max-w-[85%] ml-auto;
}

/* 来源引用标签 */
.citation-tag {
  @apply inline-flex items-center gap-1 bg-primary-light text-primary
         text-xs rounded-full px-2 py-0.5 cursor-pointer
         hover:bg-primary hover:text-white transition-colors duration-150;
}

/* 加载动画（脉冲点） */
.typing-indicator {
  @apply flex gap-1;
}
.typing-dot {
  @apply w-2 h-2 bg-text-secondary rounded-full
         animate-bounce [animation-delay:var(--delay)];
}
```

### 字体规范

```typescript
// tailwind.config.ts
theme: {
  extend: {
    fontFamily: {
      sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
    },
    fontSize: {
      xs:   ['12px', { lineHeight: '16px' }],
      sm:   ['13px', { lineHeight: '20px' }],
      base: ['14px', { lineHeight: '22px' }],  // 正文最小 14px
      md:   ['15px', { lineHeight: '24px' }],
      lg:   ['16px', { lineHeight: '24px' }],
      xl:   ['18px', { lineHeight: '28px' }],
    },
  },
}
```

正文默认使用 `text-base`（14px），面板标题使用 `text-lg`，卡片标签使用 `text-sm`。

### 圆角与过渡规范

- 所有交互元素圆角：`rounded-lg`（8px）
- 卡片圆角：`rounded-xl`（12px）
- 消息气泡圆角：`rounded-2xl`（16px）
- 所有过渡：`transition-all duration-150 ease-in-out`
- 深色模式：通过 `class="dark"` 在 `<html>` 上切换，Tailwind `dark:` 变体



---

## FastAPI 路由设计

### 端点总览

```
POST   /api/chat                    # 流式对话（SSE）
POST   /api/upload                  # 上传 PDF / GitHub 链接
POST   /api/search                  # 资源搜索
GET    /api/studio/{type}           # 生成 Studio 内容
POST   /api/notes                   # 新建笔记
PUT    /api/notes/{id}              # 编辑笔记
DELETE /api/notes/{id}              # 删除笔记
PUT    /api/plan/day/{day_id}/complete  # 标记 Day 完成
GET    /api/session/{plan_id}       # 恢复会话状态
GET    /api/material/{id}/summary   # 获取材料摘要（点击材料时触发）
GET    /api/plans                   # 获取所有学习规划
POST   /api/plans                   # 新建学习规划
PUT    /api/plans/{id}              # 重命名/更新学习规划
DELETE /api/plans/{id}              # 删除学习规划
```

### 关键端点数据模型

```python
# POST /api/chat — 请求体
class ChatRequest(BaseModel):
    plan_id: str
    message: str
    history: List[Dict[str, str]] = []  # 最近 6 轮，由前端维护
    use_rag: bool = True

# SSE 响应格式（text/event-stream）
# data: {"type": "chunk", "content": "..."}
# data: {"type": "sources", "sources": [...]}
# data: {"type": "done"}

# POST /api/upload — multipart/form-data
# fields: plan_id, file (PDF) 或 url (GitHub)
# 响应
class UploadResponse(BaseModel):
    material_id: str
    name: str
    status: str  # "processing" | "ready"

# POST /api/search — 请求体
class SearchRequest(BaseModel):
    plan_id: str
    query: str
    platforms: List[str] = ["bilibili", "youtube", "google", "xiaohongshu"]

# 响应
class SearchResponse(BaseModel):
    results: List[SearchResultDTO]  # 已按 quality_score 降序排列

class SearchResultDTO(BaseModel):
    id: str
    title: str
    url: str
    platform: str
    description: str
    quality_score: float   # 0-1
    recommendation_reason: str

# GET /api/studio/{type}?plan_id=xxx
# type: learning-plan | study-guide | flashcards | quiz | progress-report
class StudioResponse(BaseModel):
    type: str
    content: str           # Markdown 格式
    created_at: str

# PUT /api/plan/day/{day_id}/complete
class CompleteDayRequest(BaseModel):
    plan_id: str

class CompleteDayResponse(BaseModel):
    completed_day: int
    next_day: Optional[int]   # None 表示全部完成
    progress_percentage: float
```

### 与现有 Python 模块的集成

```python
# backend/main.py（FastAPI 应用入口）
# 每个 plan_id 对应一个独立的 session，懒加载 Agent 实例

_sessions: Dict[str, SessionContext] = {}

@dataclass
class SessionContext:
    tutor: TutorAgent
    rag_engine: Optional[RAGEngine]
    progress_tracker: ProgressTracker
    orchestrator: Orchestrator  # 或 LangGraphOrchestrator

def get_session(plan_id: str) -> SessionContext:
    if plan_id not in _sessions:
        _sessions[plan_id] = SessionContext(
            tutor=TutorAgent(...),
            rag_engine=None,
            progress_tracker=ProgressTracker(plan_id),
            orchestrator=Orchestrator(...),
        )
        _sessions[plan_id].progress_tracker.load()
    return _sessions[plan_id]
```

---

## 关键数据流

### 1. 搜索流程

```
用户输入关键词 + 选择平台
    │
    ▼
SearchPanel → POST /api/search
    │
    ▼
FastAPI → ResourceSearcher.search(query, platforms)
    │         ↓ 并行搜索各平台
    │     QualityScorer.score_batch(results)
    │         ↓ LLM 评分 + 归一化
    │     按 quality_score 降序排列
    │
    ▼
SearchResponse → sourceStore.setSearchResults()
    │
    ▼
SearchResultItem 渲染（⭐ x.x/10 + 推荐理由 + 勾选框）
```

### 2. 对话流程（SSE）

```
用户发送消息
    │
    ▼
ChatInput → chatStore.addMessage(userMsg)
    │
    ▼
useSSE hook → POST /api/chat（SSE）
    │
    ▼
FastAPI → TutorAgent.stream_response(message, history, use_rag=True)
    │         ↓ RAGEngine.build_context(query)
    │         ↓ LLM.stream(messages)
    │         ↓ yield chunks
    │
    ▼
SSE chunks → chatStore.appendStreamChunk(chunk)
    │         → MessageBubble 实时渲染
    │
    ▼
SSE done event → chatStore.finalizeStream(sources)
    │             → SourceCitation 渲染来源引用
    │
    ▼
后端异步生成推荐问题 → suggestedQuestions 更新
```

### 3. 学习计划推进流程

```
用户点击"完成 Day N"
    │
    ▼
TodayTasks → PUT /api/plan/day/{dayId}/complete
    │
    ▼
FastAPI → ProgressTracker.mark_day_completed(day_number)
    │         ↓ 持久化到 data/sessions/{plan_id}.json
    │
    ▼
CompleteDayResponse { next_day: N+1, progress_percentage }
    │
    ▼
studioStore.completeDay(N)
    │  ├─ 更新 allDays[N].completed = true
    │  └─ 更新 currentDay = allDays[N+1]（若存在）
    │
    ▼
TodayTasks 重新渲染（显示 Day N+1 的任务）
进度报告自动刷新（React Query invalidate）
```

---

## 正确性属性

*A property is a characteristic or behavior that should hold true across all valid executions of a system — essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1：搜索结果降序排列

*For any* 搜索结果列表，经过后端处理后返回给前端的结果，相邻两项的 `quality_score` 应满足 `results[i].quality_score >= results[i+1].quality_score`（降序）。

**Validates: Requirements 4.5**

### Property 2：今日任务指向第一个未完成 Day

*For any* 进度状态（包含若干已完成和未完成的 Day），`currentDay` 应始终等于 `allDays` 中第一个 `completed == false` 的 Day；若所有 Day 均已完成，则 `currentDay` 为 `null`。

**Validates: Requirements 6.2, 6.9**

### Property 3：完成 Day 后进度单调递增

*For any* 进度状态，调用 `completeDay(N)` 后，`completedDays` 的数量应严格大于调用前的数量，且不会减少。

**Validates: Requirements 6.3, 6.9**

### Property 4：会话状态往返一致

*For any* 工作区会话状态（对话历史、已添加材料、已生成 Studio 内容），将其持久化后重新加载，应得到与原始状态等价的状态。

**Validates: Requirements 1.5**

### Property 5：材料类型图标映射完备

*For any* 合法的 `PlatformType` 值，渲染 `MaterialItem` 组件时，输出的 HTML 应包含对应的平台图标（📄/🔗/📺/🎬/📕/🌐）。

**Validates: Requirements 3.4**

### Property 6：搜索结果评分显示格式正确

*For any* `SearchResult`，渲染 `SearchResultItem` 时，输出中应包含格式为 `⭐ x.x/10` 的评分字符串，其中数值等于 `qualityScore × 10`，保留一位小数。

**Validates: Requirements 4.3**

### Property 7：SSE 流式输出产生多个 chunk

*For any* 非空的 Tutor 回复，`/api/chat` 的 SSE 响应应产生至少 2 个 `type: "chunk"` 事件，最终以 `type: "done"` 事件结束。

**Validates: Requirements 1.4, 5.4**

### Property 8：对话历史窗口不超过 6 轮

*For any* 超过 6 轮的对话历史，前端传给 `/api/chat` 的 `history` 字段长度应不超过 12 条消息（6 轮 × 2）。

**Validates: Requirements 5.3**

---

## 键盘快捷键与无障碍

### useKeyboard hook

```typescript
// hooks/useKeyboard.ts
// 全局键盘事件监听，在 WorkspacePage 挂载
useKeyboard({
  'ctrl+k': () => chatInputRef.current?.focus(),   // 聚焦输入框
  'meta+k': () => chatInputRef.current?.focus(),
  'ctrl+n': () => openNewPlanModal(),               // 新建规划
  'meta+n': () => openNewPlanModal(),
  'Escape': () => closeAllModals(),                 // 关闭弹出层
});
```

### aria-label 规范

所有图标按钮必须提供 `aria-label`，示例：

```tsx
<button aria-label="移除材料" onClick={onRemove}>✕</button>
<button aria-label="搜索资源" onClick={onSearch}>🔍</button>
<button aria-label="新建笔记" onClick={onNewNote}>+</button>
<button aria-label="导出为 Markdown" onClick={onExport}>⬇</button>
```

### 键盘导航

`MaterialList` 使用 `role="listbox"` + `aria-activedescendant`，支持：
- `↑/↓` 箭头键切换材料
- `Enter` 选中当前材料
- `Delete` 触发移除确认对话框

所有交互元素使用 `focus-visible:ring-2 focus-visible:ring-primary` 显示焦点指示器。

---

## 材料点击联动设计

当用户点击左侧材料列表中的某个材料时：

```
MaterialItem.onClick
    │
    ▼
sourceStore.selectMaterial(materialId)
    │
    ▼
ChatArea 监听 selectedMaterialId 变化
    │  WHEN selectedMaterialId 变化且不为 null
    ▼
调用 GET /api/material/{id}/summary
    │
    ▼
在 MessageList 顶部插入一条系统消息（role: 'system'）
显示该材料的摘要信息（标题、类型、简短描述）
MaterialItem 高亮显示（border-primary + bg-primary-light）
```

| 场景 | 前端处理 | 后端处理 |
|---|---|---|
| PDF 解析失败 | 材料状态显示 `error`，提示重试 | 返回 `422` + 错误详情 |
| 搜索超时（>15s） | 显示已完成平台的结果，超时平台显示"搜索超时" | 各平台独立超时，部分结果可用时返回 `206` |
| SSE 连接中断 | `useSSE` hook 自动重连（最多 3 次），失败后降级为普通 HTTP | — |
| LLM 调用失败 | 显示"AI 暂时不可用，请稍后重试" | 返回 `503`，日志记录 |
| 笔记保存冲突 | 乐观更新 + 失败时回滚，提示"保存失败" | 返回 `409` |
| Day 已完成重复标记 | 幂等处理，不报错 | `mark_day_completed` 幂等，重复调用返回 `200` |

---

## 测试策略

### 单元测试

- `SearchResultItem` 渲染测试：验证评分格式、图标映射
- `TodayTasks` 渲染测试：验证空状态、任务列表、完成状态
- `studioStore.completeDay` 逻辑测试：验证状态转换
- FastAPI 端点测试：验证请求/响应格式、HTTP 状态码
- `ProgressTracker.mark_day_completed` 幂等性测试

### 属性测试（Property-Based Testing）

使用 **fast-check**（前端 TypeScript）和 **Hypothesis**（后端 Python）。每个属性测试最少运行 **100 次**迭代。

```typescript
// 前端属性测试示例（fast-check）
// Feature: notebooklm-style-frontend, Property 1: 搜索结果降序排列
test('搜索结果始终按 quality_score 降序排列', () => {
  fc.assert(fc.property(
    fc.array(fc.record({
      id: fc.string(),
      qualityScore: fc.float({ min: 0, max: 1 }),
      // ...其他字段
    }), { minLength: 1 }),
    (results) => {
      const sorted = sortByQualityScore(results);
      for (let i = 0; i < sorted.length - 1; i++) {
        expect(sorted[i].qualityScore).toBeGreaterThanOrEqual(sorted[i+1].qualityScore);
      }
    }
  ), { numRuns: 100 });
});

// Feature: notebooklm-style-frontend, Property 2: 今日任务指向第一个未完成 Day
test('currentDay 始终是第一个未完成的 Day', () => {
  fc.assert(fc.property(
    fc.array(fc.record({
      dayNumber: fc.integer({ min: 1, max: 30 }),
      completed: fc.boolean(),
      title: fc.string(),
      tasks: fc.constant([]),
    }), { minLength: 0, maxLength: 30 }),
    (days) => {
      const store = createStudioStore(days);
      const firstUncompleted = days.find(d => !d.completed) ?? null;
      expect(store.currentDay?.dayNumber).toBe(firstUncompleted?.dayNumber ?? undefined);
    }
  ), { numRuns: 100 });
});
```

```python
# 后端属性测试示例（Hypothesis）
# Feature: notebooklm-style-frontend, Property 3: 完成 Day 后进度单调递增
@given(
    days=st.lists(
        st.builds(DayProgress, day_number=st.integers(min_value=1, max_value=30),
                  title=st.text(min_size=1), completed=st.booleans()),
        min_size=1, max_size=30
    )
)
@settings(max_examples=100)
def test_complete_day_monotonic(days, tmp_path):
    tracker = ProgressTracker("test-session")
    tracker._days = days
    before = sum(1 for d in tracker._days if d.completed)
    uncompleted = [d for d in days if not d.completed]
    if uncompleted:
        tracker.mark_day_completed(uncompleted[0].day_number)
        after = sum(1 for d in tracker._days if d.completed)
        assert after > before

# Feature: notebooklm-style-frontend, Property 4: 会话状态往返一致
@given(
    days=st.lists(
        st.builds(DayProgress, day_number=st.integers(min_value=1, max_value=10),
                  title=st.text(min_size=1), completed=st.booleans()),
        min_size=0, max_size=10
    )
)
@settings(max_examples=100)
def test_progress_round_trip(days, tmp_path):
    tracker = ProgressTracker("rt-session")
    tracker._days = days
    tracker.save()
    tracker2 = ProgressTracker("rt-session")
    tracker2.load()
    assert [d.model_dump() for d in tracker2.days] == [d.model_dump() for d in days]
```

**属性测试标签格式**：每个属性测试必须在注释中标注：
`Feature: notebooklm-style-frontend, Property {N}: {property_text}`


---

## 视觉验收标准（对标 NotebookLM）

> 实现阶段第一个任务必须是纯静态 UI shell，无后端逻辑，只有布局和样式。完成后对照本节逐条验收，全部通过后才能接入后端。

---

### 整体布局

| 项目 | 要求 |
|---|---|
| 三列分割线 | 1px solid `#DADCE0`，不是阴影，不是 gap |
| 左侧面板背景 | `#F8F9FA`（比中间略深） |
| 中间对话区背景 | `#FFFFFF`（纯白） |
| 右侧 Studio 面板背景 | `#F8F9FA`（与左侧一致） |
| 顶部导航栏高度 | 56px，背景 `#FFFFFF`，底部 1px `#DADCE0` |
| 顶部导航栏内容 | 左侧 Logo + 产品名，右侧设置图标 + 用户头像，垂直居中 |
| 三列总高度 | `calc(100vh - 56px)`，不出现页面级滚动条 |
| 各面板内部 | 独立滚动，不影响其他面板 |

---

### 顶部导航栏

```
┌─────────────────────────────────────────────────────────────────┐  56px
│  ⚛ XLearning Agent          [规划名称（可编辑）]    ⚙  👤      │
└─────────────────────────────────────────────────────────────────┘
```

| 项目 | 要求 |
|---|---|
| Logo 区域 | 图标 20px + 产品名 `text-lg font-semibold text-text-primary`，左侧 padding 16px |
| 规划名称 | 居中显示，`text-base text-text-secondary`，点击可内联编辑，编辑时显示下划线 |
| 右侧图标 | 24px 图标，`text-text-secondary`，hover 时背景 `#F1F3F4` 圆形 32px |
| 整体 | `bg-white border-b border-border`，`z-10` 保证在面板之上 |

---

### 左侧材料面板

```
┌─────────────────────────┐
│  📚 学习材料        [+] │  ← 面板标题行，高度 48px
├─────────────────────────┤
│  ┌─────────┐ ┌────────┐ │  ← 两个 Tab 按钮
│  │ 上传文件 │ │搜索资源│ │
│  └─────────┘ └────────┘ │
├─────────────────────────┤
│  ── 已添加材料 ────────  │  ← section 标题，text-xs text-text-secondary
│  📄 transformer...  ✅  │  ← 材料行，高度 40px
│  🔗 langchain...    ✅  │
├─────────────────────────┤
│  ── 搜索结果 ──────────  │
│  ☑ [B站] 标题...        │  ← 搜索结果行
│     ⭐ 8.7/10            │
│     💡 推荐理由...       │
└─────────────────────────┘
```

| 项目 | 要求 |
|---|---|
| 面板内边距 | `px-4 py-3` |
| 面板标题 | `text-sm font-semibold text-text-primary`，高度 48px，垂直居中 |
| Tab 按钮（上传/搜索） | 等宽两列，高度 36px，`rounded-lg`，激活态 `bg-primary-light text-primary font-medium`，非激活 `text-text-secondary hover:bg-surface-tertiary` |
| Section 标题 | `text-xs font-medium text-text-secondary uppercase tracking-wide`，`mt-4 mb-2` |
| 材料行 | 高度 40px，`rounded-lg`，hover `bg-surface-tertiary`，选中 `bg-primary-light border-l-2 border-primary` |
| 材料图标 | 16px，左侧 `mr-2` |
| 材料名称 | `text-sm text-text-primary`，超出截断显示省略号 |
| 就绪状态 | 绿色圆点 8px `bg-green-500`，右侧对齐 |
| 处理中状态 | 灰色脉冲动画圆点 |
| 移除按钮 | hover 材料行时才显示，`✕` 16px，`text-text-disabled hover:text-red-500` |
| 搜索结果行 | `rounded-lg border border-border p-3 mb-2`，勾选后 `border-primary bg-primary-light` |
| 评分显示 | `text-accent font-semibold text-sm`，⭐ emoji + 数字 |
| 推荐理由 | `text-xs text-text-secondary`，最多显示 2 行，超出省略 |
| 加入材料按钮 | 固定在搜索结果列表底部，`btn-primary w-full`，显示已选数量 |

---

### 中间对话区

```
┌─────────────────────────────────────────┐
│  ── 建议问题 ──────────────────────────  │  ← 顶部，可折叠
│  [问题1] [问题2] [问题3]                │
├─────────────────────────────────────────┤
│                                         │
│  [用户消息气泡]              右对齐 →   │
│                                         │
│  ← [AI 消息气泡]                        │
│    📎 来源引用标签                       │
│                                         │
│  [流式输出时的脉冲点]                   │
│                                         │
├─────────────────────────────────────────┤
│  [无材料时的提示横幅]                   │
│  ┌─────────────────────────────────┐    │  ← 输入框，固定底部
│  │ 向 AI 提问...              [发送]│    │
│  └─────────────────────────────────┘    │
└─────────────────────────────────────────┘
```

| 项目 | 要求 |
|---|---|
| 消息列表区域 | `flex-1 overflow-y-auto px-6 py-4`，消息间距 `gap-6` |
| 用户消息气泡 | `bg-primary text-white rounded-2xl rounded-tr-sm px-4 py-3 max-w-[75%] ml-auto` |
| AI 消息气泡 | `bg-surface-secondary rounded-2xl rounded-tl-sm px-4 py-3 max-w-[85%]`，无边框 |
| AI 消息文字 | `text-base text-text-primary`，Markdown 渲染，代码块有语法高亮 |
| 来源引用标签 | `inline-flex items-center gap-1 bg-primary-light text-primary text-xs rounded-full px-2 py-0.5 mt-2 cursor-pointer hover:bg-primary hover:text-white` |
| 流式输出光标 | 末尾闪烁的 `|` 光标，`animate-pulse` |
| 脉冲点（等待中） | 3个点，`w-2 h-2 bg-text-secondary rounded-full animate-bounce`，延迟 0/150/300ms |
| 建议问题区域 | `flex flex-wrap gap-2 px-6 py-3 border-b border-border`，每个问题 `rounded-full border border-border text-sm px-3 py-1 hover:bg-surface-tertiary cursor-pointer` |
| 输入框容器 | `border-t border-border px-4 py-3 bg-white` |
| 输入框 | `w-full rounded-xl border border-border px-4 py-3 text-base resize-none focus:ring-2 focus:ring-primary`，最小高度 44px，最大高度 200px 自动扩展 |
| 发送按钮 | 输入框右下角内嵌，`bg-primary text-white rounded-lg px-3 py-1.5 text-sm`，无内容时 `opacity-50 cursor-not-allowed` |
| 无材料提示横幅 | `bg-accent-light border border-accent text-accent text-sm rounded-lg px-4 py-2 mx-4 mb-2` |

---

### 右侧 Studio 面板

```
┌─────────────────────────┐
│  ✨ Studio               │  ← 面板标题，48px
├─────────────────────────┤
│  🎯 今日任务             │  ← 区域标题
│  ☑ 看: 视频 ⭐9.2       │  ← 任务行，40px
│  ☐ 读: 章节             │
│  [完成 Day 1 →]         │  ← 完成按钮
├─────────────────────────┤
│  ── 学习工具 ──────────  │
│  ┌────────┐ ┌────────┐  │  ← 2列网格，卡片高度 72px
│  │📅 计划 │ │📊 进度 │  │
│  └────────┘ └────────┘  │
│  ┌────────┐ ┌────────┐  │
│  │🧪 测验 │ │📖 指南 │  │
│  └────────┘ └────────┘  │
│  ┌────────┐ ┌────────┐  │
│  │🃏 闪卡 │ │📝 笔记 │  │
│  └────────┘ └────────┘  │
├─────────────────────────┤
│  [AI生成] [我的笔记]     │  ← Tab
│  📅 学习计划  03-03 [↓] │  ← 内容列表行，36px
├─────────────────────────┤
│  🔗 LangSmith ✅         │  ← 底部状态栏，32px
└─────────────────────────┘
```

| 项目 | 要求 |
|---|---|
| 今日任务区域 | `bg-white rounded-xl border border-border mx-3 mt-3 p-3`，与面板背景形成层次 |
| 今日任务标题 | `text-sm font-semibold text-text-primary flex items-center gap-1` |
| 任务行 | 高度 36px，`flex items-center gap-2`，勾选框 16px |
| 勾选框（已完成） | `text-primary`，勾选动画 150ms |
| 完成 Day 按钮 | `text-xs text-primary hover:underline`，右对齐，仅当天所有任务完成后高亮 |
| 工具卡片网格 | `grid grid-cols-2 gap-2 px-3 py-2` |
| 工具卡片 | 高度 72px，`bg-white rounded-xl border border-border flex flex-col items-center justify-center gap-1 hover:shadow-md hover:border-primary cursor-pointer transition-all duration-150` |
| 工具卡片图标 | 24px emoji |
| 工具卡片文字 | `text-xs font-medium text-text-primary` |
| 工具卡片加载中 | 图标替换为 `Spinner`，文字变为"生成中..." |
| 内容库 Tab | `flex border-b border-border mx-3`，激活 `border-b-2 border-primary text-primary font-medium`，非激活 `text-text-secondary` |
| 内容列表行 | 高度 36px，`flex items-center justify-between px-3 text-sm hover:bg-surface-tertiary rounded-lg` |
| 导出按钮 | `text-xs text-text-secondary hover:text-primary`，仅 hover 时显示 |
| 底部状态栏 | 高度 32px，`border-t border-border px-3 flex items-center text-xs text-text-secondary` |
| LangSmith 已连接 | 绿色圆点 6px + "LangSmith ✅" |
| LangSmith 未连接 | 红色圆点 6px + "LangSmith ❌" |

---

### 首页（学习规划列表）

| 项目 | 要求 |
|---|---|
| 页面背景 | `#FFFFFF` |
| 顶部筛选栏 | 高度 48px，`border-b border-border`，Tab 样式与 NotebookLM 一致：文字 Tab，激活态下划线 `border-b-2 border-primary` |
| 精选规划区域 | 横向滚动，`overflow-x-auto`，隐藏滚动条，卡片宽度 200px，高度 160px |
| 精选卡片 | 上半部分为纯色色块（6种预设颜色随机分配），下半部分白色，显示标题和来源数 |
| 最近规划网格 | `grid grid-cols-4 gap-4 px-6`，卡片宽度自适应 |
| 规划卡片 | 高度 180px，`rounded-xl border border-border hover:shadow-lg transition-shadow duration-150`，hover 时显示三点菜单 ⋮ |
| 卡片封面色块 | 高度 100px，6种颜色：`#E8F0FE`(蓝) `#FFF7ED`(橙) `#F0FDF4`(绿) `#FDF4FF`(紫) `#FFF1F2`(红) `#F0F9FF`(青) |
| 卡片信息区 | `px-3 py-2`，标题 `text-sm font-medium`，来源数和时间 `text-xs text-text-secondary` |
| 新建按钮 | 右上角，`bg-primary text-white rounded-lg px-4 py-2 text-sm font-medium`，`+ 新建` |
| 新建弹窗 | 宽度 480px，`rounded-2xl shadow-2xl`，三种创建方式卡片等宽排列，选中态 `border-primary bg-primary-light` |
| 空状态 | 居中显示，大图标 + 引导文字 + 三种创建方式按钮 |

---

### 交互细节（必须实现）

| 交互 | 要求 |
|---|---|
| 所有 hover 过渡 | `transition-all duration-150 ease-in-out`，不能有卡顿感 |
| 按钮点击反馈 | `active:scale-95`，有轻微缩放感 |
| 弹窗出现 | `animate-in fade-in zoom-in-95 duration-150` |
| 弹窗消失 | `animate-out fade-out zoom-out-95 duration-100` |
| 面板滚动 | 自定义滚动条：宽度 4px，颜色 `#DADCE0`，hover `#9AA0A6`，`rounded-full` |
| 加载骨架屏 | 内容加载时显示 `animate-pulse bg-surface-tertiary rounded` 占位块，不显示空白 |
| 确认对话框 | 移除材料时，小型弹窗（宽度 320px），`rounded-xl shadow-lg`，取消/确认两个按钮 |
| 深色模式切换 | 切换时所有颜色平滑过渡 `transition-colors duration-200` |
| 焦点指示器 | `focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2`，仅键盘导航时显示 |

---

### 静态 UI Shell 验收清单

实现完静态 shell 后，逐项打勾：

- [ ] 三列布局比例正确（20/50/30），分割线为 1px 细线
- [ ] 左侧面板背景比中间略深，视觉层次清晰
- [ ] 顶部导航栏高度 56px，底部有分割线
- [ ] 材料列表行 hover 有背景色变化，选中有左侧蓝色边框
- [ ] 搜索结果卡片有边框，勾选后变蓝
- [ ] 用户消息气泡蓝色右对齐，AI 消息气泡灰色左对齐
- [ ] 来源引用标签为圆角胶囊形，hover 变蓝
- [ ] 输入框圆角，focus 时有蓝色 ring
- [ ] Studio 工具卡片 2 列网格，hover 有阴影
- [ ] 今日任务区域有白色卡片背景，与面板背景形成层次
- [ ] 内容库 Tab 切换，激活态有下划线
- [ ] 底部 LangSmith 状态栏始终可见
- [ ] 首页规划卡片有彩色封面色块
- [ ] 新建弹窗圆角大，有阴影
- [ ] 所有 hover/active 过渡流畅，无卡顿
- [ ] 深色模式下所有颜色正确切换
- [ ] 自定义滚动条细且圆润
