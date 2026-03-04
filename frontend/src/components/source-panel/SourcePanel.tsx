import React, { useState, useEffect } from 'react'
import { MaterialList } from './MaterialList'
import { SearchPanel } from './SearchPanel'
import { UploadArea } from './UploadArea'
import { PreviewPopup } from './PreviewPopup'
import { ContentViewer } from './ContentViewer'
import { useSourceStore } from '../../store/sourceStore'
import { useSearchStore } from '../../store/searchStore'
import type { Material, SearchResult } from '../../types'

type ActiveTab = 'upload' | 'search'

/** 判断材料是否为本地上传文件（非外部搜索资源） */
function isLocalFile(m: Material): boolean {
  return m.type === 'other' || !m.url
}

/** 推断本地文件类型 */
function inferFileType(name: string): 'markdown' | 'pdf' | 'text' {
  const lower = name.toLowerCase()
  if (lower.endsWith('.md') || lower.endsWith('.markdown')) return 'markdown'
  if (lower.endsWith('.pdf')) return 'pdf'
  return 'text'
}

interface SourcePanelProps {
  planId?: string
  onReadingChange?: (reading: boolean) => void
}

export const SourcePanel: React.FC<SourcePanelProps> = ({ planId = '', onReadingChange }) => {
  const [activeTab, setActiveTab] = useState<ActiveTab>('upload')
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [previewResult, setPreviewResult] = useState<SearchResult | null>(null)
  const [viewingMaterial, setViewingMaterial] = useState<Material | null>(null)
  const { materials, removeMaterial, addMaterial } = useSourceStore()

  // 清理残留的临时材料（temp- 开头的 ID 是上传中断留下的）
  useEffect(() => {
    const tempMats = materials.filter(m => m.id.startsWith('temp-'))
    tempMats.forEach(m => removeMaterial(m.id))
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  const handleRemove = async (id: string) => {
    removeMaterial(id)
    try {
      await fetch(`/api/material/${id}?plan_id=${planId}`, { method: 'DELETE' })
    } catch {
      // 静默失败
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

    if (isLocalFile(mat)) {
      // 本地文件 → 左侧面板内全屏展示
      setViewingMaterial(mat)
      onReadingChange?.(true)
    } else {
      // 外部资源 → PreviewPopup（从 searchStore 获取详情）
      const detail = useSearchStore.getState().getResultDetail(id)
      if (detail) {
        setPreviewResult(detail)
      } else {
        // 没有缓存的详情，构造基础 SearchResult
        setPreviewResult({
          id: mat.id,
          title: mat.name,
          url: mat.url || '',
          platform: mat.type,
          description: '',
          qualityScore: 0,
          recommendationReason: '',
        })
      }
    }
  }

  const handleAddFromSearch = (results: SearchResult[]) => {
    // 保存完整搜索结果到 searchStore（供 PreviewPopup 使用）
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
  }

  return (
    <div className="flex flex-col h-full overflow-hidden relative">
      {/* PreviewPopup overlay */}
      {previewResult && (
        <PreviewPopup
          result={previewResult}
          onClose={() => { setPreviewResult(null); setSelectedId(null) }}
          onRefresh={() => {
            if (previewResult) {
              useSearchStore.getState().saveResultDetails([previewResult])
            }
          }}
        />
      )}

      {/* ContentViewer — 左侧面板内全屏覆盖 */}
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

      <div className="flex items-center justify-between px-5 h-14 flex-shrink-0 border-b border-[#DADCE0]">
        <span className="text-base font-semibold text-[#202124] flex items-center gap-2">
          📚 学习材料
          {materials.length > 0 && (
            <span className="text-xs bg-[#E8F0FE] text-[#1A73E8] px-1.5 py-0.5 rounded-full font-medium">
              {materials.length}
            </span>
          )}
        </span>
        <button
          aria-label="添加材料"
          className="w-7 h-7 flex items-center justify-center rounded-full text-[#5F6368] hover:bg-[#F1F3F4] transition-colors duration-150 text-xl leading-none"
        >
          +
        </button>
      </div>

      <div className="flex gap-2 px-4 py-3 flex-shrink-0">
        {(['upload', 'search'] as ActiveTab[]).map(tab => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`flex-1 h-10 rounded-lg text-sm font-medium transition-all duration-150 ${
              activeTab === tab
                ? 'bg-[#E8F0FE] text-[#1A73E8]'
                : 'text-[#5F6368] hover:bg-[#F1F3F4]'
            }`}
          >
            {tab === 'upload' ? '➕ 上传文件' : '🔍 搜索资源'}
          </button>
        ))}
      </div>

      <div className="flex-1 overflow-y-auto scrollbar-thin px-4 pb-4">
        {activeTab === 'upload' ? (
          <div className="flex flex-col gap-3">
            <UploadArea planId={planId} />
            <MaterialList
              materials={materials}
              selectedId={selectedId ?? undefined}
              onSelect={handleSelect}
              onRemove={handleRemove}
            />
          </div>
        ) : (
          <SearchPanel onAddToMaterials={handleAddFromSearch} />
        )}
      </div>
    </div>
  )
}
