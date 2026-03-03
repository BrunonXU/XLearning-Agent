import React, { useState, useEffect, useRef } from 'react'
import { TodayTasks } from './TodayTasks'
import { ToolGrid } from './ToolGrid'
import { ContentLibrary } from './ContentLibrary'
import { useStudioStore } from '../../store/studioStore'
import { useSourceStore } from '../../store/sourceStore'
import type { StudioTool, GeneratedContent } from '../../types'

const STUDIO_TOOLS: StudioTool[] = [
  { type: 'learning-plan', icon: '📅', label: '学习计划' },
  { type: 'progress-report', icon: '📊', label: '进度报告' },
  { type: 'quiz', icon: '🧪', label: '测验' },
  { type: 'study-guide', icon: '📖', label: '学习指南' },
  { type: 'flashcards', icon: '🃏', label: '闪卡' },
]

// 9.1: 开发者工具卡片（仅 devMode 下显示）
const DEV_TOOLS: StudioTool[] = [
  { type: 'learning-plan', icon: '🔀', label: 'LangGraph' },
  { type: 'progress-report', icon: '🔍', label: 'Agent Trace' },
]

interface AgentTrace {
  tool: string
  durationMs: number
  tokens: number
  timestamp: string
}

interface StudioPanelProps {
  planId?: string
}

export const StudioPanel: React.FC<StudioPanelProps> = ({ planId = '' }) => {
  const {
    currentDay, toggleTask, completeDay,
    addGeneratedContent, generatedContents,
    devMode, setDevMode,
    langGraphEnabled, setLangGraphEnabled,
  } = useStudioStore()
  const { materials } = useSourceStore()
  const [loadingTool, setLoadingTool] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<'ai-generated' | 'my-notes'>('ai-generated')
  const prevMaterialCount = useRef(materials.length)

  // 9.3: Agent Trace 状态
  const [traces, setTraces] = useState<AgentTrace[]>([])
  const [showTrace, setShowTrace] = useState(false)

  // 9.4: LangSmith 状态
  const [langsmithOk, setLangsmithOk] = useState<boolean | null>(null)
  useEffect(() => {
    fetch('/api/health').then(r => r.ok ? setLangsmithOk(true) : setLangsmithOk(false)).catch(() => setLangsmithOk(false))
  }, [])

  // 8.3: 完成 Day 时同步后端（幂等）
  const handleCompleteDay = async (dayNumber: number) => {
    completeDay(dayNumber)
    try {
      await fetch(`/api/plan/day/${dayNumber}/complete?plan_id=${planId}`, { method: 'PUT' })
    } catch { /* 幂等 */ }
  }

  // 8.4: 工具卡片点击触发内容生成
  const handleToolClick = async (tool: StudioTool) => {
    if (loadingTool) return
    setLoadingTool(tool.type)
    setActiveTab('ai-generated')
    const t0 = Date.now()
    try {
      const res = await fetch(`/api/studio/${tool.type}?plan_id=${encodeURIComponent(planId)}`)
      if (res.ok) {
        const data = await res.json()
        const content: GeneratedContent = {
          id: `${tool.type}-${Date.now()}`,
          type: tool.type as GeneratedContent['type'],
          title: data.title,
          content: data.content,
          createdAt: new Date().toISOString(),
        }
        addGeneratedContent(content)
        // 9.3: 记录 trace
        if (devMode) {
          setTraces((prev: AgentTrace[]) => [{
            tool: tool.label,
            durationMs: Date.now() - t0,
            tokens: Math.round(data.content.length / 4),
            timestamp: new Date().toLocaleTimeString('zh-CN'),
          }, ...prev].slice(0, 20))
        }
      }
    } catch { /* 静默 */ }
    finally { setLoadingTool(null) }
  }

  // 8.5: 首次添加材料自动触发学习指南
  useEffect(() => {
    const prev = prevMaterialCount.current
    prevMaterialCount.current = materials.length
    if (prev === 0 && materials.length === 1) {
      const alreadyHasGuide = generatedContents.some(c => c.type === 'study-guide')
      if (!alreadyHasGuide) {
        handleToolClick({ type: 'study-guide', icon: '📖', label: '学习指南' })
      }
    }
  }, [materials.length])

  // 9.2: LangGraph 切换
  const handleLangGraphToggle = () => {
    setLangGraphEnabled(!langGraphEnabled)
  }

  return (
    <div className="flex flex-col h-full overflow-hidden">
      <div className="flex items-center px-4 h-12 flex-shrink-0 border-b border-[#DADCE0] dark:border-dark-border">
        <span className="text-sm font-semibold text-[#202124] dark:text-dark-text flex-1">
          ✨ Studio
        </span>
        {/* 9.1: Dev Mode 开关 */}
        <button
          onClick={() => setDevMode(!devMode)}
          aria-label={devMode ? '关闭开发者模式' : '开启开发者模式'}
          title={devMode ? '关闭开发者模式' : '开启开发者模式'}
          className={`text-xs px-2 py-0.5 rounded-full transition-all duration-150 ${
            devMode
              ? 'bg-[#E8F0FE] text-[#1A73E8] border border-[#1A73E8]'
              : 'text-[#9AA0A6] hover:text-[#5F6368]'
          }`}
        >
          DEV
        </button>
      </div>

      <div className="flex-1 overflow-y-auto scrollbar-thin flex flex-col">
        <div className="px-3 pt-3">
          <TodayTasks
            currentDay={currentDay}
            onTaskToggle={(i) => currentDay && toggleTask(currentDay.dayNumber, i)}
            onCompleteDay={handleCompleteDay}
          />
        </div>

        <div className="px-3 pt-3">
          <p className="text-xs font-medium text-[#5F6368] uppercase tracking-wide mb-2">
            学习工具
          </p>
          <ToolGrid tools={STUDIO_TOOLS} onToolClick={handleToolClick} loadingTool={loadingTool ?? undefined} />
        </div>

        {/* 9.1: 开发者工具区块 */}
        {devMode && (
          <div className="px-3 pt-3">
            <p className="text-xs font-medium text-[#5F6368] uppercase tracking-wide mb-2">
              开发者工具
            </p>
            <ToolGrid tools={DEV_TOOLS} onToolClick={() => {}} />

            {/* 9.2: LangGraph 切换 */}
            <div className="mt-2 flex items-center justify-between px-2 py-2 bg-white rounded-xl border border-[#DADCE0] shadow-sm">
              <span className="text-xs text-[#202124] flex items-center gap-1.5">
                🔀 LangGraph 模式
              </span>
              <button
                onClick={handleLangGraphToggle}
                aria-label={langGraphEnabled ? '关闭 LangGraph' : '开启 LangGraph'}
                className={`relative w-9 h-5 rounded-full transition-colors duration-200 ${
                  langGraphEnabled ? 'bg-[#1A73E8]' : 'bg-[#DADCE0]'
                }`}
              >
                <span className={`absolute top-0.5 w-4 h-4 bg-white rounded-full shadow transition-transform duration-200 ${
                  langGraphEnabled ? 'translate-x-4' : 'translate-x-0.5'
                }`} />
              </button>
            </div>

            {/* 9.3: Agent Trace 卡片 */}
            <div className="mt-2 bg-white rounded-xl border border-[#DADCE0] shadow-sm overflow-hidden">
              <button
                onClick={() => setShowTrace((v: boolean) => !v)}
                className="w-full flex items-center justify-between px-3 py-2 text-xs text-[#202124] hover:bg-[#F1F3F4] transition-colors duration-150"
              >
                <span className="flex items-center gap-1.5">🔍 Agent Trace</span>
                <span className="text-[#9AA0A6]">{showTrace ? '▲' : '▼'}</span>
              </button>
              {showTrace && (
                <div className="border-t border-[#DADCE0] max-h-40 overflow-y-auto">
                  {traces.length === 0 ? (
                    <p className="text-xs text-[#9AA0A6] text-center py-3">点击工具卡片后显示 trace</p>
                  ) : (
                    <ul className="divide-y divide-[#F1F3F4]">
                      {traces.map((t: AgentTrace, i: number) => (
                        <li key={i} className="px-3 py-1.5 text-xs text-[#5F6368]">
                          <span className="font-medium text-[#202124]">{t.tool}</span>
                          <span className="ml-2">{t.durationMs}ms</span>
                          <span className="ml-2">~{t.tokens} tokens</span>
                          <span className="ml-2 text-[#9AA0A6]">{t.timestamp}</span>
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
              )}
            </div>
          </div>
        )}

        <div className="flex-1 px-0 pt-3 min-h-0">
          <ContentLibrary planId={planId} activeTab={activeTab} onTabChange={setActiveTab} />
        </div>
      </div>

      {/* 9.4: 底部状态栏 — LangSmith 指示器 */}
      <div className="h-8 border-t border-[#DADCE0] dark:border-dark-border px-3 flex items-center flex-shrink-0 gap-3">
        <span className="text-xs text-[#5F6368] flex items-center gap-1">
          <span className={`w-1.5 h-1.5 rounded-full inline-block ${
            langsmithOk === null ? 'bg-yellow-400' : langsmithOk ? 'bg-green-500' : 'bg-red-400'
          }`} />
          LangSmith {langsmithOk === null ? '…' : langsmithOk ? '✅' : '❌'}
        </span>
        {devMode && langGraphEnabled && (
          <span className="text-xs text-[#1A73E8] font-medium">LangGraph ON</span>
        )}
      </div>
    </div>
  )
}
