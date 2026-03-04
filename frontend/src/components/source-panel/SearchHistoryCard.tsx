/**
 * SearchHistoryCard — 搜索历史记录卡片
 *
 * 折叠态：搜索关键词 + 平台图标列表 + 结果数量
 * 展开态：完整 top 10 结果列表（可勾选）+ 加入学习材料按钮 + 搜索时间 + 收起按钮
 * 点击切换展开/收起
 *
 * 需求: 3.4, 3.5, 3.6
 */
import React, { useState } from 'react'
import { Button } from '../ui/Button'
import type { SearchHistoryEntry, SearchResult, PlatformType } from '../../types'

const PLATFORM_ICONS: Record<PlatformType, string> = {
  bilibili: '📺',
  youtube: '🎬',
  google: '🌐',
  github: '🔗',
  xiaohongshu: '📕',
  other: '🌐',
}

const ALL_KNOWN_PLATFORMS: PlatformType[] = ['bilibili', 'youtube', 'google', 'github', 'xiaohongshu']

export interface SearchHistoryCardProps {
  entry: SearchHistoryEntry
  isExpanded: boolean
  onToggle: () => void
  onAddToMaterials?: (results: SearchResult[]) => void
}

/** Format ISO date to Chinese style: "3月4日 14:32" */
export function formatSearchTime(isoString: string): string {
  const d = new Date(isoString)
  if (isNaN(d.getTime())) return ''
  const month = d.getMonth() + 1
  const day = d.getDate()
  const hours = String(d.getHours()).padStart(2, '0')
  const minutes = String(d.getMinutes()).padStart(2, '0')
  return `${month}月${day}日 ${hours}:${minutes}`
}

/** Build platform display: icons list or "混合搜索" if all platforms */
export function getPlatformDisplay(platforms: PlatformType[]): string {
  const isAll = ALL_KNOWN_PLATFORMS.every(p => platforms.includes(p))
  if (isAll) return '混合搜索'
  return platforms.map(p => PLATFORM_ICONS[p] ?? '🌐').join('')
}

export const SearchHistoryCard: React.FC<SearchHistoryCardProps> = ({
  entry,
  isExpanded,
  onToggle,
  onAddToMaterials,
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
    if (!onAddToMaterials) return
    const selected = entry.results.filter(r => checked.has(r.id))
    onAddToMaterials(selected)
    setChecked(new Set())
  }

  if (isExpanded) {
    return (
      <div className="rounded-lg border border-[#DADCE0] bg-white dark:bg-dark-surface dark:border-dark-border">
        {/* Expanded header */}
        <div className="flex items-center justify-between px-3 py-2 border-b border-[#DADCE0] dark:border-dark-border">
          <span className="text-xs text-[#5F6368] dark:text-dark-text-secondary">
            {formatSearchTime(entry.searchedAt)}
          </span>
          <button
            onClick={onToggle}
            className="text-xs text-[#1A73E8] hover:text-[#1557B0] font-medium transition-colors duration-150"
            aria-label="收起搜索历史"
          >
            收起 ▲
          </button>
        </div>

        {/* Search keyword */}
        <div className="px-3 py-2">
          <p className="text-sm font-medium text-[#202124] dark:text-dark-text truncate">
            🔍 {entry.query}
          </p>
        </div>

        {/* Result list with checkboxes */}
        <div className="flex flex-col gap-1.5 px-3 pb-3">
          {entry.results.map((r) => {
            const score = (r.qualityScore * 10).toFixed(1)
            const desc =
              r.description.length > 100
                ? r.description.slice(0, 100) + '…'
                : r.description
            const isChecked = checked.has(r.id)
            return (
              <div
                key={r.id}
                onClick={() => toggleCheck(r.id)}
                className={`rounded-lg border p-2.5 cursor-pointer transition-all duration-150 ${
                  isChecked
                    ? 'border-[#1A73E8] bg-[#E8F0FE]'
                    : 'border-[#DADCE0] dark:border-dark-border hover:bg-[#F8F9FA] dark:hover:bg-dark-surface-secondary'
                }`}
              >
                <div className="flex items-start gap-2">
                  <input
                    type="checkbox"
                    checked={isChecked}
                    onChange={() => toggleCheck(r.id)}
                    onClick={e => e.stopPropagation()}
                    className="mt-0.5 accent-[#1A73E8] flex-shrink-0"
                    aria-label={`选择 ${r.title}`}
                  />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-1 mb-0.5">
                      <span className="text-sm" aria-hidden="true">
                        {PLATFORM_ICONS[r.platform] ?? '🌐'}
                      </span>
                      <a
                        href={r.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        onClick={e => e.stopPropagation()}
                        className="text-sm font-medium text-[#202124] dark:text-dark-text hover:text-[#1A73E8] hover:underline truncate"
                      >
                        {r.title}
                      </a>
                    </div>
                    <p className="text-xs text-[#5F6368] dark:text-dark-text-secondary line-clamp-2 mb-0.5">
                      {desc}
                    </p>
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-semibold text-[#F9AB00]">
                        ⭐ {score}/10
                      </span>
                      {r.recommendationReason && (
                        <span className="text-xs text-[#5F6368] dark:text-dark-text-secondary truncate">
                          💡 {r.recommendationReason}
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            )
          })}
        </div>

        {/* Add to materials button */}
        {checked.size > 0 && onAddToMaterials && (
          <div className="px-3 pb-3">
            <Button variant="primary" className="w-full" onClick={handleAdd}>
              加入学习材料（{checked.size} 项已选）
            </Button>
          </div>
        )}
      </div>
    )
  }

  // Collapsed state
  return (
    <button
      onClick={onToggle}
      className="w-full flex items-center gap-2 rounded-lg border border-[#DADCE0] dark:border-dark-border bg-white dark:bg-dark-surface px-3 py-2 hover:bg-[#F8F9FA] dark:hover:bg-dark-surface-secondary transition-colors duration-150 text-left"
      aria-label={`展开搜索历史: ${entry.query}`}
    >
      <span className="text-sm font-medium text-[#202124] dark:text-dark-text truncate flex-1">
        {entry.query}
      </span>
      <span className="text-xs text-[#5F6368] dark:text-dark-text-secondary whitespace-nowrap">
        {getPlatformDisplay(entry.platforms)}
      </span>
      <span className="text-xs text-[#9AA0A6] whitespace-nowrap">
        {entry.resultCount} 条结果
      </span>
    </button>
  )
}
