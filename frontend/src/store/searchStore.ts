import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { SearchHistoryEntry, SearchResult } from '../types'

interface SearchStore {
  history: SearchHistoryEntry[]
  resultDetailMap: Record<string, SearchResult>
  addEntry: (entry: SearchHistoryEntry) => void
  clearHistory: () => void
  saveResultDetails: (results: SearchResult[]) => void
  getResultDetail: (materialId: string) => SearchResult | undefined
}

export const useSearchStore = create<SearchStore>()(
  persist(
    (set, get) => ({
      history: [],
      resultDetailMap: {},
      addEntry: (entry) =>
        set((s) => ({
          history: [entry, ...s.history].slice(0, 20),
        })),
      clearHistory: () => set({ history: [], resultDetailMap: {} }),
      saveResultDetails: (results) =>
        set((s) => {
          const map = { ...s.resultDetailMap }
          results.forEach((r) => {
            map[r.id] = r
          })
          return { resultDetailMap: map }
        }),
      getResultDetail: (id) => get().resultDetailMap[id],
    }),
    { name: 'search-history' }
  )
)
