import React, { useState } from 'react'
import type { GeneratedContent, Note, LibraryTab } from '../../types'

// 静态 mock 数据（Task 8 接入后端后替换）
const MOCK_CONTENTS: GeneratedContent[] = [
  { id: 'c1', type: 'learning-plan', title: '学习计划', content: '', createdAt: '2026-03-03T00:00:00Z' },
  { id: 'c2', type: 'study-guide', title: '学习指南', content: '', createdAt: '2026-03-01T00:00:00Z' },
  { id: 'c3', type: 'flashcards', title: '闪卡', content: '', createdAt: '2026-03-01T00:00:00Z' },
]

const MOCK_NOTES: Note[] = [
  { id: 'n1', title: '我的学习笔记', content: '# 笔记\n...', updatedAt: '2026-03-03T00:00:00Z' },
]

const TYPE_ICONS: Record<GeneratedContent['type'], string> = {
  'learning-plan': '📅',
  'study-guide': '📖',
  'flashcards': '🃏',
  'quiz': '🧪',
  'progress-report': '📊',
}

interface ContentLibraryProps {
  planId: string
  activeTab: LibraryTab
  onTabChange: (tab: LibraryTab) => void
}

export const ContentLibrary: React.FC<ContentLibraryProps> = ({
  activeTab: initialTab,
}) => {
  const [activeTab, setActiveTab] = useState<LibraryTab>(initialTab)
  const [hoveredId, setHoveredId] = useState<string | null>(null)

  const formatDate = (iso: string) =>
    new Date(iso).toLocaleDateString('zh-CN', { month: '2-digit', day: '2-digit' })

  return (
    <div className="flex flex-col h-full">
      {/* Tab 切换 */}
      <div className="flex border-b border-border dark:border-dark-border mx-3">
        {(['ai-generated', 'my-notes'] as LibraryTab[]).map(tab => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`flex-1 py-2 text-sm transition-all duration-150 ${
              activeTab === tab
                ? 'border-b-2 border-primary text-primary font-medium'
                : 'text-text-secondary hover:text-text-primary'
            }`}
          >
            {tab === 'ai-generated' ? 'AI 生成' : '我的笔记'}
          </button>
        ))}
      </div>

      {/* 内容列表 */}
      <div className="flex-1 overflow-y-auto scrollbar-thin px-3 py-2">
        {activeTab === 'ai-generated' ? (
          <ul className="flex flex-col gap-0.5">
            {MOCK_CONTENTS.map(c => (
              <li
                key={c.id}
                className="flex items-center justify-between h-9 px-2 rounded-lg hover:bg-surface-tertiary dark:hover:bg-dark-surface transition-colors duration-150 cursor-pointer"
                onMouseEnter={() => setHoveredId(c.id)}
                onMouseLeave={() => setHoveredId(null)}
              >
                <span className="flex items-center gap-1.5 text-sm text-text-primary dark:text-dark-text truncate">
                  <span aria-hidden="true">{TYPE_ICONS[c.type]}</span>
                  {c.title}
                </span>
                <span className="flex items-center gap-2 flex-shrink-0">
                  <span className="text-xs text-text-secondary">{formatDate(c.createdAt)}</span>
                  {hoveredId === c.id && (
                    <button
                      aria-label="导出为 Markdown"
                      className="text-xs text-text-secondary hover:text-primary transition-colors duration-150"
                    >
                      ↓
                    </button>
                  )}
                </span>
              </li>
            ))}
          </ul>
        ) : (
          <div className="flex flex-col h-full">
            <ul className="flex flex-col gap-0.5 flex-1">
              {MOCK_NOTES.map(n => (
                <li
                  key={n.id}
                  className="flex items-center justify-between h-9 px-2 rounded-lg hover:bg-surface-tertiary dark:hover:bg-dark-surface transition-colors duration-150 cursor-pointer"
                >
                  <span className="text-sm text-text-primary dark:text-dark-text truncate">
                    📝 {n.title}
                  </span>
                  <span className="flex items-center gap-2 flex-shrink-0">
                    <span className="text-xs text-text-secondary">{formatDate(n.updatedAt)}</span>
                    <button
                      aria-label="编辑笔记"
                      className="text-xs text-text-secondary hover:text-primary transition-colors duration-150"
                    >
                      编辑
                    </button>
                  </span>
                </li>
              ))}
            </ul>
            <button
              className="mt-2 w-full h-9 rounded-lg border border-dashed border-border text-sm text-text-secondary hover:border-primary hover:text-primary transition-all duration-150"
              aria-label="新建笔记"
            >
              + 新建笔记
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
