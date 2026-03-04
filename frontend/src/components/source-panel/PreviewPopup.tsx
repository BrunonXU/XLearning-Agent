/**
 * PreviewPopup — 外部资源预览浮窗
 *
 * 功能：
 * - 展示搜索结果的完整详情：标题、URL、平台标识、AI 摘要、评论结论、
 *   图片缩略图网格、互动指标、评分、推荐理由
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

  // Sync with prop changes
  useEffect(() => {
    setResult(initialResult)
  }, [initialResult])

  // Escape key closes popup
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
      if (!res.ok) {
        throw new Error(`刷新失败 (${res.status})`)
      }
      const data = await res.json()
      setResult((prev) => ({
        ...prev,
        contentSummary: data.contentSummary ?? prev.contentSummary,
        commentSummary: data.commentSummary ?? prev.commentSummary,
        imageUrls: data.imageUrls ?? prev.imageUrls,
        engagementMetrics: data.engagementMetrics ?? prev.engagementMetrics,
        qualityScore: data.qualityScore ?? prev.qualityScore,
        recommendationReason: data.recommendationReason ?? prev.recommendationReason,
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
  const images = (result.imageUrls ?? []).slice(0, 9)

  return (
    <div
      className="absolute inset-0 z-50 flex flex-col bg-surface rounded-xl border border-border shadow-lg overflow-hidden"
      role="dialog"
      aria-label={`预览: ${result.title}`}
      aria-modal="true"
    >
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-border bg-surface-secondary">
        <div className="flex items-center gap-2 min-w-0">
          <span
            className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-primary-light text-primary"
            data-testid="platform-badge"
          >
            <span aria-hidden="true">{platform.icon}</span>
            {platform.name}
          </span>
          <h2 className="text-base font-semibold text-text-primary truncate">
            {result.title}
          </h2>
        </div>
        <button
          onClick={onClose}
          aria-label="关闭预览"
          className="flex-shrink-0 w-7 h-7 flex items-center justify-center rounded-lg text-text-secondary hover:bg-surface-tertiary hover:text-text-primary transition-colors"
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
              className="block text-xs text-primary hover:underline truncate"
              data-testid="result-url"
            >
              {result.url}
            </a>

            {/* Quality score + Recommendation reason */}
            <div className="flex items-start gap-3">
              <div
                className="flex-shrink-0 flex items-center gap-1 px-2.5 py-1 rounded-lg bg-accent-light"
                data-testid="quality-score"
              >
                <span className="text-accent font-bold text-lg">⭐ {score}</span>
                <span className="text-xs text-text-secondary">/10</span>
              </div>
              {result.recommendationReason && (
                <p className="text-sm text-text-secondary leading-relaxed" data-testid="recommendation-reason">
                  💡 {result.recommendationReason}
                </p>
              )}
            </div>

            {/* AI Content Summary */}
            {result.contentSummary && (
              <section data-testid="content-summary">
                <h3 className="text-sm font-medium text-text-primary mb-1">📝 内容摘要</h3>
                <p className="text-sm text-text-secondary leading-relaxed bg-surface-secondary rounded-lg p-3">
                  {result.contentSummary}
                </p>
              </section>
            )}

            {/* Comment Summary */}
            {result.commentSummary && (
              <section data-testid="comment-summary">
                <h3 className="text-sm font-medium text-text-primary mb-1">💬 评论结论</h3>
                <p className="text-sm text-text-secondary leading-relaxed bg-surface-secondary rounded-lg p-3">
                  {result.commentSummary}
                </p>
              </section>
            )}

            {/* Image Thumbnail Grid */}
            {images.length > 0 && (
              <section data-testid="image-grid">
                <h3 className="text-sm font-medium text-text-primary mb-2">🖼️ 图片</h3>
                <div className="grid grid-cols-3 gap-2">
                  {images.map((url, idx) => (
                    <a
                      key={idx}
                      href={url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="aspect-square rounded-lg overflow-hidden border border-border hover:border-primary transition-colors"
                      aria-label={`查看大图 ${idx + 1}`}
                    >
                      <img
                        src={url}
                        alt={`图片 ${idx + 1}`}
                        className="w-full h-full object-cover"
                        loading="lazy"
                      />
                    </a>
                  ))}
                </div>
              </section>
            )}

            {/* Engagement Metrics */}
            {Object.keys(metrics).length > 0 && (
              <section data-testid="engagement-metrics">
                <h3 className="text-sm font-medium text-text-primary mb-2">📊 互动指标</h3>
                <div className="flex flex-wrap gap-3">
                  {metrics.likes != null && (
                    <MetricBadge icon="👍" label="点赞" value={metrics.likes} />
                  )}
                  {metrics.collects != null && (
                    <MetricBadge icon="⭐" label="收藏" value={metrics.collects} />
                  )}
                  {metrics.comments != null && (
                    <MetricBadge icon="💬" label="评论" value={metrics.comments} />
                  )}
                  {/* Render any other metrics */}
                  {Object.entries(metrics)
                    .filter(([k]) => !['likes', 'collects', 'comments'].includes(k))
                    .map(([key, val]) => (
                      <MetricBadge key={key} icon="📈" label={key} value={val} />
                    ))}
                </div>
              </section>
            )}

            {/* Refresh error */}
            {refreshError && (
              <div className="flex items-center gap-2 p-3 rounded-lg bg-red-50 border border-red-200" data-testid="refresh-error">
                <span className="text-sm text-red-600">{refreshError}</span>
                <button
                  onClick={handleRefresh}
                  className="text-sm text-primary hover:underline font-medium"
                >
                  重试
                </button>
              </div>
            )}
          </>
        )}
      </div>

      {/* Footer actions */}
      <div className="flex items-center gap-2 px-4 py-3 border-t border-border bg-surface-secondary">
        <Button
          variant="primary"
          size="sm"
          onClick={() => window.open(result.url, '_blank')}
        >
          查看完整信息
        </Button>
        <Button
          variant="secondary"
          size="sm"
          loading={refreshing}
          onClick={handleRefresh}
        >
          刷新
        </Button>
        <Button
          variant="ghost"
          size="sm"
          onClick={onClose}
        >
          关闭
        </Button>
      </div>
    </div>
  )
}

/** Metric badge for engagement data */
const MetricBadge: React.FC<{ icon: string; label: string; value: any }> = ({
  icon,
  label,
  value,
}) => (
  <span className="inline-flex items-center gap-1 px-2 py-1 rounded-lg bg-surface-tertiary text-sm text-text-secondary">
    <span aria-hidden="true">{icon}</span>
    <span>{label}</span>
    <span className="font-medium text-text-primary">{formatNumber(value)}</span>
  </span>
)

/** Format large numbers (e.g. 12345 → 1.2万) */
function formatNumber(n: any): string {
  const num = Number(n)
  if (isNaN(num)) return String(n)
  if (num >= 10000) return (num / 10000).toFixed(1) + '万'
  return String(num)
}

/** Skeleton loading state during refresh */
const SkeletonContent: React.FC = () => (
  <div className="space-y-4 animate-pulse" data-testid="skeleton">
    <div className="h-4 bg-surface-tertiary rounded w-3/4" />
    <div className="flex gap-3">
      <div className="h-10 w-20 bg-surface-tertiary rounded-lg" />
      <div className="flex-1 h-10 bg-surface-tertiary rounded-lg" />
    </div>
    <div className="space-y-2">
      <div className="h-3 bg-surface-tertiary rounded w-1/4" />
      <div className="h-20 bg-surface-tertiary rounded-lg" />
    </div>
    <div className="space-y-2">
      <div className="h-3 bg-surface-tertiary rounded w-1/4" />
      <div className="h-16 bg-surface-tertiary rounded-lg" />
    </div>
    <div className="grid grid-cols-3 gap-2">
      {[1, 2, 3].map((i) => (
        <div key={i} className="aspect-square bg-surface-tertiary rounded-lg" />
      ))}
    </div>
    <div className="flex gap-3">
      {[1, 2, 3].map((i) => (
        <div key={i} className="h-8 w-16 bg-surface-tertiary rounded-lg" />
      ))}
    </div>
  </div>
)
