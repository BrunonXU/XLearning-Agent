import React, { useState, useRef, useEffect } from 'react'
import { createPortal } from 'react-dom'
import type { SearchResult, PlatformType } from '../../types'

const PLATFORM_ICONS: Record<PlatformType, string> = {
  bilibili: '📺',
  youtube: '🎬',
  google: '🌐',
  github: '🔗',
  xiaohongshu: '📕',
  other: '🌐',
}

function formatNum(n: any): string {
  const num = Number(n)
  if (isNaN(num)) return String(n)
  if (num >= 10000) return (num / 10000).toFixed(1) + '万'
  return String(num)
}

interface SearchResultItemProps {
  result: SearchResult
  checked: boolean
  onToggle: () => void
  onViewDetail?: (result: SearchResult) => void
}

export const SearchResultItem: React.FC<SearchResultItemProps> = ({ result, checked, onToggle, onViewDetail }) => {
  const score = (result.qualityScore * 10).toFixed(1)
  const desc = result.description.length > 100
    ? result.description.slice(0, 100) + '…'
    : result.description

  const [hovered, setHovered] = useState(false)
  const [popupPos, setPopupPos] = useState<{ top: number; left: number } | null>(null)
  const [imgIdx, setImgIdx] = useState(0)
  const cardRef = useRef<HTMLDivElement>(null)
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  const hasDetail = !!(result.contentSummary || result.imageUrls?.length || result.topComments?.length || result.engagementMetrics)

  const showPopup = () => {
    if (!hasDetail || !cardRef.current) return
    const rect = cardRef.current.getBoundingClientRect()
    const popupWidth = 340
    const spaceRight = window.innerWidth - rect.right
    const left = spaceRight > popupWidth + 16 ? rect.right + 8 : rect.left - popupWidth - 8
    const top = Math.max(8, Math.min(rect.top, window.innerHeight - 460))
    setPopupPos({ top, left })
    setImgIdx(0)
    setHovered(true)
  }

  const hidePopup = () => {
    if (timerRef.current) clearTimeout(timerRef.current)
    setHovered(false)
    setPopupPos(null)
  }

  const handleMouseEnter = () => {
    if (timerRef.current) clearTimeout(timerRef.current)
    timerRef.current = setTimeout(showPopup, 300)
  }

  const handleMouseLeave = () => {
    if (timerRef.current) clearTimeout(timerRef.current)
    timerRef.current = setTimeout(hidePopup, 150)
  }

  useEffect(() => () => { if (timerRef.current) clearTimeout(timerRef.current) }, [])

  const metrics = result.engagementMetrics ?? {}
  const coreMetrics: { icon: string; label: string; value: number }[] = []
  if (metrics.likes != null) coreMetrics.push({ icon: '👍', label: '点赞', value: metrics.likes })
  if (metrics.collected != null) coreMetrics.push({ icon: '⭐', label: '收藏', value: metrics.collected })
  if (metrics.comments_count != null || metrics.comments != null)
    coreMetrics.push({ icon: '💬', label: '评论', value: metrics.comments_count ?? metrics.comments ?? 0 })

  const images = result.imageUrls ?? []

  return (
    <>
      <div
        ref={cardRef}
        onMouseEnter={handleMouseEnter}
        onMouseLeave={handleMouseLeave}
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
            <p className="text-xs text-text-secondary line-clamp-2 mb-1">{desc}</p>
            <span className="text-accent font-semibold text-sm">⭐ {score}/10</span>
            <p className="text-xs text-text-secondary mt-0.5 line-clamp-2">
              💡 {result.recommendationReason}
            </p>
          </div>
        </div>
      </div>

      {/* Hover 预览浮窗 */}
      {hovered && popupPos && hasDetail && createPortal(
        <div
          onMouseEnter={() => { if (timerRef.current) clearTimeout(timerRef.current) }}
          onMouseLeave={handleMouseLeave}
          style={{ top: popupPos.top, left: popupPos.left }}
          className="fixed z-[9999] w-[340px] max-h-[460px] overflow-y-auto rounded-xl border border-[#E0E0E0] bg-white dark:bg-dark-surface shadow-2xl animate-in fade-in zoom-in-95 duration-150"
        >
          {/* 图片轮播 — 大图，撑满宽度 */}
          {images.length > 0 && (
            <div className="relative w-full bg-[#F8F9FA]">
              <a href={images[imgIdx]} target="_blank" rel="noopener noreferrer" onClick={e => e.stopPropagation()}>
                <img
                  src={images[imgIdx]}
                  alt={`图片 ${imgIdx + 1}`}
                  className="w-full max-h-[200px] object-contain cursor-pointer"
                  loading="lazy"
                />
              </a>
              {images.length > 1 && (
                <>
                  <button
                    onClick={e => { e.stopPropagation(); setImgIdx(i => (i - 1 + images.length) % images.length) }}
                    className="absolute left-1.5 top-1/2 -translate-y-1/2 w-7 h-7 rounded-full bg-black/40 text-white flex items-center justify-center hover:bg-black/60 transition-colors text-sm"
                    aria-label="上一张"
                  >‹</button>
                  <button
                    onClick={e => { e.stopPropagation(); setImgIdx(i => (i + 1) % images.length) }}
                    className="absolute right-1.5 top-1/2 -translate-y-1/2 w-7 h-7 rounded-full bg-black/40 text-white flex items-center justify-center hover:bg-black/60 transition-colors text-sm"
                    aria-label="下一张"
                  >›</button>
                  <span className="absolute bottom-1.5 right-2 text-[10px] text-white bg-black/50 px-1.5 py-0.5 rounded-full">
                    {imgIdx + 1}/{images.length}
                  </span>
                </>
              )}
            </div>
          )}

          <div className="p-3.5 space-y-3">
            {/* 互动指标 badges */}
            {coreMetrics.length > 0 && (
              <div className="flex items-center gap-2 flex-wrap">
                {coreMetrics.map(m => (
                  <span key={m.label} className="inline-flex items-center gap-1 text-xs px-2 py-1 rounded-full bg-[#F1F3F4] text-[#5F6368]">
                    <span>{m.icon}</span>
                    <span className="font-medium">{formatNum(m.value)}</span>
                  </span>
                ))}
              </div>
            )}

            {/* 完整描述 */}
            {result.description && (
              <>
                <p className="text-[13px] text-[#3C4043] dark:text-dark-text leading-[1.6]">
                  {result.description}
                </p>
                <div className="border-t border-[#EEEEEE] dark:border-dark-border" />
              </>
            )}

            {/* 内容摘要 */}
            {result.contentSummary && (
              <>
                <div>
                  <p className="text-xs font-medium text-[#202124] dark:text-dark-text mb-1.5">📋 内容摘要</p>
                  <p className="text-[13px] text-[#3C4043] leading-[1.7] bg-[#F8F9FA] dark:bg-dark-bg rounded-lg px-3 py-2 whitespace-pre-line">
                    {result.contentSummary}
                  </p>
                </div>
                <div className="border-t border-[#EEEEEE] dark:border-dark-border" />
              </>
            )}

            {/* 高赞评论 */}
            {result.topComments && result.topComments.length > 0 && (
              <>
                <div>
                  <p className="text-xs font-medium text-[#202124] dark:text-dark-text mb-1.5">🔥 高赞评论</p>
                  <div className="space-y-1.5">
                    {result.topComments.slice(0, 3).map((c, i) => (
                      <p key={i} className="text-[13px] text-[#5F6368] leading-[1.6] pl-2.5 border-l-2 border-[#D97757]/40 line-clamp-2">
                        {c}
                      </p>
                    ))}
                  </div>
                </div>
              </>
            )}

            {/* 查看完整详情 */}
            {onViewDetail && (
              <button
                onClick={e => { e.stopPropagation(); hidePopup(); onViewDetail(result) }}
                className="w-full text-center text-xs text-[#D97757] hover:text-[#C06144] font-medium py-1.5 rounded-lg hover:bg-[#FDF5F0] transition-colors"
              >
                查看完整详情 →
              </button>
            )}
          </div>
        </div>,
        document.body
      )}
    </>
  )
}
