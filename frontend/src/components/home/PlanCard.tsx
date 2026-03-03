import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import type { LearningPlan } from '../../types'

const COVER_COLORS = [
  '#E8F0FE', '#FFF7ED', '#F0FDF4', '#FDF4FF', '#FFF1F2', '#F0F9FF',
]
const COVER_ICONS = ['📚', '🧠', '💡', '🔬', '🎯', '⚡']

interface PlanCardProps {
  plan: LearningPlan
  onRename: (id: string) => void
  onDelete: (id: string) => void
}

export const PlanCard: React.FC<PlanCardProps> = ({ plan, onRename, onDelete }) => {
  const navigate = useNavigate()
  const [menuOpen, setMenuOpen] = useState(false)
  const idx = parseInt(plan.id, 36) % COVER_COLORS.length
  const coverColor = COVER_COLORS[idx] ?? COVER_COLORS[0]
  const coverIcon = COVER_ICONS[idx] ?? '📚'

  const formatDate = (iso: string) =>
    new Date(iso).toLocaleDateString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit' })

  return (
    <div
      className="relative rounded-xl border border-[#DADCE0] hover:shadow-lg hover:-translate-y-0.5 transition-all duration-150 cursor-pointer overflow-hidden group bg-white"
      onClick={() => navigate(`/workspace/${plan.id}`)}
    >
      {/* 封面色块 */}
      <div
        className="h-[110px] flex items-center justify-center"
        style={{ backgroundColor: coverColor }}
      >
        <span className="text-5xl opacity-60">{coverIcon}</span>
      </div>

      {/* 信息区 */}
      <div className="px-3 py-3">
        <p className="text-sm font-semibold text-[#202124] truncate mb-1">{plan.title}</p>
        <p className="text-xs text-[#5F6368]">
          {plan.sourceCount} 个来源 · {formatDate(plan.lastAccessedAt)}
        </p>
      </div>

      {/* 三点菜单 */}
      <button
        aria-label="更多操作"
        className="absolute top-2 right-2 w-8 h-8 rounded-full bg-white/90 shadow-sm flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity duration-150 hover:bg-white text-[#5F6368]"
        onClick={e => { e.stopPropagation(); setMenuOpen(m => !m) }}
      >
        ⋮
      </button>

      {menuOpen && (
        <div
          className="absolute top-11 right-2 bg-white rounded-xl shadow-xl border border-[#DADCE0] z-10 py-1 min-w-[110px]"
          onClick={e => e.stopPropagation()}
        >
          {[
            { label: '打开', action: () => navigate(`/workspace/${plan.id}`) },
            { label: '重命名', action: () => { onRename(plan.id); setMenuOpen(false) } },
            { label: '删除', action: () => { onDelete(plan.id); setMenuOpen(false) }, danger: true },
          ].map(item => (
            <button
              key={item.label}
              onClick={item.action}
              className={`w-full text-left px-4 py-2 text-sm hover:bg-[#F1F3F4] transition-colors duration-150 ${item.danger ? 'text-red-500' : 'text-[#202124]'}`}
            >
              {item.label}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
