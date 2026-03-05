import React from 'react'
import { useStudioStore } from '../../store/studioStore'

interface TodayTasksBarProps {
  planId: string
}

export const TodayTasksBar: React.FC<TodayTasksBarProps> = ({ planId }) => {
  const { currentDay, allDays, toggleTask, completeDay, addGeneratedContent } = useStudioStore()

  if (!currentDay || allDays.length === 0) return null

  const allTasksDone = currentDay.tasks.length > 0 && currentDay.tasks.every(t => t.completed)

  const handleCompleteDay = async () => {
    completeDay(currentDay.dayNumber)
    try {
      const { allDays: latestDays, activePlanId } = useStudioStore.getState()
      const res = await fetch('/api/studio/day-summary', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          planId: planId || activePlanId,
          allDays: latestDays,
          currentDayNumber: currentDay.dayNumber,
        }),
      })
      if (res.ok) {
        const data = await res.json()
        addGeneratedContent({
          id: `day-summary-${Date.now()}`,
          type: 'day-summary',
          title: data.title || '今日总结',
          content: data.content,
          createdAt: data.createdAt || new Date().toISOString(),
        })
      }
    } catch { /* 静默 */ }
  }

  return (
    <div className="px-6 py-3 border-b border-gray-200 bg-orange-50/50">
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm font-medium text-gray-700">
          📅 Day {currentDay.dayNumber}: {currentDay.title}
        </span>
        <span className="text-xs text-gray-500">
          {currentDay.tasks.filter(t => t.completed).length}/{currentDay.tasks.length}
        </span>
      </div>
      <ul className="space-y-1">
        {currentDay.tasks.map((task, i) => (
          <li key={task.id} className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={task.completed}
              onChange={() => toggleTask(currentDay.dayNumber, i)}
              className="rounded"
            />
            <span className={`text-sm ${task.completed ? 'line-through text-gray-400' : 'text-gray-700'}`}>
              {task.title}
            </span>
          </li>
        ))}
      </ul>
      {allTasksDone && (
        <button
          onClick={handleCompleteDay}
          className="mt-2 w-full py-1.5 bg-green-500 text-white text-sm rounded-lg hover:bg-green-600 transition-colors"
        >
          ✅ 完成今日学习
        </button>
      )}
    </div>
  )
}
