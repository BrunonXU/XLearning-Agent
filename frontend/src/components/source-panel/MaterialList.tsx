import React, { useCallback } from 'react'
import { MaterialItem } from './MaterialItem'
import type { Material } from '../../types'

interface MaterialListProps {
  materials: Material[]
  selectedId?: string
  onSelect: (id: string) => void
  onRemove: (id: string) => void
}

export const MaterialList: React.FC<MaterialListProps> = ({
  materials, selectedId, onSelect, onRemove,
}) => {
  // 11.2: ↑/↓ 键盘导航
  const handleListKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (!['ArrowUp', 'ArrowDown'].includes(e.key)) return
    e.preventDefault()
    const idx = materials.findIndex(m => m.id === selectedId)
    if (e.key === 'ArrowDown') {
      const next = materials[idx + 1] ?? materials[0]
      if (next) onSelect(next.id)
    } else {
      const prev = materials[idx - 1] ?? materials[materials.length - 1]
      if (prev) onSelect(prev.id)
    }
  }, [materials, selectedId, onSelect])
  if (materials.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-8 text-center px-2">
        <span className="text-3xl mb-3">📂</span>
        <p className="text-sm text-text-secondary dark:text-dark-text leading-relaxed">
          上传 PDF 或搜索资源，让 AI 基于你的材料回答
        </p>
      </div>
    )
  }

  return (
    <div>
      {/* 上传区域（拖拽） */}
      <div className="border-2 border-dashed border-border rounded-xl p-4 mb-3 text-center hover:border-primary hover:bg-primary-light/30 transition-all duration-150 cursor-pointer">
        <p className="text-xs text-text-secondary">拖拽 PDF 到此处，或</p>
        <button className="text-xs text-primary hover:underline mt-0.5">点击选择文件</button>
      </div>

      {/* 已添加材料 */}
      <p className="text-xs font-medium text-text-secondary uppercase tracking-wide mt-4 mb-2">
        已添加材料
      </p>
      <ul role="listbox" aria-label="学习材料列表" className="flex flex-col gap-1" onKeyDown={handleListKeyDown}>
        {materials.map(m => (
          <MaterialItem
            key={m.id}
            material={m}
            isSelected={selectedId === m.id}
            onClick={() => onSelect(m.id)}
            onRemove={() => onRemove(m.id)}
          />
        ))}
      </ul>
    </div>
  )
}
