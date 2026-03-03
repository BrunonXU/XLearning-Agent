import React, { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import { WorkspaceLayout } from '../components/layout/WorkspaceLayout'
import { TopNav } from '../components/layout/TopNav'
import { SourcePanel } from '../components/source-panel/SourcePanel'
import { ChatArea } from '../components/chat/ChatArea'
import { StudioPanel } from '../components/studio/StudioPanel'
import { useKeyboard } from '../hooks/useKeyboard'
import { useChatStore } from '../store/chatStore'
import { useSourceStore } from '../store/sourceStore'
import { usePlanStore } from '../store/planStore'
import type { ChatMessage, Material } from '../types'

const WorkspacePage: React.FC = () => {
  const { planId } = useParams<{ planId: string }>()
  const [isDark, setIsDark] = useState(() => {
    const saved = localStorage.getItem('theme')
    if (saved === 'dark') { document.documentElement.classList.add('dark'); return true }
    return false
  })
  const [isRestoring, setIsRestoring] = useState(true)

  const { plans } = usePlanStore()
  const planTitle = plans.find(p => p.id === planId)?.title ?? '学习规划'

  const toggleDark = () => {
    setIsDark(d => {
      const next = !d
      document.documentElement.classList.toggle('dark', next)
      localStorage.setItem('theme', next ? 'dark' : 'light')
      return next
    })
  }

  // 12.1: 页面加载时从后端恢复会话状态
  useEffect(() => {
    if (!planId) { setIsRestoring(false); return }
    fetch(`/api/session/${planId}`)
      .then(r => r.ok ? r.json() : null)
      .then(data => {
        if (!data) return
        // 恢复对话历史
        if (data.messages?.length > 0) {
          const msgs: ChatMessage[] = data.messages.map((m: any) => ({
            id: m.id ?? `restored-${Date.now()}-${Math.random()}`,
            role: m.role,
            content: m.content,
            createdAt: m.createdAt ?? new Date().toISOString(),
          }))
          useChatStore.getState().setMessages(msgs)
        }
        // 恢复材料列表
        if (data.materials?.length > 0) {
          const mats: Material[] = data.materials.map((m: any) => ({
            id: m.id,
            type: m.type ?? 'other',
            name: m.name ?? m.filename ?? '未知材料',
            url: m.url,
            status: m.status ?? 'ready',
            addedAt: m.addedAt ?? new Date().toISOString(),
          }))
          useSourceStore.getState().setMaterials(mats)
        }
      })
      .catch(() => { /* 静默失败，使用 store 缓存 */ })
      .finally(() => setIsRestoring(false))
  }, [planId])

  // 11.1: Ctrl+K 聚焦输入框
  useKeyboard({
    onFocusInput: () => {
      const textarea = document.querySelector<HTMLTextAreaElement>('textarea[aria-label="输入消息"]')
      textarea?.focus()
    },
  })

  // 12.4: 加载骨架屏
  if (isRestoring) {
    return (
      <div className="flex flex-col h-screen bg-[#F8F9FA] dark:bg-dark-bg">
        <div className="h-14 bg-white dark:bg-dark-bg border-b border-[#DADCE0] animate-pulse" />
        <div className="flex flex-1 gap-0">
          <div className="w-[22%] bg-[#F1F3F4] animate-pulse" />
          <div className="flex-1 bg-white animate-pulse" />
          <div className="w-[28%] bg-[#F1F3F4] animate-pulse" />
        </div>
      </div>
    )
  }

  return (
    <WorkspaceLayout
      topNav={
        <TopNav
          planTitle={planTitle}
          onToggleDark={toggleDark}
          isDark={isDark}
        />
      }
      left={<SourcePanel planId={planId} />}
      center={<ChatArea planId={planId} />}
      right={<StudioPanel planId={planId} />}
    />
  )
}

export default WorkspacePage
