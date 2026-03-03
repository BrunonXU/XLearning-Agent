import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { DayProgress, GeneratedContent, Note } from '../types'

interface PlanData {
  allDays: DayProgress[]
  currentDay: DayProgress | null
  generatedContents: GeneratedContent[]
  notes: Note[]
}

interface StudioStore extends PlanData {
  /** planId -> 保存的数据 */
  _cache: Record<string, PlanData>
  _activePlanId: string
  activePlanId: string
  devMode: boolean
  langGraphEnabled: boolean

  setActivePlan: (planId: string) => void
  setLearningPlan: (days: DayProgress[]) => void
  toggleTask: (dayNumber: number, taskIndex: number) => void
  completeDay: (dayNumber: number) => void
  addGeneratedContent: (c: GeneratedContent) => void
  addNote: (n: Note) => void
  updateNote: (id: string, patch: Partial<Note>) => void
  deleteNote: (id: string) => void
  setDevMode: (v: boolean) => void
  setLangGraphEnabled: (v: boolean) => void
}

function findCurrentDay(days: DayProgress[]): DayProgress | null {
  return days.find((d) => !d.completed) ?? null
}

const emptyPlan: PlanData = { allDays: [], currentDay: null, generatedContents: [], notes: [] }

/** 从当前 state 提取 PlanData */
function snapshot(s: StudioStore): PlanData {
  return { allDays: s.allDays, currentDay: s.currentDay, generatedContents: s.generatedContents, notes: s.notes }
}

export const useStudioStore = create<StudioStore>()(
  persist(
    (set, get) => ({
      ...emptyPlan,
      _cache: {},
      _activePlanId: '',
      activePlanId: '',
      devMode: false,
      langGraphEnabled: false,

      setActivePlan: (planId) => set((s) => {
        // 保存当前 plan 数据到 cache
        const cache = { ...s._cache }
        if (s._activePlanId) cache[s._activePlanId] = snapshot(s)
        // 恢复目标 plan 数据
        const restored = cache[planId] || emptyPlan
        return { ...restored, _cache: cache, _activePlanId: planId, activePlanId: planId }
      }),

      setLearningPlan: (days) => set({ allDays: days, currentDay: findCurrentDay(days) }),

      toggleTask: (dayNumber, taskIndex) => set((s) => {
        const allDays = s.allDays.map((d) => {
          if (d.dayNumber !== dayNumber) return d
          const tasks = d.tasks.map((t, i) => i === taskIndex ? { ...t, completed: !t.completed } : t)
          return { ...d, tasks }
        })
        return { allDays, currentDay: findCurrentDay(allDays) }
      }),

      completeDay: (dayNumber) => set((s) => {
        const allDays = s.allDays.map((d) => d.dayNumber === dayNumber ? { ...d, completed: true } : d)
        return { allDays, currentDay: findCurrentDay(allDays) }
      }),

      addGeneratedContent: (c) => set((s) => ({ generatedContents: [c, ...s.generatedContents] })),
      addNote: (n) => set((s) => ({ notes: [n, ...s.notes] })),
      updateNote: (id, patch) => set((s) => ({ notes: s.notes.map((n) => n.id === id ? { ...n, ...patch } : n) })),
      deleteNote: (id) => set((s) => ({ notes: s.notes.filter((n) => n.id !== id) })),
      setDevMode: (v) => set({ devMode: v }),
      setLangGraphEnabled: (v) => set({ langGraphEnabled: v }),
    }),
    {
      name: 'studio-store',
      partialize: (s) => ({
        _cache: (() => {
          // 保存时把当前数据也写入 cache
          const cache = { ...s._cache }
          if (s._activePlanId) cache[s._activePlanId] = snapshot(s as unknown as StudioStore)
          return cache
        })(),
        _activePlanId: s._activePlanId,
        activePlanId: s._activePlanId,
        devMode: s.devMode,
        langGraphEnabled: s.langGraphEnabled,
        // 也保存顶层字段（兼容）
        allDays: s.allDays,
        currentDay: s.currentDay,
        generatedContents: s.generatedContents,
        notes: s.notes,
      }),
    }
  )
)
