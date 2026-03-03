import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { Material, SearchResult, PlatformType } from '../types'

type PlatformStatus = 'idle' | 'searching' | 'done' | 'timeout' | 'error'

interface PlanSourceData {
  materials: Material[]
}

interface SourceStore extends PlanSourceData {
  _cache: Record<string, PlanSourceData>
  _activePlanId: string
  searchResults: SearchResult[]
  platformSearchStatus: Record<PlatformType, PlatformStatus>
  isSearching: boolean
  searchQuery: string

  setActivePlan: (planId: string) => void
  addMaterial: (m: Material) => void
  setMaterials: (mats: Material[]) => void
  removeMaterial: (id: string) => void
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

const emptySource: PlanSourceData = { materials: [] }

function snapshot(s: SourceStore): PlanSourceData {
  return { materials: s.materials }
}

export const useSourceStore = create<SourceStore>()(
  persist(
    (set) => ({
      ...emptySource,
      _cache: {},
      _activePlanId: '',
      searchResults: [],
      platformSearchStatus: { ...DEFAULT_PLATFORM_STATUS },
      isSearching: false,
      searchQuery: '',

      setActivePlan: (planId) => set((s) => {
        const cache = { ...s._cache }
        if (s._activePlanId) cache[s._activePlanId] = snapshot(s as unknown as SourceStore)
        const restored = cache[planId] || emptySource
        return { ...restored, _cache: cache, _activePlanId: planId }
      }),

      addMaterial: (m) =>
        set((s) => ({ materials: [...s.materials, m] })),

      setMaterials: (mats) => set({ materials: mats }),

      removeMaterial: (id) =>
        set((s) => ({ materials: s.materials.filter((m) => m.id !== id) })),

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
    }),
    {
      name: 'source-store',
      partialize: (s) => ({
        _cache: (() => {
          const cache = { ...s._cache }
          if (s._activePlanId) cache[s._activePlanId] = snapshot(s as unknown as SourceStore)
          return cache
        })(),
        _activePlanId: s._activePlanId,
        materials: s.materials,
      }),
    }
  )
)
