import React, { useState } from 'react'
import { createPortal } from 'react-dom'
import type { LearnerProfile } from '../../types'

interface Props {
  initial?: LearnerProfile | null
  onSave: (profile: LearnerProfile) => void
  onSkip: () => void
}

const LEVEL_OPTIONS = ['零基础', '入门级', '有一定基础', '中级', '高级']
const DURATION_OPTIONS = ['1周', '2周', '1个月', '2个月', '3个月', '半年']
const HOURS_OPTIONS = ['30分钟以内', '1小时', '2小时', '3小时以上']

export const LearnerProfileModal: React.FC<Props> = ({ initial, onSave, onSkip }) => {
  const [goal, setGoal] = useState(initial?.goal || '')
  const [duration, setDuration] = useState(initial?.duration || '')
  const [level, setLevel] = useState(initial?.level || '')
  const [background, setBackground] = useState(initial?.background || '')
  const [dailyHours, setDailyHours] = useState(initial?.dailyHours || '')

  const handleSave = () => {
    onSave({ goal, duration, level, background, dailyHours })
  }

  const canSave = goal.trim() || level.trim()

  return createPortal(
    <div className="fixed inset-0 z-[9999] flex items-center justify-center bg-black/40" onClick={onSkip}>
      <div className="bg-white dark:bg-dark-surface rounded-2xl shadow-2xl w-[520px] max-h-[85vh] overflow-y-auto"
        onClick={e => e.stopPropagation()}>
        {/* Header */}
        <div className="px-6 pt-6 pb-2">
          <h2 className="text-lg font-semibold text-[#202124]">📋 学习者画像</h2>
          <p className="text-sm text-gray-500 mt-1">
            填写你的学习背景，AI 将为你生成个性化内容
          </p>
        </div>

        <div className="px-6 py-4 space-y-5">
          {/* 学习目的 */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">🎯 学习目的</label>
            <textarea value={goal} onChange={e => setGoal(e.target.value)}
              placeholder="例如：准备考研、转行学编程、提升工作技能..."
              className="w-full px-3 py-2.5 border border-gray-300 rounded-xl text-sm resize-none focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              rows={2} />
          </div>

          {/* 当前水平 */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">📊 当前水平</label>
            <div className="flex flex-wrap gap-2">
              {LEVEL_OPTIONS.map(opt => (
                <button key={opt} onClick={() => setLevel(opt)}
                  className={`px-3 py-1.5 rounded-full text-sm border transition-all ${
                    level === opt
                      ? 'bg-orange-50 border-blue-400 text-orange-700'
                      : 'border-gray-300 text-gray-600 hover:border-gray-400'
                  }`}>{opt}</button>
              ))}
            </div>
          </div>

          {/* 学习周期 */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">📅 学习周期</label>
            <div className="flex flex-wrap gap-2">
              {DURATION_OPTIONS.map(opt => (
                <button key={opt} onClick={() => setDuration(opt)}
                  className={`px-3 py-1.5 rounded-full text-sm border transition-all ${
                    duration === opt
                      ? 'bg-green-50 border-green-400 text-green-700'
                      : 'border-gray-300 text-gray-600 hover:border-gray-400'
                  }`}>{opt}</button>
              ))}
            </div>
          </div>

          {/* 每日可用时间 */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">⏰ 每日可用时间</label>
            <div className="flex flex-wrap gap-2">
              {HOURS_OPTIONS.map(opt => (
                <button key={opt} onClick={() => setDailyHours(opt)}
                  className={`px-3 py-1.5 rounded-full text-sm border transition-all ${
                    dailyHours === opt
                      ? 'bg-orange-50 border-orange-400 text-orange-700'
                      : 'border-gray-300 text-gray-600 hover:border-gray-400'
                  }`}>{opt}</button>
              ))}
            </div>
          </div>

          {/* 个人背景 */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">💼 个人背景（选填）</label>
            <textarea value={background} onChange={e => setBackground(e.target.value)}
              placeholder="例如：大三计算机专业、在职产品经理、自学爱好者..."
              className="w-full px-3 py-2.5 border border-gray-300 rounded-xl text-sm resize-none focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              rows={2} />
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 py-4 flex justify-end gap-3 border-t border-gray-100">
          <button onClick={onSkip}
            className="px-4 py-2 text-sm text-gray-500 hover:text-gray-700 transition-colors">
            跳过
          </button>
          <button onClick={handleSave} disabled={!canSave}
            className={`px-5 py-2 rounded-full text-sm font-medium transition-all ${
              canSave
                ? 'bg-blue-600 text-white hover:bg-blue-700'
                : 'bg-gray-200 text-gray-400 cursor-not-allowed'
            }`}>
            保存并继续
          </button>
        </div>
      </div>
    </div>,
    document.body
  )
}
