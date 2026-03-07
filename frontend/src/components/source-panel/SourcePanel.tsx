import React, { useState, useEffect } from 'react'
import { createPortal } from 'react-dom'
import { MaterialList } from './MaterialList'
import { MaterialIcon } from './MaterialItem'
import { SearchPanel } from './SearchPanel'
import { UploadArea } from './UploadArea'
import { PreviewPopup } from './PreviewPopup'
import { ContentViewer } from './ContentViewer'
import { useSourceStore } from '../../store/sourceStore'
import { useSearchStore } from '../../store/searchStore'
import type { Material, SearchResult } from '../../types'

type ActiveTab = 'upload' | 'search'

function isLocalFile(m: Material): boolean {
  return m.type === 'other' || !m.url
}

function inferFileType(name: string): 'markdown' | 'pdf' | 'text' {
  const lower = name.toLowerCase()
  if (lower.endsWith('.md') || lower.endsWith('.markdown')) return 'markdown'
  if (lower.endsWith('.pdf')) return 'pdf'
  return 'text'
}

interface SourcePanelProps {
  planId?: string
  onReadingChange?: (reading: boolean) => void
  isCollapsed?: boolean
  onToggleCollapse?: () => void
}

export const SourcePanel: React.FC<SourcePanelProps> = ({
  planId = '', onReadingChange, isCollapsed = false, onToggleCollapse
}) => {
  const [activeTab, setActiveTab] = useState<ActiveTab>('upload')
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [previewResult, setPreviewResult] = useState<SearchResult | null>(null)
  const [viewingMaterial, setViewingMaterial] = useState<Material | null>(null)
  const [hoveredFile, setHoveredFile] = useState<{ id: string, rect: DOMRect } | null>(null)
  const { materials, removeMaterial, addMaterial } = useSourceStore()

  useEffect(() => {
    const tempMats = materials.filter(m => m.id.startsWith('temp-'))
    tempMats.forEach(m => removeMaterial(m.id))
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  const handleRemove = async (id: string) => {
    removeMaterial(id)
    try {
      await fetch(`/api/material/${id}?plan_id=${planId}`, { method: 'DELETE' })
    } catch {
      // quiet
    }
  }

  const handleSelect = async (id: string) => {
    if (selectedId === id) {
      setSelectedId(null)
      return
    }
    setSelectedId(id)

    const mat = materials.find(m => m.id === id)
    if (!mat) return

    // 标记为已查看
    if (!mat.viewedAt) {
      useSourceStore.getState().updateMaterial(id, { viewedAt: new Date().toISOString() })
      fetch(`/api/material/${id}/viewed`, { method: 'PATCH' }).catch(() => {})
    }

    if (isLocalFile(mat)) {
      setViewingMaterial(mat)
      onReadingChange?.(true)
    } else {
      onReadingChange?.(true)
      const detail = useSearchStore.getState().getResultDetail(id)
      if (detail) {
        setPreviewResult(detail)
      } else {
        // Fallback: construct a minimal SearchResult with safe defaults
        setPreviewResult({
          id: mat.id,
          title: mat.name,
          url: mat.url || '',
          platform: mat.type,
          description: '',
          qualityScore: 0,
          recommendationReason: '',
          contentSummary: '',
          commentSummary: '',
          engagementMetrics: {},
          imageUrls: [],
          topComments: [],
        })
      }
    }
  }

  const handleAddFromSearch = (results: SearchResult[]) => {
    useSearchStore.getState().saveResultDetails(results)
    results.forEach(r => {
      addMaterial({
        id: r.id,
        type: r.platform,
        name: r.title.slice(0, 40),
        url: r.url,
        status: 'ready',
        addedAt: new Date().toISOString(),
      })
    })
    setActiveTab('upload')

    // 持久化到后端数据库
    if (planId) {
      fetch('/api/materials/from-search', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          items: results.map(r => ({
            id: r.id,
            planId: planId,
            platform: r.platform,
            name: r.title.slice(0, 40),
            url: r.url,
            extraData: {
              description: r.description,
              qualityScore: r.qualityScore,
              recommendationReason: r.recommendationReason,
              contentSummary: r.contentSummary,
              commentSummary: r.commentSummary,
              engagementMetrics: r.engagementMetrics,
              imageUrls: r.imageUrls,
              topComments: r.topComments,
              contentText: r.contentText,
            },
          })),
        }),
      }).catch(() => { /* 静默失败 */ })
    }

    // 异步触发深度分析（不阻塞 UI）
    results.forEach(r => {
      useSearchStore.getState().markDeepAnalysisPending(r.id)
      fetch('/api/resource/deep-analysis', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          materialId: r.id,
          title: r.title,
          url: r.url,
          platform: r.platform,
          description: r.description,
          contentSummary: r.contentSummary ?? '',
          commentSummary: r.commentSummary ?? '',
          topComments: r.topComments ?? [],
          engagementMetrics: r.engagementMetrics ?? {},
        }),
      })
        .then(res => res.ok ? res.json() : null)
        .then(data => {
          if (data) {
            useSearchStore.getState().updateResultDetail(r.id, {
              keyPoints: data.keyPoints,
              keyFacts: data.keyFacts,
              methodology: data.methodology,
              credibility: data.credibility,
            })
          }
        })
        .catch(() => { /* 静默失败 */ })
        .finally(() => {
          useSearchStore.getState().markDeepAnalysisDone(r.id)
        })
    })
  }

  return (
    <div className="flex flex-col h-full overflow-hidden relative">
      {previewResult && (
        <PreviewPopup
          result={previewResult}
          onClose={() => { setPreviewResult(null); setSelectedId(null); onReadingChange?.(false) }}
          onRefresh={() => {
            if (previewResult) {
              useSearchStore.getState().saveResultDetails([previewResult])
            }
          }}
        />
      )}

      {viewingMaterial && (
        <div className="absolute inset-0 z-50 bg-white dark:bg-dark-surface overflow-hidden">
          <ContentViewer
            materialId={viewingMaterial.id}
            materialName={viewingMaterial.name}
            fileType={inferFileType(viewingMaterial.name)}
            planId={planId}
            onBack={() => { setViewingMaterial(null); setSelectedId(null); onReadingChange?.(false) }}
          />
        </div>
      )}

      <div className={`flex items-center h-[68px] px-8 flex-shrink-0 transition-all border-b border-[#E5E5E5] ${isCollapsed ? 'justify-center px-0 flex-col gap-0 h-[68px]' : 'justify-between'}`}>
        {!isCollapsed && (
          <span className="text-base font-semibold text-[#202124] flex items-center gap-2 mt-2">
            学习材料
            {materials.length > 0 && (
              <span className="text-xs bg-[#F2DFD3] text-[#D97757] px-2 py-0.5 rounded-full font-medium">
                {materials.length}
              </span>
            )}
          </span>
        )}
        <div className={`flex items-center gap-2 ${isCollapsed ? 'flex-col' : ''}`}>
          <button
            aria-label={isCollapsed ? "展开侧边栏" : "收起侧边栏"}
            onClick={onToggleCollapse}
            className="w-10 h-10 flex items-center justify-center rounded-xl text-[#5F6368] hover:bg-[#EFECE5] transition-colors duration-150"
          >
            {isCollapsed ? (
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect><line x1="9" y1="3" x2="9" y2="21"></line></svg>
            ) : (
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect><line x1="9" y1="3" x2="9" y2="21"></line></svg>
            )}
          </button>
        </div>
      </div>

      {!isCollapsed && (
        <div className="flex gap-2 px-6 py-3 flex-shrink-0 animate-in fade-in duration-200">
          {(['upload', 'search'] as ActiveTab[]).map(tab => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`flex-1 h-9 rounded-lg text-sm font-medium transition-all duration-150 ${activeTab === tab ? 'bg-[#F2DFD3] text-[#D97757]' : 'text-[#5F6368] hover:bg-[#EFECE5]'
                }`}
            >
              {tab === 'upload' ? '➕ 上传文件' : '🔍 搜索资源'}
            </button>
          ))}
        </div>
      )}

      <div className={`flex-1 overflow-y-auto scrollbar-thin ${isCollapsed ? 'py-4' : 'px-6 pb-6'}`}>
        {isCollapsed ? (
          <ul className="flex flex-col items-center gap-4 w-full relative">
            <li className="w-10 h-10 flex items-center justify-center rounded-full text-[#5F6368] hover:bg-[#EFECE5] transition-colors duration-150 cursor-pointer text-2xl"
              onClick={onToggleCollapse}>
              +
            </li>
            {materials.map(m => (
              <li key={m.id} onClick={() => handleSelect(m.id)}
                onMouseEnter={(e) => setHoveredFile({ id: m.id, rect: e.currentTarget.getBoundingClientRect() })}
                onMouseLeave={() => setHoveredFile(null)}
                draggable
                onDragStart={(e) => {
                  e.dataTransfer.effectAllowed = 'move'
                  e.dataTransfer.setData('application/material', JSON.stringify({
                    id: m.id, name: m.name, platform: m.type,
                  }))
                }}
                className="group relative flex items-center justify-center w-full focus:outline-none">

                <div className={`w-12 h-12 flex items-center justify-center rounded-full cursor-pointer transition-all duration-150 ${selectedId === m.id ? 'bg-[#F2DFD3]' : 'hover:bg-[#EFECE5]'
                  }`}>
                  <MaterialIcon material={m} className="w-7 h-8 text-[10px]" />
                </div>
              </li>
            ))}
          </ul>
        ) : activeTab === 'upload' ? (
          <div className="flex flex-col gap-3">
            <UploadArea planId={planId} />
            <MaterialList
              materials={materials}
              planId={planId}
              selectedId={selectedId ?? undefined}
              onSelect={handleSelect}
              onRemove={handleRemove}
            />
          </div>
        ) : (
          <SearchPanel planId={planId} onAddToMaterials={handleAddFromSearch} onViewDetail={(r) => { setPreviewResult(r); onReadingChange?.(true) }} />
        )}
      </div>

      {/* Tooltip Portal */}
      {hoveredFile && isCollapsed && createPortal(
        <div style={{ top: hoveredFile.rect.top + (hoveredFile.rect.height / 2), left: hoveredFile.rect.right + 8, transform: 'translateY(-50%)' }}
          className="fixed z-[9999] px-3 py-1.5 bg-[#1E1E1E] text-white text-[13px] whitespace-nowrap rounded-md shadow-lg pointer-events-none fade-in duration-200">
          {materials.find(m => m.id === hoveredFile.id)?.name}
        </div>,
        document.body
      )}
    </div>
  )
}
