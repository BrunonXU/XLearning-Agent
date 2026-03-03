import React from 'react'
import type { SearchResult, PlatformType } from '../../types'

const PLATFORM_ICONS: Record<PlatformType, string> = {
  bilibili: '📺',
  youtube: '🎬',
  google: '🌐',
  github: '🔗',
  xiaohongshu: '📕',
  other: '🌐',
}

interface SearchResultItemProps {
  result: SearchResult
  checked: boolean
  onToggle: () => void
}

export const SearchResultItem: React.FC<SearchResultItemProps> = ({ result, checked, onToggle }) => {
  const score = (result.qualityScore * 10).toFixed(1)
  const desc = result.description.length > 100
    ? result.description.slice(0, 100) + '…'
    : result.description

  return (
    <div
      className={`rounded-lg border p-3 transition-all duration-150 cursor-pointer ${
        checked
          ? 'border-primary bg-primary-light'
          : 'border-border hover:border-primary/50 hover:bg-surface-tertiary'
      }`}
      onClick={onToggle}
    >
      <div className="flex items-start gap-2">
        <input
          type="checkbox"
          checked={checked}
          onChange={onToggle}
          onClick={e => e.stopPropagation()}
          className="mt-0.5 accent-primary flex-shrink-0"
          aria-label={`选择 ${result.title}`}
        />
        <div className="flex-1 min-w-0">
          {/* 标题行 */}
          <div className="flex items-center gap-1 mb-1">
            <span className="text-sm" aria-hidden="true">{PLATFORM_ICONS[result.platform]}</span>
            <a
              href={result.url}
              target="_blank"
              rel="noopener noreferrer"
              onClick={e => e.stopPropagation()}
              className="text-sm font-medium text-text-primary hover:text-primary hover:underline truncate"
            >
              {result.title}
            </a>
          </div>
          {/* 摘要 */}
          <p className="text-xs text-text-secondary line-clamp-2 mb-1">{desc}</p>
          {/* 评分 */}
          <span className="text-accent font-semibold text-sm">⭐ {score}/10</span>
          {/* 推荐理由 */}
          <p className="text-xs text-text-secondary mt-0.5 line-clamp-2">
            💡 {result.recommendationReason}
          </p>
        </div>
      </div>
    </div>
  )
}
