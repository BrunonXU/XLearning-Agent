/**
 * ContentViewer — AI 生成内容查看弹窗
 * - 普通内容：ReactMarkdown 渲染
 * - mind-map：markmap 交互式思维导图
 * - progress-report：结构化 JSON 渲染（fallback Markdown）
 * - learning-plan：结构化天数渲染（fallback Markdown）
 */
import React, { useRef, useEffect, useState } from 'react'
import ReactMarkdown from 'react-markdown'
import type { GeneratedContent } from '../../types'

interface ContentViewerProps {
  content: GeneratedContent
  onClose: () => void
}

/** 从可能被 ```json 包裹的字符串中提取 JSON */
function extractJSON(raw: string): any | null {
  // 先直接尝试
  try { return JSON.parse(raw) } catch {}
  // 尝试提取 ```json ... ``` 块
  const m = raw.match(/```(?:json)?\s*\n?([\s\S]*?)\n?```/)
  if (m) { try { return JSON.parse(m[1]) } catch {} }
  return null
}

/** 思维导图渲染组件 */
const MindMapRenderer: React.FC<{ markdown: string }> = ({ markdown }) => {
  const svgRef = useRef<SVGSVGElement>(null)
  const [error, setError] = useState(false)

  useEffect(() => {
    let mm: any = null
    let cancelled = false
    const render = async () => {
      try {
        const { Transformer } = await import('markmap-lib')
        const { Markmap } = await import('markmap-view')
        if (cancelled || !svgRef.current) return
        const transformer = new Transformer()
        const { root } = transformer.transform(markdown)
        svgRef.current.innerHTML = ''
        mm = Markmap.create(svgRef.current, { duration: 300, maxWidth: 300 }, root)
      } catch { if (!cancelled) setError(true) }
    }
    render()
    return () => { cancelled = true; mm?.destroy?.() }
  }, [markdown])

  if (error) return <ReactMarkdown>{markdown}</ReactMarkdown>
  return <svg ref={svgRef} className="w-full" style={{ minHeight: 500 }} />
}

/** 进度报告 JSON 渲染 */
const ProgressReportRenderer: React.FC<{ content: string }> = ({ content }) => {
  const data = extractJSON(content)
  if (!data || typeof data !== 'object') return <ReactMarkdown>{content}</ReactMarkdown>

  return (
    <div className="space-y-6">
      {data.summary && (
        <div>
          <h3 className="text-base font-semibold text-gray-800 mb-2">📋 总结</h3>
          <p className="text-sm text-gray-600 leading-relaxed">{data.summary}</p>
        </div>
      )}
      {data.knowledgeGraph && Array.isArray(data.knowledgeGraph) && (
        <div>
          <h3 className="text-base font-semibold text-gray-800 mb-2">🧠 知识图谱</h3>
          <div className="flex flex-wrap gap-2">
            {data.knowledgeGraph.map((item: any, i: number) => {
              const label = typeof item === 'string' ? item : (item.topic || item.name || JSON.stringify(item))
              const status = typeof item === 'object' ? item.status : null
              return (
                <span key={i} className={`px-3 py-1.5 rounded-full text-xs font-medium ${
                  status === 'mastered' ? 'bg-green-100 text-green-700' :
                  status === 'learning' ? 'bg-yellow-100 text-yellow-700' :
                  'bg-gray-100 text-gray-600'
                }`}>{label}</span>
              )
            })}
          </div>
        </div>
      )}
      {data.timeline && Array.isArray(data.timeline) && (
        <div>
          <h3 className="text-base font-semibold text-gray-800 mb-2">📅 学习时间线</h3>
          <div className="space-y-2">
            {data.timeline.map((entry: any, i: number) => (
              <div key={i} className="flex items-center gap-3">
                <div className={`w-3 h-3 rounded-full flex-shrink-0 ${entry.completed ? 'bg-green-500' : 'bg-gray-300'}`} />
                <span className="text-sm font-medium text-gray-700">{entry.day || entry.date || `Day ${i + 1}`}</span>
                <span className="text-sm text-gray-500 flex-1">{entry.topic || entry.content || ''}</span>
              </div>
            ))}
          </div>
        </div>
      )}
      {data.weakPoints && Array.isArray(data.weakPoints) && data.weakPoints.length > 0 && (
        <div>
          <h3 className="text-base font-semibold text-gray-800 mb-2">⚠️ 薄弱环节</h3>
          <ul className="list-disc list-inside space-y-1">
            {data.weakPoints.map((wp: any, i: number) => (
              <li key={i} className="text-sm text-gray-600">{typeof wp === 'string' ? wp : wp.topic || wp.description || JSON.stringify(wp)}</li>
            ))}
          </ul>
        </div>
      )}
      {data.nextSteps && Array.isArray(data.nextSteps) && (
        <div>
          <h3 className="text-base font-semibold text-gray-800 mb-2">🚀 下一步建议</h3>
          <ul className="list-disc list-inside space-y-1">
            {data.nextSteps.map((step: any, i: number) => (
              <li key={i} className="text-sm text-gray-600">{typeof step === 'string' ? step : step.description || step.action || JSON.stringify(step)}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}

/** 学习计划 JSON 渲染 */
const LearningPlanRenderer: React.FC<{ content: string }> = ({ content }) => {
  const data = extractJSON(content)
  if (!data) return <ReactMarkdown>{content}</ReactMarkdown>

  const days = data.days || (Array.isArray(data) ? data : null)
  if (!days) return <ReactMarkdown>{content}</ReactMarkdown>

  return (
    <div className="space-y-4">
      {days.map((day: any, i: number) => (
        <div key={i} className="border border-gray-200 rounded-xl p-4">
          <div className="flex items-center gap-2 mb-2">
            <span className="w-8 h-8 rounded-lg bg-green-100 text-green-700 flex items-center justify-center text-sm font-bold">
              {day.dayNumber || i + 1}
            </span>
            <h4 className="text-sm font-semibold text-gray-800">{day.title}</h4>
          </div>
          {day.tasks && Array.isArray(day.tasks) && (
            <ul className="ml-10 space-y-1 mb-2">
              {day.tasks.map((t: any, j: number) => (
                <li key={j} className="text-sm text-gray-600 flex items-center gap-2">
                  <span className="w-1.5 h-1.5 rounded-full bg-gray-400 flex-shrink-0" />
                  {typeof t === 'string' ? t : t.title || JSON.stringify(t)}
                </li>
              ))}
            </ul>
          )}
          {day.learningObjectives && (
            <p className="text-xs text-blue-600 ml-10">🎯 {Array.isArray(day.learningObjectives) ? day.learningObjectives.join('、') : day.learningObjectives}</p>
          )}
          {day.knowledgePoints && Array.isArray(day.knowledgePoints) && (
            <div className="flex flex-wrap gap-1 ml-10 mt-1">
              {day.knowledgePoints.map((kp: string, k: number) => (
                <span key={k} className="px-2 py-0.5 bg-purple-50 text-purple-600 rounded text-xs">{kp}</span>
              ))}
            </div>
          )}
        </div>
      ))}
    </div>
  )
}

export const ContentViewer: React.FC<ContentViewerProps> = ({ content, onClose }) => {
  const totalVersions = (content.versions?.length || 0) + 1
  const [viewingVersion, setViewingVersion] = useState(content.version || 1)

  // Build version list: current + history
  const allVersions = [
    { content: content.content, createdAt: content.createdAt, version: content.version || 1 },
    ...(content.versions || []),
  ].sort((a, b) => b.version - a.version)

  const current = allVersions.find(v => v.version === viewingVersion) || allVersions[0]

  const handleExport = () => {
    const blob = new Blob([current.content], { type: 'text/markdown;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${content.title}-v${viewingVersion}.md`
    a.click()
    URL.revokeObjectURL(url)
  }

  const renderContent = (text: string) => {
    if (content.type === 'mind-map') return <MindMapRenderer markdown={text} />
    if (content.type === 'progress-report') return <ProgressReportRenderer content={text} />
    if (content.type === 'learning-plan') return <LearningPlanRenderer content={text} />
    return <ReactMarkdown>{text || '（内容为空）'}</ReactMarkdown>
  }

  const fmtDate = (iso: string) => {
    try { return new Date(iso).toLocaleString('zh-CN', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' }) } catch { return iso }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm" onClick={onClose}>
      <div className="bg-white dark:bg-dark-surface rounded-2xl shadow-2xl w-[90vw] max-w-[900px] max-h-[90vh] flex flex-col overflow-hidden"
        onClick={e => e.stopPropagation()}>
        {/* 标题栏 */}
        <div className="flex items-center justify-between px-5 py-3.5 border-b border-[#DADCE0] dark:border-dark-border flex-shrink-0">
          <div className="flex items-center gap-3">
            <span className="text-base font-semibold text-[#202124] dark:text-dark-text">
              {content.title}
            </span>
            {totalVersions > 1 && (
              <span className="text-xs text-gray-400 bg-gray-100 px-2 py-0.5 rounded-full">
                V{viewingVersion} · {fmtDate(current.createdAt)}
              </span>
            )}
          </div>
          <div className="flex items-center gap-2">
            {totalVersions > 1 && (
              <div className="flex items-center gap-1 mr-2">
                <button onClick={() => setViewingVersion(v => Math.max(1, v - 1))}
                  disabled={viewingVersion <= 1}
                  className="w-7 h-7 flex items-center justify-center rounded-lg text-gray-500 hover:bg-gray-100 disabled:opacity-30 disabled:cursor-not-allowed text-sm">
                  ‹
                </button>
                <span className="text-xs text-gray-500 min-w-[40px] text-center">{viewingVersion}/{totalVersions}</span>
                <button onClick={() => setViewingVersion(v => Math.min(totalVersions, v + 1))}
                  disabled={viewingVersion >= totalVersions}
                  className="w-7 h-7 flex items-center justify-center rounded-lg text-gray-500 hover:bg-gray-100 disabled:opacity-30 disabled:cursor-not-allowed text-sm">
                  ›
                </button>
              </div>
            )}
            <button onClick={handleExport} aria-label="导出"
              className="h-7 px-3 rounded-lg text-xs text-[#5F6368] hover:bg-[#F1F3F4] dark:hover:bg-dark-border transition-colors duration-150 flex items-center gap-1">
              ↓ 导出
            </button>
            <button onClick={onClose} aria-label="关闭"
              className="w-8 h-8 flex items-center justify-center rounded-full hover:bg-gray-100 text-[#5F6368] hover:text-[#202124] transition-colors text-xl">
              ×
            </button>
          </div>
        </div>
        {/* 内容区 */}
        <div className={`flex-1 overflow-y-auto px-6 py-5 ${content.type === 'mind-map' ? '' : content.type === 'progress-report' || content.type === 'learning-plan' ? '' : 'prose prose-sm max-w-none dark:prose-invert'}`}>
          {renderContent(current.content)}
        </div>
      </div>
    </div>
  )
}
