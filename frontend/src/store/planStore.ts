import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { LearningPlan } from '../types'

interface PlanStore {
  plans: LearningPlan[]
  currentPlanId: string | null

  setPlans: (plans: LearningPlan[]) => void
  addPlan: (plan: LearningPlan) => void
  updatePlan: (id: string, patch: Partial<LearningPlan>) => void
  deletePlan: (id: string) => void
  setCurrentPlan: (id: string | null) => void
  getCurrentPlan: () => LearningPlan | null
}

export const usePlanStore = create<PlanStore>()(
  persist(
    (set, get) => ({
      plans: [],
      currentPlanId: null,

      setPlans: (plans) => set({ plans }),

      addPlan: (plan) =>
        set((s) => ({ plans: [...s.plans, plan] })),

      updatePlan: (id, patch) =>
        set((s) => ({
          plans: s.plans.map((p) => (p.id === id ? { ...p, ...patch } : p)),
        })),

      deletePlan: (id) =>
        set((s) => ({
          plans: s.plans.filter((p) => p.id !== id),
          currentPlanId: s.currentPlanId === id ? null : s.currentPlanId,
        })),

      setCurrentPlan: (id) => set({ currentPlanId: id }),

      getCurrentPlan: () => {
        const { plans, currentPlanId } = get()
        return plans.find((p) => p.id === currentPlanId) ?? null
      },
    }),
    {
      name: 'plan-store',
    }
  )
)
