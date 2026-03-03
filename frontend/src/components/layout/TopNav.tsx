import React, { useState } from 'react'

interface TopNavProps {
  planTitle?: string
  onTitleChange?: (title: string) => void
  onToggleDark?: () => void
  isDark?: boolean
}

export const TopNav: React.FC<TopNavProps> = ({
  planTitle = '',
  onTitleChange,
  onToggleDark,
  isDark = false,
}) => {
  const [editing, setEditing] = useState(false)
  const [draft, setDraft] = useState(planTitle)

  const commitEdit = () => {
    setEditing(false)
    if (draft.trim() && onTitleChange) onTitleChange(draft.trim())
  }

  return (
    <header className="h-14 bg-white dark:bg-dark-bg border-b border-border dark:border-dark-border flex items-center px-4 z-10 flex-shrink-0">
      {/* 左侧 Logo */}
      <div className="flex items-center gap-2 min-w-0 flex-shrink-0">
        <span className="text-xl" aria-hidden="true">⚛</span>
        <span className="text-lg font-semibold text-text-primary dark:text-dark-text whitespace-nowrap">
          XLearning
        </span>
      </div>

      {/* 中间规划名称（可编辑） */}
      <div className="flex-1 flex justify-center px-4">
        {planTitle && (
          editing ? (
            <input
              autoFocus
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
              onBlur={commitEdit}
              onKeyDown={(e) => { if (e.key === 'Enter') commitEdit(); if (e.key === 'Escape') setEditing(false) }}
              className="text-base text-text-secondary dark:text-dark-text bg-transparent border-b border-primary outline-none text-center w-64"
              aria-label="编辑规划名称"
            />
          ) : (
            <button
              onClick={() => { setDraft(planTitle); setEditing(true) }}
              className="text-base text-text-secondary dark:text-dark-text hover:underline truncate max-w-xs"
              aria-label="点击编辑规划名称"
            >
              {planTitle}
            </button>
          )
        )}
      </div>

      {/* 右侧图标 */}
      <div className="flex items-center gap-1 flex-shrink-0">
        <button
          onClick={onToggleDark}
          aria-label={isDark ? '切换浅色模式' : '切换深色模式'}
          className="w-8 h-8 flex items-center justify-center rounded-full text-text-secondary dark:text-dark-text hover:bg-surface-tertiary dark:hover:bg-dark-surface transition-colors duration-150"
        >
          {isDark ? '☀️' : '🌙'}
        </button>
        <button
          aria-label="设置"
          className="w-8 h-8 flex items-center justify-center rounded-full text-text-secondary dark:text-dark-text hover:bg-surface-tertiary dark:hover:bg-dark-surface transition-colors duration-150"
        >
          ⚙️
        </button>
        <button
          aria-label="用户头像"
          className="w-8 h-8 flex items-center justify-center rounded-full bg-primary text-white text-sm font-medium ml-1"
        >
          U
        </button>
      </div>
    </header>
  )
}
