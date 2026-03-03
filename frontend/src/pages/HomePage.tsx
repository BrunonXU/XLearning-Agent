import React, { useState, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { FeaturedPlans } from '../components/home/FeaturedPlans'
import { PlanCard } from '../components/home/PlanCard'
import { NewPlanModal } from '../components/home/NewPlanModal'
import { usePlanStore } from '../store/planStore'
import { useKeyboard } from '../hooks/useKeyboard'
import type { LearningPlan } from '../types'

type ViewMode = 'grid' | 'list'
type FilterTab = 'all' | 'featured'
type CreateMode = 'pdf' | 'link' | 'topic' | null

const COVER_COLORS = [
  'from-blue-400 to-indigo-600',
  'from-orange-400 to-pink-500',
  'from-green-400 to-teal-500',
  'from-purple-400 to-violet-600',
  'from-rose-400 to-red-500',
  'from-cyan-400 to-blue-500',
]

const HomePage: React.FC = () => {
  const navigate = useNavigate()
  const { plans, setPlans, addPlan, updatePlan, deletePlan } = usePlanStore()
  const [viewMode, setViewMode] = useState<ViewMode>('grid')
  const [filterTab, setFilterTab] = useState<FilterTab>('all')
  const [modalOpen, setModalOpen] = useState(false)
  const [renamingId, setRenamingId] = useState<string | null>(null)
  const [renameValue, setRenameValue] = useState('')
  const [isLoading, setIsLoading] = useState(true)

  // 10.1: 从后端加载规划列表
  useEffect(() => {
    fetch('/api/plans')
      .then(r => r.ok ? r.json() : [])
      .then((data: LearningPlan[]) => {
        if (data.length > 0) setPlans(data)
      })
      .catch(() => { /* 使用 store 中的缓存数据 */ })
      .finally(() => setIsLoading(false))
  }, [])

  // 10.3: 新建规划
  const handleCreate = async (title: string, _mode: CreateMode, _input: string) => {
    try {
      const res = await fetch('/api/plans', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title: title || '新建学习规划' }),
      })
      if (res.ok) {
        const plan: LearningPlan = await res.json()
        addPlan(plan)
        navigate(`/workspace/${plan.id}`)
        return
      }
    } catch { /* 降级 */ }
    // 降级：本地创建
    const colorIdx = plans.length % COVER_COLORS.length
    const newPlan: LearningPlan = {
      id: `local-${Date.now()}`,
      title: title || '新建学习规划',
      sourceCount: 0,
      lastAccessedAt: new Date().toISOString(),
      coverColor: COVER_COLORS[colorIdx],
      totalDays: 0,
      completedDays: 0,
    }
    addPlan(newPlan)
    navigate(`/workspace/${newPlan.id}`)
  }

  // 10.4: 删除规划
  const handleDelete = async (id: string) => {
    deletePlan(id)
    try { await fetch(`/api/plans/${id}`, { method: 'DELETE' }) } catch { /* 静默 */ }
  }

  // 10.4: 重命名
  const handleRename = (id: string) => {
    const plan = plans.find(p => p.id === id)
    if (!plan) return
    setRenamingId(id)
    setRenameValue(plan.title)
  }

  const commitRename = async () => {
    if (!renamingId || !renameValue.trim()) { setRenamingId(null); return }
    updatePlan(renamingId, { title: renameValue.trim() })
    try {
      await fetch(`/api/plans/${renamingId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title: renameValue.trim() }),
      })
    } catch { /* 静默 */ }
    setRenamingId(null)
  }

  // 11.1: Ctrl+N 新建规划，Escape 关闭弹窗
  useKeyboard({
    onNewPlan: useCallback(() => setModalOpen(true), []),
    onEscape: useCallback(() => { setModalOpen(false); setRenamingId(null) }, []),
  })

  const sortedPlans = [...plans].sort(
    (a, b) => new Date(b.lastAccessedAt).getTime() - new Date(a.lastAccessedAt).getTime()
  )

  return (
    <div className="min-h-screen bg-white dark:bg-dark-bg">
      {/* 顶部导航 */}
      <header className="h-14 border-b border-[#DADCE0] dark:border-dark-border flex items-center px-6 justify-between bg-white dark:bg-dark-bg">
        <div className="flex items-center gap-2">
          <span className="text-xl" aria-hidden="true">⚛</span>
          <span className="text-lg font-semibold text-[#202124] dark:text-dark-text">XLearning</span>
        </div>
        <div className="flex items-center gap-2">
          <button aria-label="设置" className="w-8 h-8 flex items-center justify-center rounded-full text-[#5F6368] hover:bg-[#F1F3F4] transition-colors duration-150">⚙️</button>
          <button aria-label="用户头像" className="w-8 h-8 rounded-full bg-[#1A73E8] text-white text-sm font-medium flex items-center justify-center">U</button>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-6 py-6">
        {/* 10.2: 精选规划横向滚动 */}
        <div className="mb-8">
          <FeaturedPlans />
        </div>

        {/* 筛选栏 + 视图切换 */}
        <div className="flex items-center justify-between mb-5">
          <div className="flex gap-1 border-b border-[#DADCE0]">
            {(['all', 'featured'] as FilterTab[]).map(tab => (
              <button
                key={tab}
                onClick={() => setFilterTab(tab)}
                className={`px-4 py-2 text-sm transition-all duration-150 ${
                  filterTab === tab
                    ? 'border-b-2 border-[#1A73E8] text-[#1A73E8] font-medium'
                    : 'text-[#5F6368] hover:text-[#202124]'
                }`}
              >
                {tab === 'all' ? '全部' : '精选笔记本'}
              </button>
            ))}
          </div>
          <div className="flex items-center gap-2">
            {/* 10.6: 网格/列表视图切换 */}
            <button
              onClick={() => setViewMode('grid')}
              aria-label="网格视图"
              aria-pressed={viewMode === 'grid'}
              className={`px-2 py-1 rounded text-sm transition-colors duration-150 ${viewMode === 'grid' ? 'text-[#1A73E8]' : 'text-[#5F6368] hover:text-[#202124]'}`}
            >
              ⊞ 网格
            </button>
            <button
              onClick={() => setViewMode('list')}
              aria-label="列表视图"
              aria-pressed={viewMode === 'list'}
              className={`px-2 py-1 rounded text-sm transition-colors duration-150 ${viewMode === 'list' ? 'text-[#1A73E8]' : 'text-[#5F6368] hover:text-[#202124]'}`}
            >
              ≡ 列表
            </button>
            <button
              onClick={() => setModalOpen(true)}
              className="ml-2 bg-[#1A73E8] text-white rounded-lg px-4 py-2 text-sm font-medium hover:bg-[#1557B0] active:scale-95 transition-all duration-150"
            >
              + 新建
            </button>
          </div>
        </div>

        {/* 10.5: 空状态 / 规划列表 */}
        {isLoading ? (
          <div className="grid grid-cols-4 gap-4">
            {[1, 2, 3, 4].map(i => (
              <div key={i} className="h-[180px] rounded-xl bg-[#F1F3F4] animate-pulse" />
            ))}
          </div>
        ) : sortedPlans.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-24 text-center">
            <span className="text-6xl mb-4" aria-hidden="true">📖</span>
            <p className="text-[#5F6368] mb-6 text-base">还没有学习规划，创建第一个吧</p>
            <button
              onClick={() => setModalOpen(true)}
              className="bg-[#1A73E8] text-white rounded-lg px-6 py-2.5 text-sm font-medium hover:bg-[#1557B0] transition-colors duration-150"
            >
              + 新建学习规划
            </button>
          </div>
        ) : (
          <section>
            <h2 className="text-sm font-semibold text-[#202124] dark:text-dark-text mb-3">
              最近打开的学习规划
            </h2>
            <div className={viewMode === 'grid' ? 'grid grid-cols-4 gap-4' : 'flex flex-col gap-2'}>
              {/* 新建卡片 */}
              <button
                onClick={() => setModalOpen(true)}
                className="h-[180px] rounded-xl border-2 border-dashed border-[#DADCE0] hover:border-[#1A73E8] hover:bg-[#E8F0FE]/30 transition-all duration-150 flex flex-col items-center justify-center gap-2 text-[#5F6368] hover:text-[#1A73E8]"
                aria-label="新建学习规划"
              >
                <span className="text-3xl" aria-hidden="true">+</span>
                <span className="text-sm font-medium">新建学习规划</span>
              </button>

              {sortedPlans.map(plan => (
                renamingId === plan.id ? (
                  // 内联重命名
                  <div key={plan.id} className="rounded-xl border-2 border-[#1A73E8] p-3 flex flex-col justify-center bg-white">
                    <input
                      autoFocus
                      value={renameValue}
                      onChange={e => setRenameValue(e.target.value)}
                      onBlur={commitRename}
                      onKeyDown={e => { if (e.key === 'Enter') commitRename(); if (e.key === 'Escape') setRenamingId(null) }}
                      className="text-sm font-semibold text-[#202124] border-b border-[#1A73E8] outline-none bg-transparent"
                      aria-label="重命名规划"
                    />
                    <p className="text-xs text-[#5F6368] mt-1">按 Enter 确认，Esc 取消</p>
                  </div>
                ) : (
                  <PlanCard
                    key={plan.id}
                    plan={plan}
                    onRename={handleRename}
                    onDelete={handleDelete}
                  />
                )
              ))}
            </div>
          </section>
        )}
      </main>

      {/* 10.3: 新建规划弹窗 */}
      <NewPlanModal
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        onCreate={handleCreate}
      />
    </div>
  )
}

export default HomePage
