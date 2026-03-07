// 全局 TypeScript 类型定义

export type PlatformType = 'bilibili' | 'youtube' | 'google' | 'github' | 'xiaohongshu' | 'other';

export interface Material {
  id: string;
  type: PlatformType;
  name: string;           // 截断至 20 字符显示
  url?: string;
  status: 'parsing' | 'chunking' | 'ready' | 'error';
  addedAt: string;        // ISO 8601
  viewedAt?: string;      // 首次查看时间，未查看则为 undefined
}

export interface SearchResult {
  id: string;
  title: string;
  url: string;
  platform: PlatformType;
  description: string;    // 截断至 100 字符显示
  qualityScore: number;   // 0-1，显示时 ×10
  recommendationReason: string;
  contentSummary?: string;              // AI 内容摘要
  commentSummary?: string;              // 评论结论摘要
  engagementMetrics?: Record<string, any>;  // 互动指标
  imageUrls?: string[];                 // 图片 URL 列表
  topComments?: string[];               // 高赞评论文本列表
  contentText?: string;                  // 正文原文
  // 结构化知识提取
  keyPoints?: string[];                 // 核心观点（3-5 条）
  keyFacts?: string[];                  // 关键数据/事实
  methodology?: string[];               // 方法论/步骤
  credibility?: {                       // 可信度子维度评估
    timeliness?: number;                // 时效性 0-10
    authority?: number;                 // 权威性 0-10
    accuracy?: number;                  // 准确性 0-10
    objectivity?: number;               // 客观性 0-10
    timeliness_note?: string;
    authority_note?: string;
    accuracy_note?: string;
    objectivity_note?: string;
  };
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  sources?: CitationSource[];
  createdAt: string;
}

export interface CitationSource {
  materialId: string;
  materialName: string;
  snippet: string;
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
  qualityScore?: number;
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
  type: 'learning-plan' | 'study-guide' | 'flashcards' | 'quiz' | 'progress-report' | 'mind-map' | 'day-summary';
  title: string;
  content: string;        // Markdown 格式
  createdAt: string;
  version?: number;                    // 当前版本号（从 1 开始）
  versions?: GeneratedContentVersion[]; // 历史版本（最新在前）
}

export interface GeneratedContentVersion {
  content: string;
  createdAt: string;
  version: number;
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

export type StudioToolType = 'learning-plan' | 'progress-report' | 'quiz' | 'study-guide' | 'flashcards' | 'notes' | 'mind-map' | 'day-summary';

export interface StudioTool {
  type: StudioToolType;
  icon: string;
  label: string;
}

export type LibraryTab = 'ai-generated' | 'my-notes';

export type PlatformSearchStatus = 'idle' | 'searching' | 'done' | 'timeout';

export interface SearchHistoryEntry {
  id: string;
  query: string;
  platforms: PlatformType[];
  results: SearchResult[];
  resultCount: number;
  searchedAt: string;     // ISO 8601
  status?: 'searching' | 'done' | 'error';
}

export type SearchStage = 'idle' | 'searching' | 'filtering' | 'extracting' | 'evaluating' | 'done' | 'error';

export interface LearnerProfile {
  goal: string;
  duration: string;
  level: string;
  background: string;
  dailyHours: string;
}
