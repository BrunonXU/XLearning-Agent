/**
 * SearchPanel — 资源搜索面板
 *
 * 功能：
 * - 关键词输入 + 平台多选
 * - 调用 /api/search/stream SSE 端点，按 stage 字段显示中文进度
 * - 搜索超时（>60s）显示"搜索超时"
 * - 搜索完成后保存历史记录
 * - 新搜索时取消当前进行中的搜索
 * - 结果按 qualityScore 降序统一排序，不按平台分组
 * - 勾选结果 + "加入学习材料"按钮
 */
import React, { useState, useRef, useCallback, useEffect } from 'react'
import { SearchResultItem } from './SearchResultItem'
import { SearchHistoryCard } from './SearchHistoryCard'
import { Button } from '../ui/Button'
import { useSearchStore } from '../../store/searchStore'
import type { SearchResult, PlatformType, SearchStage } from '../../types'

const PLATFORMS: { key: PlatformType; label: string; icon: string }[] = [
  { key: 'bilibili', label: 'B站', icon: '📺' },
  { key: 'youtube', label: 'YouTube', icon: '🎬' },
  { key: 'google', label: 'Google', icon: '🌐' },
  { key: 'github', label: 'GitHub', icon: '🔗' },
  { key: 'xiaohongshu', label: '小红书', icon: '📕' },
]

/** 根据 SSE stage 字段生成中文状态文案 */
function stageToMessage(stage: SearchStage, evt?: any): string {
  switch (stage) {
    case 'searching':
      return evt?.message || '正在搜索...'
    case 'filtering':
      return evt?.message || `已获取 ${evt?.total ?? 0} 条，正在初筛...`
    case 'extracting': {
      const completed = evt?.completed ?? 0
      const total = evt?.total ?? 0
      return evt?.message || `正在提取详情（${completed}/${total}）...`
    }
    case 'evaluating':
      return 'AI 正在评估内容质量...'
    case 'error':
      return evt?.message || '搜索出错'
    default:
      return ''
  }
}

interface SearchPanelProps {
  planId?: string
  onAddToMaterials: (results: SearchResult[]) => void
}

export const SearchPanel: React.FC<SearchPanelProps> = ({ planId = '', onAddToMaterials }) => {
  const [query, setQuery] = useState('')
  const [selectedPlatforms, setSelectedPlatforms] = useState<Set<PlatformType>>(new Set())
  const [results, setResults] = useState<SearchResult[]>([])
  const [checked, setChecked] = useState<Set<string>>(new Set())
  const [searchStage, setSearchStage] = useState<SearchStage>('idle')
  const [stageMessage, setStageMessage] = useState('')
  const [isSearching, setIsSearching] = useState(false)
  const [error, setError] = useState('')
  const [expandedHistoryId, setExpandedHistoryId] = useState<string | null>(null)
  const abortRef = useRef<AbortController | null>(null)
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const history = useSearchStore(s => s.history)

  const togglePlatform = (p: PlatformType) => {
    setSelectedPlatforms(prev => {
      const next = new Set(prev)
      next.has(p) ? next.delete(p) : next.add(p)
      return next
    })
  }

  const handleSearch = useCallback(async () => {
    if (!query.trim()) return

    // 取消当前进行中的搜索（允许新搜索覆盖旧搜索）
    abortRef.current?.abort()
    if (timeoutRef.current) clearTimeout(timeoutRef.current)

    setError('')
    setResults([])
    setChecked(new Set())
    setSearchStage('idle')
    setStageMessage('')
    setIsSearching(true)

    abortRef.current = new AbortController()

    // 60s 超时
    timeoutRef.current = setTimeout(() => {
      abortRef.current?.abort()
      setIsSearching(false)
      setSearchStage('error')
      setError('搜索超时，请重试')
    }, 60000)

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
            const stage = evt.stage as SearchStage | undefined

            if (stage === 'searching') {
              setSearchStage('searching')
              setStageMessage(stageToMessage('searching', evt))
            } else if (stage === 'filtering') {
              setSearchStage('filtering')
              setStageMessage(stageToMessage('filtering', evt))
            } else if (stage === 'extracting') {
              setSearchStage('extracting')
              setStageMessage(stageToMessage('extracting', evt))
            } else if (stage === 'evaluating') {
              setSearchStage('evaluating')
              setStageMessage(stageToMessage('evaluating', evt))
            } else if (stage === 'done') {
              if (timeoutRef.current) clearTimeout(timeoutRef.current)
              setSearchStage('done')
              setStageMessage('')

              // Parse results and sort by qualityScore descending
              const items: SearchResult[] = (evt.results ?? [])
                .map((item: any) => ({
                  id: item.id,
                  title: item.title,
                  url: item.url,
                  platform: item.platform as PlatformType,
                  description: item.description ?? '',
                  qualityScore: item.qualityScore ?? 0,
                  recommendationReason: item.recommendationReason ?? '',
                  contentSummary: item.contentSummary,
                  commentSummary: item.commentSummary,
                  engagementMetrics: item.engagementMetrics,
                  imageUrls: item.imageUrls,
                  topComments: item.topComments,
                }))
                .sort((a: SearchResult, b: SearchResult) => b.qualityScore - a.qualityScore)

              setResults(items)
              setIsSearching(false)

              // Save search history
              useSearchStore.getState().addEntry(planId, {
                id: `search-${Date.now()}`,
                query: query.trim(),
                platforms: platforms ?? PLATFORMS.map(p => p.key),
                results: items,
                resultCount: items.length,
                searchedAt: new Date().toISOString(),
              })
            } else if (stage === 'error') {
              if (timeoutRef.current) clearTimeout(timeoutRef.current)
              setSearchStage('error')
              setError(evt.message || '搜索出错')
              setIsSearching(false)
            }
          } catch { /* 忽略解析错误 */ }
        }
      }
    } catch (err: any) {
      if (err.name !== 'AbortError') {
        setError('搜索失败，请检查网络或重试')
        setSearchStage('error')
      }
    } finally {
      if (timeoutRef.current) clearTimeout(timeoutRef.current)
      setIsSearching(false)
    }
  }, [query, selectedPlatforms])

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

  const isActive = isSearching && searchStage !== 'idle' && searchStage !== 'done' && searchStage !== 'error'

  return (
    <div className="flex flex-col gap-3">
      {/* 搜索输入 */}
      <div className="flex gap-2">
        <input
          value={query}
          onChange={e => setQuery(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && handleSearch()}
          placeholder="搜索学习资源..."
          className="flex-1 h-10 rounded-lg border border-[#DADCE0] px-3 text-sm focus:outline-none focus:ring-2 focus:ring-[#1A73E8]/30 focus:border-[#1A73E8] dark:bg-dark-surface dark:border-dark-border dark:text-dark-text"
          aria-label="搜索关键词"
        />
        <button
          onClick={handleSearch}
          disabled={!query.trim()}
          aria-label="搜索资源"
          className="h-10 px-4 bg-[#1A73E8] text-white rounded-lg text-sm hover:bg-[#1557B0] disabled:opacity-40 transition-colors duration-150"
        >
          {isSearching ? '…' : '🔍'}
        </button>
      </div>

      {/* 平台选择 */}
      <div className="flex flex-wrap gap-2">
        {PLATFORMS.map(p => (
          <button
            key={p.key}
            onClick={() => togglePlatform(p.key)}
            aria-pressed={selectedPlatforms.has(p.key)}
            className={`flex items-center gap-1.5 h-8 px-3 rounded-full text-sm font-medium transition-all duration-150 ${
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

      {/* 搜索阶段进度 */}
      {isActive && stageMessage && (
        <div className="flex items-center gap-2 text-xs text-[#5F6368] py-1">
          <span className="flex gap-0.5">
            <span className="w-1.5 h-1.5 rounded-full bg-[#1A73E8] animate-bounce [animation-delay:0ms]" />
            <span className="w-1.5 h-1.5 rounded-full bg-[#1A73E8] animate-bounce [animation-delay:100ms]" />
            <span className="w-1.5 h-1.5 rounded-full bg-[#1A73E8] animate-bounce [animation-delay:200ms]" />
          </span>
          <span>{stageMessage}</span>
        </div>
      )}

      {error && <p className="text-xs text-red-500">{error}</p>}

      {/* 搜索结果 — 统一排序，不按平台分组 */}
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

      {/* 搜索历史 */}
      {history.length > 0 && results.length === 0 && !isSearching && (
        <div className="flex flex-col gap-2 mt-2">
          <p className="text-xs font-medium text-[#5F6368] uppercase tracking-wide">
            搜索历史
          </p>
          {history.map(entry => (
            <SearchHistoryCard
              key={entry.id}
              entry={entry}
              isExpanded={expandedHistoryId === entry.id}
              onToggle={() =>
                setExpandedHistoryId(prev => prev === entry.id ? null : entry.id)
              }
              onAddToMaterials={onAddToMaterials}
            />
          ))}
        </div>
      )}
    </div>
  )
}
