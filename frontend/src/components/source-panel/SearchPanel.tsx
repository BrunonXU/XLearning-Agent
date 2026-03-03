/**
 * SearchPanel — 资源搜索面板
 *
 * 功能：
 * - 关键词输入 + 平台多选
 * - 调用 /api/search/stream SSE 端点，逐平台显示进度
 * - 搜索超时（>15s）显示"搜索超时"
 * - 勾选结果 + "加入学习材料"按钮
 */
import React, { useState, useRef, useCallback, useEffect } from 'react'
import { SearchResultItem } from './SearchResultItem'
import { Button } from '../ui/Button'
import type { SearchResult, PlatformType } from '../../types'

const PLATFORMS: { key: PlatformType; label: string; icon: string }[] = [
  { key: 'bilibili', label: 'B站', icon: '📺' },
  { key: 'youtube', label: 'YouTube', icon: '🎬' },
  { key: 'google', label: 'Google', icon: '🌐' },
  { key: 'github', label: 'GitHub', icon: '🔗' },
  { key: 'xiaohongshu', label: '小红书', icon: '📕' },
]

type PlatformStatus = 'idle' | 'searching' | 'done' | 'timeout' | 'error'

interface SearchPanelProps {
  onAddToMaterials: (results: SearchResult[]) => void
}

export const SearchPanel: React.FC<SearchPanelProps> = ({ onAddToMaterials }) => {
  const [query, setQuery] = useState('')
  const [selectedPlatforms, setSelectedPlatforms] = useState<Set<PlatformType>>(new Set())
  const [results, setResults] = useState<SearchResult[]>([])
  const [checked, setChecked] = useState<Set<string>>(new Set())
  const [platformStatus, setPlatformStatus] = useState<Record<string, PlatformStatus>>({})
  const [isSearching, setIsSearching] = useState(false)
  const [error, setError] = useState('')
  const abortRef = useRef<AbortController | null>(null)
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  const togglePlatform = (p: PlatformType) => {
    setSelectedPlatforms(prev => {
      const next = new Set(prev)
      next.has(p) ? next.delete(p) : next.add(p)
      return next
    })
  }

  const handleSearch = useCallback(async () => {
    if (!query.trim() || isSearching) return
    setError('')
    setResults([])
    setChecked(new Set())
    setPlatformStatus({})
    setIsSearching(true)

    // 取消上一次搜索
    abortRef.current?.abort()
    abortRef.current = new AbortController()

    // 15s 超时
    if (timeoutRef.current) clearTimeout(timeoutRef.current)
    timeoutRef.current = setTimeout(() => {
      abortRef.current?.abort()
      setIsSearching(false)
      setError('搜索超时，请重试')
    }, 15000)

    const platforms = selectedPlatforms.size > 0 ? Array.from(selectedPlatforms) : undefined

    try {
      const res = await fetch('/api/search/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query, platforms }),
        signal: abortRef.current.signal,
      })

      if (!res.ok || !res.body) {
        throw new Error(`Search failed: ${res.status}`)
      }

      const reader = res.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() ?? ''

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue
          try {
            const evt = JSON.parse(line.slice(6))
            if (evt.type === 'platform_start') {
              setPlatformStatus(s => ({ ...s, [evt.platform]: 'searching' }))
            } else if (evt.type === 'platform_done') {
              setPlatformStatus(s => ({ ...s, [evt.platform]: 'done' }))
            } else if (evt.type === 'platform_timeout') {
              setPlatformStatus(s => ({ ...s, [evt.platform]: 'timeout' }))
            } else if (evt.type === 'platform_error') {
              setPlatformStatus(s => ({ ...s, [evt.platform]: 'error' }))
            } else if (evt.type === 'results') {
              setResults(evt.items.map((item: any) => ({
                id: item.id,
                title: item.title,
                url: item.url,
                platform: item.platform as PlatformType,
                description: item.description,
                qualityScore: item.qualityScore,
                recommendationReason: item.recommendationReason,
              })))
            } else if (evt.type === 'done') {
              if (timeoutRef.current) clearTimeout(timeoutRef.current)
              setIsSearching(false)
            }
          } catch { /* 忽略解析错误 */ }
        }
      }
    } catch (err: any) {
      if (err.name !== 'AbortError') {
        setError('搜索失败，请检查网络或重试')
      }
    } finally {
      if (timeoutRef.current) clearTimeout(timeoutRef.current)
      setIsSearching(false)
    }
  }, [query, selectedPlatforms, isSearching])

  // 清理
  useEffect(() => () => {
    abortRef.current?.abort()
    if (timeoutRef.current) clearTimeout(timeoutRef.current)
  }, [])

  const toggleCheck = (id: string) => {
    setChecked(prev => {
      const next = new Set(prev)
      next.has(id) ? next.delete(id) : next.add(id)
      return next
    })
  }

  const handleAdd = () => {
    const selected = results.filter(r => checked.has(r.id))
    onAddToMaterials(selected)
    setResults([])
    setChecked(new Set())
    setQuery('')
  }

  const activePlatforms = PLATFORMS.filter(p => platformStatus[p.key])

  return (
    <div className="flex flex-col gap-3">
      {/* 搜索输入 */}
      <div className="flex gap-1.5">
        <input
          value={query}
          onChange={e => setQuery(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && handleSearch()}
          placeholder="搜索学习资源..."
          className="flex-1 h-9 rounded-lg border border-[#DADCE0] px-3 text-sm focus:outline-none focus:ring-2 focus:ring-[#1A73E8]/30 focus:border-[#1A73E8] dark:bg-dark-surface dark:border-dark-border dark:text-dark-text"
          aria-label="搜索关键词"
        />
        <button
          onClick={handleSearch}
          disabled={isSearching || !query.trim()}
          aria-label="搜索资源"
          className="h-9 px-3 bg-[#1A73E8] text-white rounded-lg text-sm hover:bg-[#1557B0] disabled:opacity-40 transition-colors duration-150"
        >
          {isSearching ? '…' : '🔍'}
        </button>
      </div>

      {/* 平台选择 */}
      <div className="flex flex-wrap gap-1.5">
        {PLATFORMS.map(p => (
          <button
            key={p.key}
            onClick={() => togglePlatform(p.key)}
            aria-pressed={selectedPlatforms.has(p.key)}
            className={`flex items-center gap-1 h-7 px-2.5 rounded-full text-xs font-medium transition-all duration-150 ${
              selectedPlatforms.has(p.key)
                ? 'bg-[#E8F0FE] text-[#1A73E8] border border-[#1A73E8]'
                : 'bg-[#F1F3F4] text-[#5F6368] border border-transparent hover:border-[#DADCE0]'
            }`}
          >
            <span>{p.icon}</span>
            <span>{p.label}</span>
          </button>
        ))}
      </div>

      {/* 平台搜索进度 */}
      {activePlatforms.length > 0 && (
        <div className="flex flex-col gap-1">
          {activePlatforms.map(p => {
            const status = platformStatus[p.key]
            return (
              <div key={p.key} className="flex items-center gap-2 text-xs text-[#5F6368]">
                <span>{p.icon}</span>
                <span className="flex-1">{p.label}</span>
                {status === 'searching' && (
                  <span className="flex gap-0.5">
                    <span className="w-1.5 h-1.5 rounded-full bg-[#1A73E8] animate-bounce [animation-delay:0ms]" />
                    <span className="w-1.5 h-1.5 rounded-full bg-[#1A73E8] animate-bounce [animation-delay:100ms]" />
                    <span className="w-1.5 h-1.5 rounded-full bg-[#1A73E8] animate-bounce [animation-delay:200ms]" />
                  </span>
                )}
                {status === 'done' && <span className="text-green-500">✓</span>}
                {status === 'timeout' && <span className="text-orange-400">搜索超时</span>}
                {status === 'error' && <span className="text-red-400">失败</span>}
              </div>
            )
          })}
        </div>
      )}

      {error && <p className="text-xs text-red-500">{error}</p>}

      {/* 搜索结果 */}
      {results.length > 0 && (
        <>
          <p className="text-xs font-medium text-[#5F6368] uppercase tracking-wide">
            搜索结果（{results.length} 条）
          </p>
          <div className="flex flex-col gap-2">
            {results.map(r => (
              <SearchResultItem
                key={r.id}
                result={r}
                checked={checked.has(r.id)}
                onToggle={() => toggleCheck(r.id)}
              />
            ))}
          </div>
          {checked.size > 0 && (
            <Button variant="primary" className="w-full mt-1" onClick={handleAdd}>
              加入学习材料（{checked.size} 项已选）
            </Button>
          )}
        </>
      )}

      {results.length === 0 && !isSearching && !error && (
        <p className="text-xs text-[#9AA0A6] text-center py-4">
          输入关键词后按 Enter 或点击搜索
        </p>
      )}
    </div>
  )
}
