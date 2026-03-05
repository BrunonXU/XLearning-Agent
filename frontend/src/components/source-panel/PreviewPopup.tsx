/**
 * PreviewPopup — 外部资源预览浮窗
 *
 * 功能：
 * - 展示搜索结果的完整详情：标题、URL、平台标识、AI 摘要、评论结论、
 *   图片翻页轮播、高赞评论、评分、推荐理由
 * - 操作按钮：查看完整信息（新标签页）、刷新、关闭
 * - 键盘支持：Escape 关闭
 * - 刷新流程：骨架屏 → 成功更新 / 失败提示+重试
 * - 数据来源：searchStore.resultDetailMap，不发起额外 API 请求
 */
import React, { useState, useEffect, useCallback } from 'react'
import { Button } from '../ui/Button'
import type { SearchResult, PlatformType } from '../../types'

const PLATFORM_LABELS: Record<PlatformType, { icon: string; name: string }> = {
  bilibili: { icon: '📺', name: 'B站' },
  youtube: { icon: '🎬', name: 'YouTube' },
  google: { icon: '🌐', name: 'Google' },
  github: { icon: '🔗', name: 'GitHub' },
  xiaohongshu: { icon: '📕', name: '小红书' },
  other: { icon: '🌐', name: '其他' },
}

interface PreviewPopupProps {
  result: SearchResult
  onClose: () => void
  onRefresh: () => void
}

export const PreviewPopup: React.FC<PreviewPopupProps> = ({
  result: initialResult,
  onClose,
  onRefresh,
}) => {
  const [result, setResult] = useState<SearchResult>(initialResult)
  const [refreshing, setRefreshing] = useState(false)
  const [refreshError, setRefreshError] = useState('')
  const [imageIndex, setImageIndex] = useState(0)

  useEffect(() => { setResult(initialResult) }, [initialResult])
  useEffect(() => { setImageIndex(0) }, [initialResult])

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }
    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [onClose])

  const handleRefresh = useCallback(async () => {
    setRefreshing(true)
    setRefreshError('')
    try {
      const res = await fetch('/api/resource/refresh', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: result.url, platform: result.platform }),
      })
      if (!res.ok) throw new Error(`刷新失败 (${res.status})`)
      const data = await res.json()
      setResult((prev) => ({
        ...prev,
        contentSummary: data.contentSummary ?? prev.contentSummary,
        commentSummary: data.commentSummary ?? prev.commentSummary,
        imageUrls: data.imageUrls ?? prev.imageUrls,
        engagementMetrics: data.engagementMetrics ?? prev.engagementMetrics,
        qualityScore: data.qualityScore ?? prev.qualityScore,
        recommendationReason: data.recommendationReason ?? prev.recommendationReason,
        topComments: data.topComments ?? prev.topComments,
      }))
      onRefresh()
    } catch (err: any) {
      setRefreshError(err.message || '刷新失败，请重试')
    } finally {
      setRefreshing(false)
    }
  }, [result.url, result.platform, onRefresh])

  const platform = PLATFORM_LABELS[result.platform] ?? PLATFORM_LABELS.other
  const score = (result.qualityScore * 10).toFixed(1)
  const metrics = result.engagementMetrics ?? {}
  const images = (result.imageUrls ?? []).slice(0, 20)
  const comments = result.topComments ?? []

  // 过滤掉 author/share_count 等无意义指标，只保留核心互动数据
  const coreMetrics: { icon: string; label: string; value: number }[] = []
  if (metrics.likes != null) coreMetrics.push({ icon: '👍', label: '点赞', value: metrics.likes })
  if (metrics.collected != null) coreMetrics.push({ icon: '⭐', label: '收藏', value: metrics.collected })
  if (metrics.comments_count != null || metrics.comments != null)
    coreMetrics.push({ icon: '💬', label: '评论', value: metrics.comments_count ?? metrics.comments ?? 0 })

  return (
    <div
      className="absolute inset-0 z-50 flex flex-col bg-white dark:bg-dark-surface rounded-xl border border-[#DADCE0] dark:border-dark-border shadow-lg overflow-hidden"
      role="dialog"
      aria-label={`预览: ${result.title}`}
      aria-modal="true"
    >
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-[#DADCE0] dark:border-dark-border bg-[#F8F9FA] dark:bg-dark-surface-secondary">
        <div className="flex items-center gap-2 min-w-0">
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-[#F2DFD3] text-[#D97757]">
            <span aria-hidden="true">{platform.icon}</span>
            {platform.name}
          </span>
          <h2 className="text-base font-semibold text-[#202124] dark:text-dark-text truncate">
            {result.title}
          </h2>
        </div>
        <button
          onClick={onClose}
          aria-label="关闭预览"
          className="flex-shrink-0 w-7 h-7 flex items-center justify-center rounded-lg text-[#5F6368] hover:bg-[#E8EAED] hover:text-[#202124] transition-colors"
        >
          ✕
        </button>
      </div>

      {/* Scrollable content */}
      <div className="flex-1 overflow-y-auto px-4 py-3 space-y-4">
        {refreshing ? (
          <SkeletonContent />
        ) : (
          <>
            {/* URL */}
            <a
              href={result.url}
              target="_blank"
              rel="noopener noreferrer"
              className="block text-xs text-[#D97757] hover:underline truncate"
            >
              {result.url}
            </a>

            {/* Score + core metrics inline */}
            <div className="flex items-center gap-3 flex-wrap">
              <span className="text-[#F9AB00] font-bold text-lg">⭐ {score}<span className="text-xs text-[#5F6368] font-normal">/10</span></span>
              {coreMetrics.map(m => (
                <span key={m.label} className="inline-flex items-center gap-1 text-sm text-[#5F6368]">
                  <span>{m.icon}</span>
                  <span>{formatNumber(m.value)}</span>
                </span>
              ))}
            </div>

            {/* Recommendation reason */}
            {result.recommendationReason && (
              <p className="text-sm text-[#5F6368] leading-relaxed">
                💡 {result.recommendationReason}
              </p>
            )}

            {/* AI Content Summary → 信息整理 */}
            {result.contentSummary && (
              <section>
                <h3 className="text-sm font-medium text-[#202124] dark:text-dark-text mb-1">📋 信息整理</h3>
                <p className="text-sm text-[#5F6368] leading-relaxed bg-[#F8F9FA] dark:bg-dark-surface-secondary rounded-lg p-3 whitespace-pre-line">
                  {result.contentSummary}
                </p>
              </section>
            )}

            {/* Image carousel */}
            {images.length > 0 && (
              <section>
                <h3 className="text-sm font-medium text-[#202124] dark:text-dark-text mb-2">🖼️ 图片 ({imageIndex + 1}/{images.length})</h3>
                <div className="relative rounded-lg overflow-hidden border border-[#DADCE0] dark:border-dark-border bg-[#F8F9FA]">
                  <a href={images[imageIndex]} target="_blank" rel="noopener noreferrer">
                    <img
                      src={images[imageIndex]}
                      alt={`图片 ${imageIndex + 1}`}
                      className="w-full max-h-[400px] object-contain"
                      loading="lazy"
                    />
                  </a>
                  {images.length > 1 && (
                    <>
                      <button
                        onClick={() => setImageIndex(i => (i - 1 + images.length) % images.length)}
                        className="absolute left-2 top-1/2 -translate-y-1/2 w-8 h-8 rounded-full bg-black/40 text-white flex items-center justify-center hover:bg-black/60 transition-colors"
                        aria-label="上一张"
                      >
                        ‹
                      </button>
                      <button
                        onClick={() => setImageIndex(i => (i + 1) % images.length)}
                        className="absolute right-2 top-1/2 -translate-y-1/2 w-8 h-8 rounded-full bg-black/40 text-white flex items-center justify-center hover:bg-black/60 transition-colors"
                        aria-label="下一张"
                      >
                        ›
                      </button>
                    </>
                  )}
                </div>
              </section>
            )}

            {/* Top comments — 放在图片下面 */}
            {comments.length > 0 && (
              <section>
                <h3 className="text-sm font-medium text-[#202124] dark:text-dark-text mb-2">🔥 高赞评论</h3>
                <div className="flex flex-col gap-2">
                  {comments.map((text, idx) => (
                    <div key={idx} className="text-sm text-[#3C4043] bg-[#F8F9FA] dark:bg-dark-surface-secondary rounded-lg px-3 py-2 leading-relaxed">
                      {text}
                    </div>
                  ))}
                </div>
              </section>
            )}

            {/* Comment summary */}
            {result.commentSummary && (
              <section>
                <h3 className="text-sm font-medium text-[#202124] dark:text-dark-text mb-1">💬 评论结论</h3>
                <p className="text-sm text-[#5F6368] leading-relaxed bg-[#F8F9FA] dark:bg-dark-surface-secondary rounded-lg p-3">
                  {result.commentSummary}
                </p>
              </section>
            )}

            {/* Refresh error */}
            {refreshError && (
              <div className="flex items-center gap-2 p-3 rounded-lg bg-red-50 border border-red-200">
                <span className="text-sm text-red-600">{refreshError}</span>
                <button onClick={handleRefresh} className="text-sm text-[#D97757] hover:underline font-medium">重试</button>
              </div>
            )}
          </>
        )}
      </div>

      {/* Footer */}
      <div className="flex items-center gap-2 px-4 py-3 border-t border-[#DADCE0] dark:border-dark-border bg-[#F8F9FA] dark:bg-dark-surface-secondary">
        <Button variant="primary" size="sm" onClick={() => window.open(result.url, '_blank')}>查看完整信息</Button>
        <Button variant="secondary" size="sm" loading={refreshing} onClick={handleRefresh}>刷新</Button>
        <Button variant="ghost" size="sm" onClick={onClose}>关闭</Button>
      </div>
    </div>
  )
}

function formatNumber(n: any): string {
  const num = Number(n)
  if (isNaN(num)) return String(n)
  if (num >= 10000) return (num / 10000).toFixed(1) + '万'
  return String(num)
}

const SkeletonContent: React.FC = () => (
  <div className="space-y-4 animate-pulse" data-testid="skeleton">
    <div className="h-4 bg-[#E8EAED] rounded w-3/4" />
    <div className="flex gap-3">
      <div className="h-10 w-20 bg-[#E8EAED] rounded-lg" />
      <div className="flex-1 h-10 bg-[#E8EAED] rounded-lg" />
    </div>
    <div className="space-y-2">
      <div className="h-3 bg-[#E8EAED] rounded w-1/4" />
      <div className="h-20 bg-[#E8EAED] rounded-lg" />
    </div>
    <div className="h-48 bg-[#E8EAED] rounded-lg" />
    <div className="space-y-2">
      <div className="h-3 bg-[#E8EAED] rounded w-1/4" />
      <div className="h-12 bg-[#E8EAED] rounded-lg" />
      <div className="h-12 bg-[#E8EAED] rounded-lg" />
    </div>
  </div>
)
