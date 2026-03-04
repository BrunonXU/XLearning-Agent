/**
 * DevPanel — 开发者调试面板
 * 展示 LangSmith 状态、Agent 调用 Trace、系统信息
 */
import React, { useState, useEffect, useCallback } from 'react'

interface TraceEntry {
  id: string
  type: string
  name: string
  startTime: string
  duration: number
  status: string
  input: string
  output: string
  tokens: { prompt: number; completion: number; total: number }
  metadata: Record<string, any>
}

interface DevStatus {
  langsmith: {
    enabled: boolean
    connected: boolean
    hasApiKey: boolean
    packageInstalled: boolean
    project: string
  }
  system: {
    provider: string
    model: string
    tracesCount: number
  }
}

export const DevPanel: React.FC = () => {
  const [status, setStatus] = useState<DevStatus | null>(null)
  const [traces, setTraces] = useState<TraceEntry[]>([])
  const [expandedId, setExpandedId] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  const fetchData = useCallback(async () => {
    try {
      const [statusRes, tracesRes] = await Promise.all([
        fetch('/api/dev/status'),
        fetch('/api/dev/traces?limit=20'),
      ])
      if (statusRes.ok) setStatus(await statusRes.json())
      if (tracesRes.ok) setTraces(await tracesRes.json())
    } catch { /* 静默 */ }
    finally { setLoading(false) }
  }, [])

  useEffect(() => { fetchData() }, [fetchData])

  // 每 5 秒自动刷新
  useEffect(() => {
    const timer = setInterval(fetchData, 5000)
    return () => clearInterval(timer)
  }, [fetchData])

  const toggleLangSmith = async () => {
    if (!status) return
    const next = !status.langsmith.enabled
    try {
      await fetch('/api/dev/langsmith', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ enabled: next }),
      })
      setStatus(s => s ? { ...s, langsmith: { ...s.langsmith, enabled: next, connected: next && s.langsmith.hasApiKey && s.langsmith.packageInstalled } } : s)
    } catch { /* 静默 */ }
  }

  const fmtDuration = (ms: number) => ms < 1000 ? `${ms}ms` : `${(ms / 1000).toFixed(1)}s`
  const fmtTime = (iso: string) => {
    try { return new Date(iso).toLocaleTimeString('zh-CN', { hour12: false }) } catch { return iso }
  }

  const typeColors: Record<string, string> = {
    chain: 'bg-blue-100 text-blue-700',
    llm: 'bg-purple-100 text-purple-700',
    tool: 'bg-green-100 text-green-700',
    retriever: 'bg-orange-100 text-orange-700',
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="w-5 h-5 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-4 px-6 py-4 text-sm">
      {/* LangSmith 状态卡片 */}
      <div className="rounded-xl border border-[#E0E0E0] p-4">
        <div className="flex items-center justify-between mb-3">
          <span className="font-medium text-[#202124]">🔗 LangSmith</span>
          <button
            onClick={toggleLangSmith}
            className={`relative w-10 h-5 rounded-full transition-colors duration-200 ${status?.langsmith.enabled ? 'bg-blue-500' : 'bg-gray-300'}`}
            aria-label="切换 LangSmith"
          >
            <span className={`absolute top-0.5 w-4 h-4 rounded-full bg-white shadow transition-transform duration-200 ${status?.langsmith.enabled ? 'translate-x-5' : 'translate-x-0.5'}`} />
          </button>
        </div>
        <div className="grid grid-cols-2 gap-2 text-xs">
          <div className="flex items-center gap-1.5">
            <span className={`w-2 h-2 rounded-full ${status?.langsmith.connected ? 'bg-green-500' : 'bg-gray-300'}`} />
            <span className="text-[#5F6368]">{status?.langsmith.connected ? '已连接' : '未连接'}</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className={`w-2 h-2 rounded-full ${status?.langsmith.hasApiKey ? 'bg-green-500' : 'bg-red-400'}`} />
            <span className="text-[#5F6368]">{status?.langsmith.hasApiKey ? 'API Key ✓' : 'API Key ✗'}</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className={`w-2 h-2 rounded-full ${status?.langsmith.packageInstalled ? 'bg-green-500' : 'bg-red-400'}`} />
            <span className="text-[#5F6368]">{status?.langsmith.packageInstalled ? 'SDK ✓' : 'SDK ✗'}</span>
          </div>
          <div className="text-[#5F6368]">📁 {status?.langsmith.project}</div>
        </div>
      </div>

      {/* 系统信息 */}
      <div className="rounded-xl border border-[#E0E0E0] p-4">
        <span className="font-medium text-[#202124] block mb-2">⚙️ 系统</span>
        <div className="flex flex-wrap gap-2">
          <span className="px-2 py-0.5 rounded-full bg-[#E8F0FE] text-[#1A73E8] text-xs">{status?.system.provider}</span>
          <span className="px-2 py-0.5 rounded-full bg-[#E8F0FE] text-[#1A73E8] text-xs">{status?.system.model}</span>
          <span className="px-2 py-0.5 rounded-full bg-gray-100 text-[#5F6368] text-xs">{status?.system.tracesCount} traces</span>
        </div>
      </div>

      {/* Trace 列表 */}
      <div>
        <div className="flex items-center justify-between mb-2">
          <span className="font-medium text-[#202124]">📊 调用记录</span>
          <button onClick={fetchData} className="text-xs text-[#1A73E8] hover:underline">刷新</button>
        </div>
        {traces.length === 0 ? (
          <p className="text-xs text-[#9AA0A6] text-center py-6">暂无调用记录，发送消息后会自动记录</p>
        ) : (
          <ul className="flex flex-col gap-1">
            {traces.map(t => (
              <li key={t.id}>
                <button
                  onClick={() => setExpandedId(expandedId === t.id ? null : t.id)}
                  className="w-full flex items-center gap-2 px-3 py-2 rounded-lg hover:bg-gray-50 transition-colors text-left"
                >
                  <span className={`px-1.5 py-0.5 rounded text-[10px] font-mono ${typeColors[t.type] || 'bg-gray-100 text-gray-600'}`}>
                    {t.type}
                  </span>
                  <span className="flex-1 truncate text-xs text-[#202124]">{t.name}</span>
                  <span className={`text-[10px] font-mono ${t.status === 'ok' ? 'text-green-600' : 'text-red-500'}`}>
                    {fmtDuration(t.duration)}
                  </span>
                </button>
                {expandedId === t.id && (
                  <div className="mx-3 mb-2 p-3 rounded-lg bg-[#F8F9FA] text-xs space-y-2">
                    <div>
                      <span className="text-[#9AA0A6]">时间</span>
                      <span className="ml-2 text-[#202124]">{fmtTime(t.startTime)}</span>
                    </div>
                    <div>
                      <span className="text-[#9AA0A6]">输入</span>
                      <pre className="mt-1 p-2 rounded bg-white border border-[#E0E0E0] text-[11px] whitespace-pre-wrap break-all max-h-24 overflow-y-auto">{t.input || '(空)'}</pre>
                    </div>
                    <div>
                      <span className="text-[#9AA0A6]">输出</span>
                      <pre className="mt-1 p-2 rounded bg-white border border-[#E0E0E0] text-[11px] whitespace-pre-wrap break-all max-h-24 overflow-y-auto">{t.output || '(空)'}</pre>
                    </div>
                    {Object.keys(t.metadata).length > 0 && (
                      <div>
                        <span className="text-[#9AA0A6]">元数据</span>
                        <pre className="mt-1 p-2 rounded bg-white border border-[#E0E0E0] text-[11px] whitespace-pre-wrap">{JSON.stringify(t.metadata, null, 2)}</pre>
                      </div>
                    )}
                  </div>
                )}
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  )
}
