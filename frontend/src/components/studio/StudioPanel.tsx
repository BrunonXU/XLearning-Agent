import React, { useState, useEffect, useRef } from 'react'
import { ContentViewer } from './ContentViewer'
import { NoteEditor } from './NoteEditor'
import { useStudioStore } from '../../store/studioStore'
import { useSourceStore } from '../../store/sourceStore'
import type { GeneratedContent, Note } from '../../types'

/** NotebookLM 风格工具定义 */
const TOOLS = [
  { type: 'study-guide', icon: '📖', label: '学习指南', color: 'bg-blue-50 border-blue-200', iconBg: 'text-blue-600' },
  { type: 'flashcards', icon: '🃏', label: '闪卡', color: 'bg-purple-50 border-purple-200', iconBg: 'text-purple-600' },
  { type: 'quiz', icon: '🧪', label: '测验', color: 'bg-green-50 border-green-200', iconBg: 'text-green-600' },
  { type: 'learning-plan', icon: '📅', label: '学习计划', color: 'bg-orange-50 border-orange-200', iconBg: 'text-orange-600' },
  { type: 'progress-report', icon: '📊', label: '进度报告', color: 'bg-pink-50 border-pink-200', iconBg: 'text-pink-600' },
] as const

const TYPE_ICONS: Record<string, string> = {
  'learning-plan': '📅', 'study-guide': '📖', 'flashcards': '🃏',
  'quiz': '🧪', 'progress-report': '📊',
}

interface StudioPanelProps { planId?: string }

export const StudioPanel: React.FC<StudioPanelProps> = ({ planId = '' }) => {
  const {
    generatedContents, notes, addGeneratedContent, addNote, updateNote, deleteNote,
    devMode, setDevMode, langGraphEnabled, setLangGraphEnabled,
  } = useStudioStore()
  const { materials } = useSourceStore()
  const [loadingTool, setLoadingTool] = useState<string | null>(null)
  const [viewingContent, setViewingContent] = useState<GeneratedContent | null>(null)
  const [editingNote, setEditingNote] = useState<Note | null>(null)
  const [showNewNote, setShowNewNote] = useState(false)
  const [menuId, setMenuId] = useState<string | null>(null)
  const prevMatCount = useRef(materials.length)

  // 工具卡片点击
  const handleToolClick = async (type: string, label: string) => {
    if (loadingTool) return
    setLoadingTool(type)
    try {
      const res = await fetch(`/api/studio/${type}?plan_id=${encodeURIComponent(planId)}`)
      if (res.ok) {
        const data = await res.json()
        addGeneratedContent({
          id: `${type}-${Date.now()}`,
          type: type as GeneratedContent['type'],
          title: data.title || label,
          content: data.content,
          createdAt: new Date().toISOString(),
        })
      }
    } catch { /* 静默 */ }
    finally { setLoadingTool(null) }
  }

  // 首次添加材料自动生成学习指南
  useEffect(() => {
    const prev = prevMatCount.current
    prevMatCount.current = materials.length
    if (prev === 0 && materials.length === 1) {
      if (!generatedContents.some(c => c.type === 'study-guide')) {
        handleToolClick('study-guide', '学习指南')
      }
    }
  }, [materials.length])

  const handleSaveNote = (data: { id?: string; title: string; content: string }) => {
    if (data.id) {
      updateNote(data.id, { title: data.title, content: data.content, updatedAt: new Date().toISOString() })
    } else {
      addNote({ id: 'note-' + Date.now(), title: data.title, content: data.content, updatedAt: new Date().toISOString() })
    }
    setEditingNote(null); setShowNewNote(false)
  }

  const handleDeleteContent = (id: string) => {
    useStudioStore.setState((s) => ({
      generatedContents: s.generatedContents.filter(c => c.id !== id)
    }))
    setMenuId(null)
  }

  const handleDeleteNote = (id: string) => {
    deleteNote(id)
    setMenuId(null)
  }

  const handleExport = (c: GeneratedContent) => {
    const blob = new Blob([c.content], { type: 'text/markdown;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    Object.assign(document.createElement('a'), { href: url, download: c.title + '.md' }).click()
    URL.revokeObjectURL(url)
    setMenuId(null)
  }

  const fmt = (iso: string) => {
    const d = new Date(iso)
    const now = new Date()
    const diff = now.getTime() - d.getTime()
    if (diff < 60000) return '刚刚'
    if (diff < 3600000) return Math.floor(diff / 60000) + ' 分钟前'
    if (diff < 86400000) return Math.floor(diff / 3600000) + ' 小时前'
    return Math.floor(diff / 86400000) + ' 天前'
  }

  // 合并内容列表：AI 生成 + 笔记，按时间倒序
  const allItems = [
    ...generatedContents.map(c => ({ ...c, kind: 'generated' as const })),
    ...notes.map(n => ({ ...n, kind: 'note' as const, type: 'note' as const, content: n.content, createdAt: n.updatedAt })),
  ].sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime())

  return (
    <div className="flex flex-col h-full overflow-hidden bg-white dark:bg-dark-bg">
      {/* 标题栏 */}
      <div className="flex items-center justify-between px-4 h-12 flex-shrink-0 border-b border-[#DADCE0] dark:border-dark-border">
        <span className="text-base font-semibold text-[#202124] dark:text-dark-text">Studio</span>
        <button onClick={() => setDevMode(!devMode)}
          className={`text-xs px-2 py-0.5 rounded-full transition-all ${devMode ? 'bg-blue-50 text-blue-600 border border-blue-300' : 'text-gray-400 hover:text-gray-600'}`}
          aria-label="开发者模式">DEV</button>
      </div>

      <div className="flex-1 overflow-y-auto">
        {/* 工具卡片网格 — NotebookLM 风格 */}
        <div className="grid grid-cols-3 gap-2 p-3">
          {TOOLS.map(t => (
            <button key={t.type} onClick={() => handleToolClick(t.type, t.label)}
              disabled={!!loadingTool}
              className={`relative flex flex-col items-start p-3 rounded-xl border ${t.color} hover:shadow-md hover:-translate-y-0.5 transition-all duration-150 cursor-pointer min-h-[72px]`}>
              <span className={`text-xl ${t.iconBg}`}>{t.icon}</span>
              <span className="text-sm font-medium text-gray-700 mt-1">{t.label}</span>
              {loadingTool === t.type && (
                <div className="absolute inset-0 bg-white/60 rounded-xl flex items-center justify-center">
                  <div className="w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
                </div>
              )}
            </button>
          ))}
        </div>

        {/* 内容列表 */}
        <div className="px-3 pb-3">
          {allItems.length === 0 ? (
            <p className="text-sm text-gray-400 text-center py-8">点击上方工具卡片生成内容</p>
          ) : (
            <ul className="flex flex-col">
              {allItems.map(item => (
                <li key={item.id}
                  className="flex items-center gap-3 px-3 py-3 rounded-xl hover:bg-gray-50 dark:hover:bg-dark-surface cursor-pointer transition-colors group relative"
                  onClick={() => item.kind === 'generated' ? setViewingContent(item as GeneratedContent) : setEditingNote(item as unknown as Note)}>
                  {/* 图标 */}
                  <span className="w-9 h-9 rounded-lg bg-gray-100 flex items-center justify-center text-base flex-shrink-0">
                    {item.kind === 'note' ? '📝' : (TYPE_ICONS[item.type] || '📄')}
                  </span>
                  {/* 标题 + 元信息 */}
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-800 dark:text-dark-text truncate">{item.title}</p>
                    <p className="text-sm text-gray-400 mt-0.5">
                      {item.kind === 'note' ? '笔记' : item.type === 'learning-plan' ? '学习计划' : item.type === 'study-guide' ? '学习指南' : item.type === 'flashcards' ? '闪卡' : item.type === 'quiz' ? '测验' : '报告'}
                      {' · '}{fmt(item.createdAt)}
                    </p>
                  </div>
                  {/* 菜单按钮 */}
                  <button onClick={(e) => { e.stopPropagation(); setMenuId(menuId === item.id ? null : item.id) }}
                    className="opacity-0 group-hover:opacity-100 w-7 h-7 flex items-center justify-center rounded-full hover:bg-gray-200 transition-all text-gray-400"
                    aria-label="更多操作">⋮</button>
                  {/* 下拉菜单 */}
                  {menuId === item.id && (
                    <div className="absolute right-2 top-12 z-20 bg-white dark:bg-dark-surface border border-gray-200 rounded-xl shadow-lg py-1 min-w-[120px]"
                      onClick={e => e.stopPropagation()}>
                      {item.kind === 'generated' && (
                        <button onClick={() => handleExport(item as GeneratedContent)}
                          className="w-full text-left px-3 py-2 text-sm text-gray-700 hover:bg-gray-50">导出 .md</button>
                      )}
                      <button onClick={() => item.kind === 'generated' ? handleDeleteContent(item.id) : handleDeleteNote(item.id)}
                        className="w-full text-left px-3 py-2 text-sm text-red-500 hover:bg-red-50">删除</button>
                    </div>
                  )}
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>

      {/* 底部：添加笔记按钮 */}
      <div className="flex-shrink-0 px-4 py-3 border-t border-gray-200 dark:border-dark-border">
        <button onClick={() => setShowNewNote(true)}
          className="w-full flex items-center justify-center gap-2 h-10 rounded-full border border-gray-300 text-sm text-gray-600 hover:bg-gray-50 hover:border-gray-400 transition-all">
          📝 添加笔记
        </button>
      </div>

      {/* 弹窗 */}
      {viewingContent && <ContentViewer content={viewingContent} onClose={() => setViewingContent(null)} />}
      {(editingNote || showNewNote) && (
        <NoteEditor note={editingNote || undefined} onSave={handleSaveNote}
          onClose={() => { setEditingNote(null); setShowNewNote(false) }} planId={planId} />
      )}
    </div>
  )
}
