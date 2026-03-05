/**
 * SearchHistoryCard
 *
 * 需求: 3.4, 3.5, 3.6, 4.5
 */
import React, { useState } from 'react'
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

export const SearchHistoryCard: React.FC<SearchHistoryCardProps> = ({ entry, isExpanded, onToggle, onAddToMaterials }) => {
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

  if (entry.status === 'searching') {
    return (
      <div className="rounded-xl border border-[#E5E5E5] overflow-hidden">
        <div className="w-full flex items-center justify-between px-3 py-2 text-left">
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
      </div>
    )
  }

  if (entry.status === 'error') {
    return (
      <div className="rounded-xl border border-[#E5E5E5] overflow-hidden">
        <button
          className="w-full flex items-center justify-between px-3 py-2 text-left hover:bg-[#F0EDE8] transition-colors"
          onClick={onToggle}
        >
          <span className="text-sm font-medium text-[#1A1A18] truncate">{entry.query}</span>
          <span className="text-xs text-red-500 ml-2 flex-shrink-0">搜索失败</span>
        </button>
      </div>
    )
  }

  return (
    <div className="rounded-xl border border-[#E5E5E5] overflow-hidden">
      <button
        className="w-full flex items-center justify-between px-3 py-2 text-left hover:bg-[#F0EDE8] transition-colors"
        onClick={onToggle}
      >
        <span className="text-sm font-medium text-[#1A1A18] truncate">{entry.query}</span>
        <span className="text-xs text-[#8C8C87] ml-2 flex-shrink-0">
          {getPlatformDisplay(entry.platforms)} &middot; {entry.resultCount} 条
        </span>
      </button>
      {isExpanded && entry.results.length > 0 && (
        <div className="px-3 pb-3 flex flex-col gap-1.5 border-t border-[#F0EDE8]">
          {entry.results.slice(0, 10).map(r => (
            <label key={r.id} className="flex items-start gap-2 pt-2 cursor-pointer">
              <input
                type="checkbox"
                checked={checked.has(r.id)}
                onChange={() => toggleCheck(r.id)}
                className="mt-0.5 accent-[#D97757]"
              />
              <span className="text-xs text-[#1A1A18] leading-snug">{r.title}</span>
            </label>
          ))}
          {checked.size > 0 && (
            <button
              onClick={handleAdd}
              className="mt-2 w-full bg-[#D97757] text-white text-xs rounded-lg py-1.5 hover:bg-[#C06144] transition-colors"
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