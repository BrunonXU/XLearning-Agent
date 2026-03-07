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
import { useSearchStore } from '../../store/searchStore'
import type { SearchResult, PlatformType } from '../../types'

const PLATFORM_LABELS: Record<PlatformType, { icon: string; name: string }> = {
  bilibili: { icon: '📺', name: 'B站' },
  youtube: { icon: '🎬', name: 'YouTube' },
  google: { icon: '🌐', name: 'Google' },
  github: { icon: '🔗', name: 'GitHub' },
  xiaohongshu: { icon: '📕', name: '小红书' },
  zhihu: { icon: '💡', name: '知乎' },
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

  // 订阅 store 中的深度分析数据更新
  const storeDetail = useSearchStore(s => s.resultDetailMap[initialResult.id])
  const isDeepAnalysisPending = useSearchStore(s => s.pendingDeepAnalysis.has(initialResult.id))

  useEffect(() => { setResult(initialResult) }, [initialResult])
  useEffect(() => { setImageIndex(0) }, [initialResult])

  // 当 store 中的数据更新时（深度分析完成），合并到本地 result
  useEffect(() => {
    if (storeDetail && (storeDetail.keyPoints?.length || storeDetail.credibility?.timeliness != null)) {
      setResult(prev => ({ ...prev, keyPoints: storeDetail.keyPoints, keyFacts: storeDetail.keyFacts, methodology: storeDetail.methodology, credibility: storeDetail.credibility }))
    }
  }, [storeDetail])

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
      className="absolute inset-0 z-50 flex flex-col bg-white dark:bg-dark-bg overflow-hidden"
      role="dialog"
      aria-label={`预览: ${result.title}`}
      aria-modal="true"
    >
      {/* Header — 与 ContentViewer 统一 */}
      <div className="flex items-center gap-3 px-5 py-3.5 border-b border-border flex-shrink-0">
        <button
          onClick={onClose}
          aria-label="返回材料列表"
          className="w-8 h-8 flex items-center justify-center rounded-full hover:bg-surface-tertiary transition-colors text-text-secondary"
        >
          ←
        </button>
        <div className="flex-1 min-w-0">
          <h1 className="text-[15px] font-semibold text-text-primary truncate leading-tight">
            {platform.icon} {result.title}
          </h1>
        </div>
        <span className="text-xs text-text-secondary px-2 py-1 rounded-md bg-surface-tertiary font-medium">
          {platform.name}
        </span>
      </div>

      {/* Scrollable content */}
      <div className="flex-1 overflow-y-auto px-5 py-5 space-y-5">
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

            {/* Score + metrics card */}
            <div className="flex items-center gap-3 flex-wrap bg-gradient-to-r from-[#FFF8F5] to-[#FFF] dark:from-dark-surface dark:to-dark-bg rounded-xl p-3.5 border border-[#F2DFD3]">
              <span className="text-[#F9AB00] font-bold text-xl">⭐ {score}<span className="text-xs text-[#5F6368] font-normal">/10</span></span>
              <div className="w-px h-6 bg-[#E8EAED]" />
              {coreMetrics.map(m => (
                <span key={m.label} className="inline-flex items-center gap-1.5 text-sm text-[#5F6368] bg-white dark:bg-dark-surface px-2.5 py-1 rounded-full border border-[#E8EAED]">
                  <span>{m.icon}</span>
                  <span className="font-medium">{formatNumber(m.value)}</span>
                </span>
              ))}
            </div>

            {/* Recommendation reason */}
            {result.recommendationReason && (
              <div className="flex items-start gap-2 bg-[#FEF7E0] dark:bg-dark-surface rounded-lg px-3.5 py-2.5 border border-[#FDE68A]/50">
                <span className="text-base mt-0.5">💡</span>
                <p className="text-[14px] text-[#78590A] dark:text-dark-text leading-6">{result.recommendationReason}</p>
              </div>
            )}

            {/* Image carousel — 大图竖直展示 */}
            {images.length > 0 && (
              <section>
                <div className="flex items-center justify-between mb-2">
                  <h3 className="text-[15px] font-medium text-[#202124] dark:text-dark-text flex items-center gap-1.5">
                    <span className="w-1 h-4 bg-[#E8EAED] rounded-full" />
                    🖼️ 图片
                  </h3>
                  <span className="text-xs text-[#9AA0A6] bg-[#F1F3F4] px-2 py-0.5 rounded-full">{imageIndex + 1} / {images.length}</span>
                </div>
                <div className="relative rounded-xl overflow-hidden border border-[#DADCE0] dark:border-dark-border bg-[#FAFAFA]">
                  <a href={images[imageIndex]} target="_blank" rel="noopener noreferrer">
                    <img
                      src={images[imageIndex]}
                      alt={`图片 ${imageIndex + 1}`}
                      className="w-full object-contain"
                      style={{ maxHeight: '70vh' }}
                      loading="lazy"
                    />
                  </a>
                  {images.length > 1 && (
                    <>
                      <button
                        onClick={() => setImageIndex(i => (i - 1 + images.length) % images.length)}
                        className="absolute left-2 top-1/2 -translate-y-1/2 w-9 h-9 rounded-full bg-black/40 text-white flex items-center justify-center hover:bg-black/60 transition-colors text-lg"
                        aria-label="上一张"
                      >‹</button>
                      <button
                        onClick={() => setImageIndex(i => (i + 1) % images.length)}
                        className="absolute right-2 top-1/2 -translate-y-1/2 w-9 h-9 rounded-full bg-black/40 text-white flex items-center justify-center hover:bg-black/60 transition-colors text-lg"
                        aria-label="下一张"
                      >›</button>
                    </>
                  )}
                </div>
              </section>
            )}

            {/* AI Content Summary → 信息整理 */}
            {result.contentSummary && (
              <section>
                <h3 className="text-[15px] font-medium text-[#202124] dark:text-dark-text mb-2 flex items-center gap-1.5">
                  <span className="w-1 h-4 bg-[#D97757] rounded-full" />
                  📋 信息整理
                </h3>
                <div className="bg-[#F8F9FA] dark:bg-dark-surface rounded-xl p-4 space-y-1.5">
                  {result.contentSummary.split('→').map((segment, idx) => {
                    const text = segment.trim()
                    if (!text) return null
                    return idx === 0 ? (
                      <p key={idx} className="text-[14px] text-[#202124] dark:text-dark-text leading-6 font-medium">{text}</p>
                    ) : (
                      <div key={idx} className="flex items-start gap-2 text-[14px] text-[#3C4043] leading-6">
                        <span className="text-[#D97757] mt-0.5 flex-shrink-0">→</span>
                        <span>{text}</span>
                      </div>
                    )
                  })}
                </div>
              </section>
            )}

            {/* 原文内容 — 加入素材后的完整阅读 */}
            {result.contentText && (
              <section>
                <h3 className="text-[15px] font-medium text-[#202124] dark:text-dark-text mb-2 flex items-center gap-1.5">
                  <span className="w-1 h-4 bg-[#5F6368] rounded-full" />
                  📄 原文内容
                </h3>
                <div className="bg-white dark:bg-dark-surface rounded-xl border border-[#E8EAED] p-4">
                  <p className="text-[14px] text-[#3C4043] dark:text-dark-text leading-7 whitespace-pre-line">{result.contentText}</p>
                </div>
              </section>
            )}

            {/* 核心观点 */}
            {result.keyPoints && result.keyPoints.length > 0 && (
              <section>
                <h3 className="text-[15px] font-medium text-[#202124] dark:text-dark-text mb-2 flex items-center gap-1.5">
                  <span className="w-1 h-4 bg-[#4285F4] rounded-full" />
                  🎯 核心观点
                </h3>
                <div className="grid gap-2">
                  {result.keyPoints.map((point, idx) => (
                    <div key={idx} className="flex items-start gap-2.5 bg-[#EEF4FF] dark:bg-dark-surface rounded-lg px-3.5 py-2.5 border border-[#D2E3FC]/60">
                      <span className="flex-shrink-0 w-6 h-6 rounded-full bg-[#4285F4] text-white text-xs flex items-center justify-center font-semibold">{idx + 1}</span>
                      <span className="text-[14px] text-[#202124] dark:text-dark-text leading-6">{point}</span>
                    </div>
                  ))}
                </div>
              </section>
            )}

            {/* 关键数据/事实 */}
            {result.keyFacts && result.keyFacts.length > 0 && (
              <section>
                <h3 className="text-[15px] font-medium text-[#202124] dark:text-dark-text mb-2 flex items-center gap-1.5">
                  <span className="w-1 h-4 bg-[#34A853] rounded-full" />
                  📊 关键数据
                </h3>
                <div className="flex flex-wrap gap-2">
                  {result.keyFacts.map((fact, idx) => (
                    <span key={idx} className="inline-flex items-center gap-1.5 text-[13px] text-[#137333] bg-[#E6F4EA] rounded-lg px-3 py-2 leading-5 border border-[#CEEAD6]">
                      <span className="text-[#34A853]">•</span>
                      {fact}
                    </span>
                  ))}
                </div>
              </section>
            )}

            {/* 方法论/步骤 */}
            {result.methodology && result.methodology.length > 0 && (
              <section>
                <h3 className="text-[15px] font-medium text-[#202124] dark:text-dark-text mb-2 flex items-center gap-1.5">
                  <span className="w-1 h-4 bg-[#FBBC04] rounded-full" />
                  📝 方法/步骤
                </h3>
                <div className="bg-[#F8F9FA] dark:bg-dark-surface rounded-xl p-4 space-y-3">
                  {result.methodology.map((step, idx) => (
                    <div key={idx} className="flex items-start gap-3">
                      <div className="flex flex-col items-center">
                        <span className="w-7 h-7 rounded-full bg-[#FEF7E0] border border-[#FBBC04] text-[#78590A] text-xs flex items-center justify-center font-semibold">{idx + 1}</span>
                        {idx < result.methodology!.length - 1 && <div className="w-px h-3 bg-[#DADCE0] mt-1" />}
                      </div>
                      <span className="text-[14px] text-[#3C4043] leading-6 pt-1">{step}</span>
                    </div>
                  ))}
                </div>
              </section>
            )}

            {/* 可信度评估 */}
            {result.credibility && (result.credibility.timeliness != null || result.credibility.authority != null) && (
              <section>
                <h3 className="text-[15px] font-medium text-[#202124] dark:text-dark-text mb-2 flex items-center gap-1.5">
                  <span className="w-1 h-4 bg-[#9AA0A6] rounded-full" />
                  🛡️ 可信度评估
                </h3>
                <div className="grid grid-cols-2 gap-2">
                  {([
                    { key: 'timeliness' as const, label: '时效性', icon: '🕐' },
                    { key: 'authority' as const, label: '权威性', icon: '👤' },
                    { key: 'accuracy' as const, label: '准确性', icon: '✅' },
                    { key: 'objectivity' as const, label: '客观性', icon: '⚖️' },
                  ] as const).map(dim => {
                    const val = result.credibility?.[dim.key]
                    const note = result.credibility?.[`${dim.key}_note`]
                    if (val == null) return null
                    const pct = (val / 10) * 100
                    const color = val >= 7 ? '#34A853' : val >= 4 ? '#F9AB00' : '#EA4335'
                    return (
                      <div key={dim.key} className="bg-[#F8F9FA] dark:bg-dark-surface rounded-lg p-2.5 border border-[#E8EAED]">
                        <div className="flex items-center justify-between mb-1.5">
                          <span className="text-xs text-[#5F6368]">{dim.icon} {dim.label}</span>
                          <span className="text-xs font-bold" style={{ color }}>{val}/10</span>
                        </div>
                        <div className="w-full h-2 bg-[#E8EAED] rounded-full overflow-hidden">
                          <div className="h-full rounded-full transition-all duration-500" style={{ width: `${pct}%`, backgroundColor: color }} />
                        </div>
                        {note && <p className="text-[11px] text-[#9AA0A6] mt-1.5 leading-4">{note}</p>}
                      </div>
                    )
                  })}
                </div>
              </section>
            )}

            {/* 高赞评论 — 卡片样式，小字斜体 */}
            {/* 深度分析加载提示 — 仅在实际触发了深度分析时显示 */}
            {isDeepAnalysisPending && !result.keyPoints?.length && (
              <div className="flex items-center gap-2 py-3 text-xs text-[#9AA0A6]">
                <span className="inline-flex gap-0.5">
                  <span className="w-1.5 h-1.5 rounded-full bg-[#D97757] animate-bounce" style={{ animationDelay: '0ms' }} />
                  <span className="w-1.5 h-1.5 rounded-full bg-[#D97757] animate-bounce" style={{ animationDelay: '100ms' }} />
                  <span className="w-1.5 h-1.5 rounded-full bg-[#D97757] animate-bounce" style={{ animationDelay: '200ms' }} />
                </span>
                <span>深度分析中，核心观点和可信度评估即将呈现...</span>
              </div>
            )}
            {comments.length > 0 && (
              <section>
                <h3 className="text-[15px] font-medium text-[#202124] dark:text-dark-text mb-2 flex items-center gap-1.5">
                  <span className="w-1 h-4 bg-[#EA4335] rounded-full" />
                  🔥 高赞评论
                </h3>
                <div className="space-y-2">
                  {comments.map((text, idx) => (
                    <div key={idx} className="flex items-start gap-0 rounded-xl overflow-hidden border border-[#E8EAED] bg-white dark:bg-dark-surface">
                      <div className="w-1 self-stretch bg-[#D97757]/60 flex-shrink-0" />
                      <div className="flex-1 px-3.5 py-2.5">
                        <p className="text-[12px] text-[#5F6368] dark:text-dark-text-secondary leading-5 italic">{text}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </section>
            )}

            {/* 评论结论 — callout 样式 */}
            {result.commentSummary && (
              <section>
                <div className="flex items-start gap-2.5 bg-[#F0F4FF] dark:bg-dark-surface rounded-xl px-4 py-3 border border-[#D2E3FC]/60">
                  <span className="text-lg mt-0.5">💬</span>
                  <div>
                    <p className="text-xs font-medium text-[#4285F4] mb-1">评论结论</p>
                    <p className="text-[14px] text-[#3C4043] dark:text-dark-text leading-6">{result.commentSummary}</p>
                  </div>
                </div>
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

      {/* Footer — 与 ContentViewer 统一 */}
      <div className="flex items-center gap-2 px-5 py-3 border-t border-border flex-shrink-0">
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
