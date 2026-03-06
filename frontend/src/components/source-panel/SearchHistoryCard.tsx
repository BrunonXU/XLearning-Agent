/**
 * SearchHistoryCard
 *
 * 需求: 3.4, 3.5, 3.6, 4.5
 */
import React, { useState } from 'react'
import { SearchResultItem } from './SearchResultItem'
import type { SearchHistoryEntry, SearchResult, PlatformType } from '../../types'

const PLATFORM_ICONS: Record<PlatformType, string> = {
  bilibili: '',
  youtube: '',
  google: '',
  github: '',
  xiaohongshu: '',
  other: '',
}

const ALL_KNOWN_PLATFORMS: PlatformType[] = ['bilibili', 'youtube', 'google', 'github', 'xiaohongshu']

export interface SearchHistoryCardProps {
  entry: SearchHistoryEntry
  isExpanded: boolean
  onToggle: () => void
  onAddToMaterials?: (results: SearchResult[]) => void
  onRemove?: (id: string) => void
  onViewDetail?: (result: SearchResult) => void
}

export function formatSearchTime(isoString: string): string {
  const d = new Date(isoString)
  if (isNaN(d.getTime())) return ''
  const month = d.getMonth() + 1
  const day = d.getDate()
  const hours = String(d.getHours()).padStart(2, '0')
  const minutes = String(d.getMinutes()).padStart(2, '0')
  return `${month}月${day}日 ${hours}:${minutes}`
}

export function getPlatformDisplay(platforms: PlatformType[]): string {
  const isAll = ALL_KNOWN_PLATFORMS.every(p => platforms.includes(p))
  if (isAll) return '混合搜索'
  return platforms.map(p => PLATFORM_ICONS[p] ?? '').join('')
}

export const SearchHistoryCard: React.FC<SearchHistoryCardProps> = ({
  entry, isExpanded, onToggle, onAddToMaterials, onRemove, onViewDetail,
}) => {
  const [checked, setChecked] = useState<Set<string>>(new Set())

  const toggleCheck = (id: string) => {
    setChecked(prev => {
      const next = new Set(prev)
      next.has(id) ? next.delete(id) : next.add(id)
      return next
    })
  }

  const handleAdd = () => {
    const selected = entry.results.filter(r => checked.has(r.id))
    onAddToMaterials?.(selected)
    setChecked(new Set())
  }

  const deleteBtn = onRemove ? (
    <button
      onClick={(e) => { e.stopPropagation(); if (window.confirm(`确定删除搜索记录「${entry.query}」吗？`)) onRemove(entry.id) }}
      className="flex-shrink-0 w-8 h-8 flex items-center justify-center text-[#999] hover:text-red-500 hover:bg-red-50 rounded-lg transition-colors mr-1"
      aria-label="删除搜索记录"
      title="删除"
    >
      <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
    </button>
  ) : null

  if (entry.status === 'searching') {
    return (
      <div className="rounded-xl border border-[#E5E5E5] overflow-hidden">
        <div className="flex items-center">
          <div className="flex-1 flex items-center justify-between px-3 py-2 text-left min-w-0">
            <span className="text-sm font-medium text-[#1A1A18] truncate">{entry.query}</span>
            <span className="text-xs text-[#8C8C87] ml-2 flex-shrink-0 inline-flex items-center gap-1">
              <span className="inline-flex gap-0.5" data-testid="loading-dots">
                <span className="animate-bounce inline-block w-1.5 h-1.5 rounded-full bg-[#D97757]" style={{ animationDelay: '0ms' }} />
                <span className="animate-bounce inline-block w-1.5 h-1.5 rounded-full bg-[#D97757]" style={{ animationDelay: '150ms' }} />
                <span className="animate-bounce inline-block w-1.5 h-1.5 rounded-full bg-[#D97757]" style={{ animationDelay: '300ms' }} />
              </span>
              <span>搜索中...</span>
            </span>
          </div>
          {deleteBtn}
        </div>
      </div>
    )
  }

  if (entry.status === 'error') {
    return (
      <div className="rounded-xl border border-[#E5E5E5] overflow-hidden">
        <div className="flex items-center">
          <button
            className="flex-1 flex items-center justify-between px-3 py-2 text-left hover:bg-[#F0EDE8] transition-colors min-w-0"
            onClick={onToggle}
          >
            <span className="text-sm font-medium text-[#1A1A18] truncate">{entry.query}</span>
            <span className="text-xs text-red-500 ml-2 flex-shrink-0">搜索失败</span>
          </button>
          {deleteBtn}
        </div>
      </div>
    )
  }

  return (
    <div className="rounded-xl border border-[#E5E5E5] overflow-hidden">
      <div className="flex items-center">
        <button
          className="flex-1 flex items-center justify-between px-3 py-2 text-left hover:bg-[#F0EDE8] transition-colors min-w-0"
          onClick={onToggle}
        >
          <span className="text-sm font-medium text-[#1A1A18] truncate">{entry.query}</span>
          <span className="text-xs text-[#8C8C87] ml-2 flex-shrink-0">
            {getPlatformDisplay(entry.platforms)} &middot; {entry.resultCount} 条
          </span>
        </button>
        {deleteBtn}
      </div>
      {isExpanded && entry.results.length > 0 && (
        <div className="px-3 pb-3 flex flex-col gap-2 border-t border-[#F0EDE8] pt-2">
          {entry.results.slice(0, 10).map(r => (
            <SearchResultItem
              key={r.id}
              result={r}
              checked={checked.has(r.id)}
              onToggle={() => toggleCheck(r.id)}
              onViewDetail={onViewDetail}
            />
          ))}
          {checked.size > 0 && (
            <button
              onClick={handleAdd}
              className="mt-1 w-full bg-[#D97757] text-white text-xs rounded-lg py-1.5 hover:bg-[#C06144] transition-colors"
            >
              加入学习材料（{checked.size} 项已选）
            </button>
          )}
          <p className="text-xs text-[#B0B5BA] mt-1">{formatSearchTime(entry.searchedAt)}</p>
        </div>
      )}
    </div>
  )
}