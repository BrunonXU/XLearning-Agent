import React from 'react'
import { useNavigate } from 'react-router-dom'
import type { LearningPlan } from '../../types'

// 渐变封面色，更有视觉冲击力
const COVER_GRADIENTS = [
  'from-orange-400 to-indigo-600',
  'from-orange-400 to-red-500',
  'from-emerald-400 to-teal-600',
  'from-purple-400 to-pink-500',
]

const FEATURED: LearningPlan[] = [
  { id: 'f1', title: 'Transformer 架构精讲', sourceCount: 16, lastAccessedAt: '2026-03-01T00:00:00Z', coverColor: '', totalDays: 7, completedDays: 0 },
  { id: 'f2', title: 'Python 异步编程实战', sourceCount: 8, lastAccessedAt: '2026-02-28T00:00:00Z', coverColor: '', totalDays: 5, completedDays: 0 },
  { id: 'f3', title: 'LangChain 从入门到精通', sourceCount: 13, lastAccessedAt: '2026-02-20T00:00:00Z', coverColor: '', totalDays: 10, completedDays: 0 },
  { id: 'f4', title: '强化学习基础', sourceCount: 5, lastAccessedAt: '2026-02-15T00:00:00Z', coverColor: '', totalDays: 6, completedDays: 0 },
]

export const FeaturedPlans: React.FC = () => {
  const navigate = useNavigate()

  return (
    <section>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-base font-semibold text-[#202124]">精选学习规划</h2>
        <button className="text-sm text-[#D97757] hover:underline">查看全部 ▶</button>
      </div>
      <div className="flex gap-4 overflow-x-auto pb-2 scrollbar-thin">
        {FEATURED.map((plan, i) => (
          <div
            key={plan.id}
            className="flex-shrink-0 w-[240px] rounded-3xl overflow-hidden border border-black/5 shadow-soft hover:shadow-md hover:-translate-y-1 transition-all duration-200 cursor-pointer group bg-white"
            onClick={() => navigate(`/workspace/${plan.id}`)}
          >
            {/* 渐变封面 */}
            <div className={`h-[120px] bg-gradient-to-br ${COVER_GRADIENTS[i % COVER_GRADIENTS.length]} flex items-end p-3`}>
              <span className="text-white text-sm font-semibold leading-tight drop-shadow">
                {plan.title}
              </span>
            </div>
            {/* 信息区 */}
            <div className="bg-white px-5 py-4 flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-[#5F6368] mb-0.5">{plan.sourceCount} 个来源</p>
                <p className="text-sm text-[#9AA0A6]">
                  {new Date(plan.lastAccessedAt).toLocaleDateString('zh-CN')}
                </p>
              </div>
              <span className="text-[#9AA0A6] text-lg">🌐</span>
            </div>
          </div>
        ))}
      </div>
    </section>
  )
}
