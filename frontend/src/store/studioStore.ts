import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { DayProgress, GeneratedContent, Note } from '../types'

interface StudioStore {
  allDays: DayProgress[]
  currentDay: DayProgress | null
  generatedContents: GeneratedContent[]
  notes: Note[]
  devMode: boolean
  langGraphEnabled: boolean

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

/** 找到第一个未完成的 Day */
function findCurrentDay(days: DayProgress[]): DayProgress | null {
  return days.find((d) => !d.completed) ?? null
}

export const useStudioStore = create<StudioStore>()(
  persist(
    (set) => ({
      allDays: [],
      currentDay: null,
      generatedContents: [],
      notes: [],
      devMode: false,
      langGraphEnabled: false,

      setLearningPlan: (days) =>
        set({ allDays: days, currentDay: findCurrentDay(days) }),

      toggleTask: (dayNumber, taskIndex) =>
        set((s) => {
          const allDays = s.allDays.map((d) => {
            if (d.dayNumber !== dayNumber) return d
            const tasks = d.tasks.map((t, i) =>
              i === taskIndex ? { ...t, completed: !t.completed } : t
            )
            return { ...d, tasks }
          })
          return { allDays, currentDay: findCurrentDay(allDays) }
        }),

      completeDay: (dayNumber) =>
        set((s) => {
          const allDays = s.allDays.map((d) =>
            d.dayNumber === dayNumber ? { ...d, completed: true } : d
          )
          return { allDays, currentDay: findCurrentDay(allDays) }
        }),

      addGeneratedContent: (c) =>
        set((s) => ({
          generatedContents: [c, ...s.generatedContents],
        })),

      addNote: (n) =>
        set((s) => ({ notes: [n, ...s.notes] })),

      updateNote: (id, patch) =>
        set((s) => ({
          notes: s.notes.map((n) => (n.id === id ? { ...n, ...patch } : n)),
        })),

      deleteNote: (id) =>
        set((s) => ({ notes: s.notes.filter((n) => n.id !== id) })),

      setDevMode: (v) => set({ devMode: v }),
      setLangGraphEnabled: (v) => set({ langGraphEnabled: v }),
    }),
    {
      name: 'studio-store',
      partialize: (s) => ({
        allDays: s.allDays,
        currentDay: s.currentDay,
        generatedContents: s.generatedContents,
        notes: s.notes,
        devMode: s.devMode,
        langGraphEnabled: s.langGraphEnabled,
      }),
    }
  )
)
