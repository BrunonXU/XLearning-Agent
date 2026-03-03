import { create } from 'zustand'
import type { Material, SearchResult, PlatformType } from '../types'

type PlatformStatus = 'idle' | 'searching' | 'done' | 'timeout' | 'error'

interface SourceStore {
  materials: Material[]
  searchResults: SearchResult[]
  platformSearchStatus: Record<PlatformType, PlatformStatus>
  isSearching: boolean
  searchQuery: string

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

export const useSourceStore = create<SourceStore>((set) => ({
  materials: [],
  searchResults: [],
  platformSearchStatus: { ...DEFAULT_PLATFORM_STATUS },
  isSearching: false,
  searchQuery: '',

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
}))
