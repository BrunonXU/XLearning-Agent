// 全局 TypeScript 类型定义

export type PlatformType = 'bilibili' | 'youtube' | 'google' | 'github' | 'xiaohongshu' | 'other';

export interface Material {
  id: string;
  type: PlatformType;
  name: string;           // 截断至 20 字符显示
  url?: string;
  status: 'parsing' | 'chunking' | 'ready' | 'error';
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

export type LibraryTab = 'ai-generated' | 'my-notes';

export type PlatformSearchStatus = 'idle' | 'searching' | 'done' | 'timeout';
