import { create } from 'zustand'
import type { SearchHistoryEntry, SearchResult } from '../types'

interface SearchStore {
  history: SearchHistoryEntry[]
  resultDetailMap: Record<string, SearchResult>
  loading: boolean

  loadHistory: (planId: string) => Promise<void>
  addEntry: (planId: string, entry: SearchHistoryEntry) => void
  clearHistory: (planId: string) => Promise<void>
  saveResultDetails: (results: SearchResult[]) => void
  getResultDetail: (materialId: string) => SearchResult | undefined
}

export const useSearchStore = create<SearchStore>()((set, get) => ({
  history: [],
  resultDetailMap: {},
  loading: false,

  loadHistory: async (planId: string) => {
    set({ loading: true })
    try {
      const res = await fetch(`/api/plans/${planId}/search-history`)
      if (!res.ok) throw new Error('加载失败')
      const data = await res.json()
      const map: Record<string, SearchResult> = {}
      data.forEach((entry: SearchHistoryEntry) => {
        entry.results.forEach((r: SearchResult) => { map[r.id] = r })
      })
      set({ history: data, resultDetailMap: map, loading: false })
    } catch {
      set({ loading: false })
    }
  },

  addEntry: (planId, entry) => {
    // 先更新本地状态
    set((s) => {
      const map = { ...s.resultDetailMap }
      entry.results.forEach((r) => { map[r.id] = r })
      return {
        history: [entry, ...s.history].slice(0, 20),
        resultDetailMap: map,
      }
    })
    // 异步保存到后端
    fetch(`/api/plans/${planId}/search-history`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(entry),
    }).catch(() => { /* 静默失败 */ })
  },

  clearHistory: async (planId) => {
    set({ history: [], resultDetailMap: {} })
    try {
      await fetch(`/api/plans/${planId}/search-history`, { method: 'DELETE' })
    } catch { /* 静默失败 */ }
  },

  saveResultDetails: (results) =>
    set((s) => {
      const map = { ...s.resultDetailMap }
      results.forEach((r) => { map[r.id] = r })
      return { resultDetailMap: map }
    }),

  getResultDetail: (id) => get().resultDetailMap[id],
}))
