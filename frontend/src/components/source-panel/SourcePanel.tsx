import React, { useState } from 'react'
import { MaterialList } from './MaterialList'
import { SearchPanel } from './SearchPanel'
import { UploadArea } from './UploadArea'
import { useSourceStore } from '../../store/sourceStore'
import type { SearchResult } from '../../types'

type ActiveTab = 'upload' | 'search'

interface SourcePanelProps {
  planId?: string
}

export const SourcePanel: React.FC<SourcePanelProps> = ({ planId = '' }) => {
  const [activeTab, setActiveTab] = useState<ActiveTab>('upload')
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const { materials, removeMaterial, addMaterial } = useSourceStore()

  const handleRemove = async (id: string) => {
    removeMaterial(id)
    try {
      await fetch(`/api/material/${id}?plan_id=${planId}`, { method: 'DELETE' })
    } catch {
      // 静默失败
    }
  }

  const handleSelect = async (id: string) => {
    setSelectedId(prev => prev === id ? null : id)
    // 点击材料 → 选中高亮，不再插入系统消息
  }

  const handleAddFromSearch = (results: SearchResult[]) => {
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
    <div className="flex flex-col h-full overflow-hidden">
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
