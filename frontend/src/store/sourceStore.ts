import { create } from 'zustand'
import type { Material, SearchResult, PlatformType } from '../types'

type PlatformStatus = 'idle' | 'searching' | 'done' | 'timeout' | 'error'

interface SourceStore {
  materials: Material[]
  searchResults: SearchResult[]
  platformSearchStatus: Record<PlatformType, PlatformStatus>
  isSearching: boolean
  searchQuery: string
  loading: boolean

  loadMaterials: (planId: string) => Promise<void>
  addMaterial: (m: Material) => void
  setMaterials: (mats: Material[]) => void
  removeMaterial: (id: string) => void
  updateMaterial: (id: string, updates: Partial<Material>) => void
  updateMaterialStatus: (id: string, status: Material['status']) => void
  setSearchResults: (results: SearchResult[]) => void
  setPlatformStatus: (platform: PlatformType, status: PlatformStatus) => void
  setSearching: (v: boolean) => void
  setSearchQuery: (q: string) => void
  clearSearch: () => void
}

const DEFAULT_PLATFORM_STATUS: Record<PlatformType, PlatformStatus> = {
  bilibili: 'idle',
  youtube: 'idle',
  github: 'idle',
  xiaohongshu: 'idle',
  google: 'idle',
  other: 'idle',
}

export const useSourceStore = create<SourceStore>()((set) => ({
  materials: [],
  searchResults: [],
  platformSearchStatus: { ...DEFAULT_PLATFORM_STATUS },
  isSearching: false,
  searchQuery: '',
  loading: false,

  loadMaterials: async (planId: string) => {
    set({ loading: true })
    try {
      const res = await fetch(`/api/plans/${planId}/materials`)
      if (!res.ok) throw new Error('加载失败')
      const data = await res.json()
      // 从 extraData 恢复搜索来源材料的详情到 searchStore
      const searchDetails: SearchResult[] = []
      for (const m of data) {
        if (m.url && m.extraData && Object.keys(m.extraData).length > 0) {
          searchDetails.push({
            id: m.id,
            title: m.name,
            url: m.url,
            platform: m.type,
            description: m.extraData.description ?? '',
            qualityScore: m.extraData.qualityScore ?? 0,
            recommendationReason: m.extraData.recommendationReason ?? '',
            contentSummary: m.extraData.contentSummary,
            commentSummary: m.extraData.commentSummary,
            engagementMetrics: m.extraData.engagementMetrics,
            imageUrls: m.extraData.imageUrls,
            topComments: m.extraData.topComments,
          })
        }
      }
      if (searchDetails.length > 0) {
        const { useSearchStore } = await import('./searchStore')
        useSearchStore.getState().saveResultDetails(searchDetails)
      }
      set({ materials: data, loading: false })
    } catch {
      set({ loading: false })
    }
  },

  addMaterial: (m) =>
    set((s) => ({ materials: [...s.materials, m] })),

  setMaterials: (mats) => set({ materials: mats }),

  removeMaterial: (id) =>
    set((s) => ({ materials: s.materials.filter((m) => m.id !== id) })),

  updateMaterial: (id, updates) =>
    set((s) => ({
      materials: s.materials.map((m) => (m.id === id ? { ...m, ...updates } : m)),
    })),

  updateMaterialStatus: (id, status) =>
    set((s) => ({
      materials: s.materials.map((m) => (m.id === id ? { ...m, status } : m)),
    })),

  setSearchResults: (results) => set({ searchResults: results }),

  setPlatformStatus: (platform, status) =>
    set((s) => ({
      platformSearchStatus: { ...s.platformSearchStatus, [platform]: status },
    })),

  setSearching: (v) => set({ isSearching: v }),
  setSearchQuery: (q) => set({ searchQuery: q }),

  clearSearch: () =>
    set({
      searchResults: [],
      platformSearchStatus: { ...DEFAULT_PLATFORM_STATUS },
      isSearching: false,
      searchQuery: '',
    }),
}))
