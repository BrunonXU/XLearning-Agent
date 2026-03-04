import { create } from 'zustand'
import type { DayProgress, GeneratedContent, Note } from '../types'

interface StudioStore {
  allDays: DayProgress[]
  currentDay: DayProgress | null
  generatedContents: GeneratedContent[]
  notes: Note[]
  activePlanId: string
  devMode: boolean
  loading: boolean

  loadStudioData: (planId: string) => Promise<void>
  setLearningPlan: (days: DayProgress[]) => void
  toggleTask: (dayNumber: number, taskIndex: number) => void
  completeDay: (dayNumber: number) => void
  addGeneratedContent: (c: GeneratedContent) => void
  addNote: (n: Note) => void
  updateNote: (id: string, patch: Partial<Note>) => void
  deleteNote: (id: string) => void
  setDevMode: (v: boolean) => void
}

function findCurrentDay(days: DayProgress[]): DayProgress | null {
  return days.find((d) => !d.completed) ?? null
}

export const useStudioStore = create<StudioStore>()((set) => ({
  allDays: [],
  currentDay: null,
  generatedContents: [],
  notes: [],
  activePlanId: '',
  devMode: false,
  loading: false,

  loadStudioData: async (planId: string) => {
    set({ loading: true, activePlanId: planId })
    try {
      const [progressRes, contentsRes, notesRes] = await Promise.all([
        fetch(`/api/plans/${planId}/progress`),
        fetch(`/api/plans/${planId}/generated-contents`),
        fetch(`/api/plans/${planId}/notes`),
      ])
      const [progress, contents, notesData] = await Promise.all([
        progressRes.ok ? progressRes.json() : [],
        contentsRes.ok ? contentsRes.json() : [],
        notesRes.ok ? notesRes.json() : [],
      ])
      set({
        allDays: progress,
        currentDay: findCurrentDay(progress),
        generatedContents: contents,
        notes: notesData,
        loading: false,
      })
    } catch {
      set({ loading: false })
    }
  },

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
}))
