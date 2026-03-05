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

/** 将平铺的内容列表按 type 合并，同类型保留最新为当前版本，旧的存入 versions */
function mergeContentsByType(items: GeneratedContent[]): GeneratedContent[] {
  const grouped = new Map<string, GeneratedContent[]>()
  for (const item of items) {
    const list = grouped.get(item.type) || []
    list.push(item)
    grouped.set(item.type, list)
  }
  const result: GeneratedContent[] = []
  for (const [, list] of grouped) {
    // 按时间倒序（最新在前）
    list.sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime())
    const [latest, ...older] = list
    const versions = older.map((item, i) => ({
      content: item.content,
      createdAt: item.createdAt,
      version: older.length - i,
    }))
    result.push({
      ...latest,
      version: list.length,
      versions,
    })
  }
  // 按最新 createdAt 排序
  result.sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime())
  return result
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
        generatedContents: mergeContentsByType(contents),
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

  addGeneratedContent: (c) => set((s) => {
    const existing = s.generatedContents.find((g) => g.type === c.type)
    if (existing) {
      // 合并：旧版本存入 versions，新内容替换当前
      const oldVersions = existing.versions || []
      const oldVersion = {
        content: existing.content,
        createdAt: existing.createdAt,
        version: existing.version || 1,
      }
      const newVersion = (existing.version || 1) + 1
      const merged = {
        ...existing,
        content: c.content,
        title: c.title,
        createdAt: c.createdAt,
        version: newVersion,
        versions: [oldVersion, ...oldVersions],
      }
      return {
        generatedContents: s.generatedContents.map((g) => g.type === c.type ? merged : g),
      }
    }
    // 新类型：直接添加
    return { generatedContents: [{ ...c, version: 1, versions: [] }, ...s.generatedContents] }
  }),
  addNote: (n) => set((s) => ({ notes: [n, ...s.notes] })),
  updateNote: (id, patch) => set((s) => ({ notes: s.notes.map((n) => n.id === id ? { ...n, ...patch } : n) })),
  deleteNote: (id) => set((s) => ({ notes: s.notes.filter((n) => n.id !== id) })),
  setDevMode: (v) => set({ devMode: v }),
}))
