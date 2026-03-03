import React, { useState, useRef, useEffect } from 'react'

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
  const [settingsOpen, setSettingsOpen] = useState(false)
  const [avatarOpen, setAvatarOpen] = useState(false)
  const settingsRef = useRef<HTMLDivElement>(null)
  const avatarRef = useRef<HTMLDivElement>(null)

  // 同步外部 planTitle 变化
  useEffect(() => { setDraft(planTitle) }, [planTitle])

  // 点击外部关闭下拉
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (settingsRef.current && !settingsRef.current.contains(e.target as Node)) setSettingsOpen(false)
      if (avatarRef.current && !avatarRef.current.contains(e.target as Node)) setAvatarOpen(false)
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [])

  const commitEdit = () => {
    setEditing(false)
    if (draft.trim() && draft.trim() !== planTitle && onTitleChange) {
      onTitleChange(draft.trim())
    }
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
              onKeyDown={(e) => { if (e.key === 'Enter') commitEdit(); if (e.key === 'Escape') { setDraft(planTitle); setEditing(false) } }}
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

        {/* 设置按钮 + 下拉 */}
        <div ref={settingsRef} className="relative">
          <button
            onClick={() => { setSettingsOpen(!settingsOpen); setAvatarOpen(false) }}
            aria-label="设置"
            className="w-8 h-8 flex items-center justify-center rounded-full text-text-secondary dark:text-dark-text hover:bg-surface-tertiary dark:hover:bg-dark-surface transition-colors duration-150"
          >
            ⚙️
          </button>
          {settingsOpen && (
            <div className="absolute right-0 top-10 z-50 bg-white dark:bg-dark-surface border border-gray-200 dark:border-dark-border rounded-xl shadow-lg py-2 min-w-[180px]">
              <div className="px-4 py-2 text-xs text-gray-400 font-medium">设置</div>
              <button onClick={() => { onToggleDark?.(); setSettingsOpen(false) }}
                className="w-full text-left px-4 py-2.5 text-sm text-gray-700 dark:text-dark-text hover:bg-gray-50 dark:hover:bg-dark-bg flex items-center gap-2">
                {isDark ? '☀️ 浅色模式' : '🌙 深色模式'}
              </button>
              <div className="border-t border-gray-100 dark:border-dark-border my-1" />
              <div className="px-4 py-2 text-xs text-gray-400">版本 0.1.0</div>
            </div>
          )}
        </div>

        {/* 头像按钮 + 下拉 */}
        <div ref={avatarRef} className="relative">
          <button
            onClick={() => { setAvatarOpen(!avatarOpen); setSettingsOpen(false) }}
            aria-label="用户头像"
            className="w-8 h-8 flex items-center justify-center rounded-full bg-primary text-white text-sm font-medium ml-1"
          >
            U
          </button>
          {avatarOpen && (
            <div className="absolute right-0 top-10 z-50 bg-white dark:bg-dark-surface border border-gray-200 dark:border-dark-border rounded-xl shadow-lg py-2 min-w-[180px]">
              <div className="px-4 py-2 text-xs text-gray-400 font-medium">用户</div>
              <div className="px-4 py-2.5 text-sm text-gray-700 dark:text-dark-text flex items-center gap-2">
                👤 本地用户
              </div>
              <div className="border-t border-gray-100 dark:border-dark-border my-1" />
              <div className="px-4 py-2 text-xs text-gray-400">登录功能即将推出</div>
            </div>
          )}
        </div>
      </div>
    </header>
  )
}
