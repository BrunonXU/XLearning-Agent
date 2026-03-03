import React, { useState } from 'react'
import { ConfirmModal } from '../ui/Modal'
import type { Material, PlatformType } from '../../types'

const PLATFORM_ICONS: Record<PlatformType, string> = {
  bilibili: '📺', youtube: '🎬', google: '🌐',
  github: '🔗', xiaohongshu: '📕', other: '📄',
}

const STATUS_DOT: Record<Material['status'], React.ReactNode> = {
  ready:    <span className="w-2 h-2 rounded-full bg-green-500 flex-shrink-0" title="就绪" />,
  parsing:  <span className="w-2 h-2 rounded-full bg-gray-300 animate-pulse flex-shrink-0" title="解析中" />,
  chunking: <span className="w-2 h-2 rounded-full bg-yellow-400 animate-pulse flex-shrink-0" title="分块中" />,
  error:    <span className="w-2 h-2 rounded-full bg-red-500 flex-shrink-0" title="错误" />,
}

interface MaterialItemProps {
  material: Material
  isSelected: boolean
  onClick: () => void
  onRemove: () => void
}

export const MaterialItem: React.FC<MaterialItemProps> = ({
  material, isSelected, onClick, onRemove,
}) => {
  const [hovered, setHovered] = useState(false)
  const [confirmOpen, setConfirmOpen] = useState(false)

  const displayName = material.name.length > 22 ? material.name.slice(0, 22) + '…' : material.name

  return (
    <>
      <li
        role="option"
        aria-selected={isSelected}
        tabIndex={0}
        className={`flex items-center gap-3 h-11 px-3 rounded-xl cursor-pointer transition-all duration-150 focus-visible:ring-2 focus-visible:ring-[#1A73E8] outline-none ${
          isSelected
            ? 'bg-[#E8F0FE] border-l-[3px] border-[#1A73E8]'
            : 'hover:bg-[#F1F3F4]'
        }`}
        onClick={onClick}
        onKeyDown={e => {
          if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); onClick() }
          if (e.key === 'Delete') { e.preventDefault(); setConfirmOpen(true) }
        }}
        onMouseEnter={() => setHovered(true)}
        onMouseLeave={() => setHovered(false)}
      >
        <span className="text-lg flex-shrink-0" aria-hidden="true">{PLATFORM_ICONS[material.type]}</span>
        <span className="flex-1 text-sm text-[#202124] truncate">{displayName}</span>
        {hovered ? (
          <button
            aria-label="移除材料"
            onClick={e => { e.stopPropagation(); setConfirmOpen(true) }}
            className="text-[#9AA0A6] hover:text-red-500 text-base flex-shrink-0 transition-colors duration-150 w-5 h-5 flex items-center justify-center"
          >
            ✕
          </button>
        ) : (
          <span className="flex-shrink-0">{STATUS_DOT[material.status]}</span>
        )}
      </li>

      <ConfirmModal
        open={confirmOpen}
        onClose={() => setConfirmOpen(false)}
        onConfirm={onRemove}
        message={`确认移除「${displayName}」？`}
        confirmLabel="移除"
      />
    </>
  )
}
