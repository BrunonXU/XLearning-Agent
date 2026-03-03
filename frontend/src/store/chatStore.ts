import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { ChatMessage } from '../types'

interface PlanChatData {
  messages: ChatMessage[]
  suggestedQuestions: string[]
}

interface ChatStore extends PlanChatData {
  _cache: Record<string, PlanChatData>
  _activePlanId: string
  isStreaming: boolean
  streamingContent: string

  setActivePlan: (planId: string) => void
  addMessage: (msg: ChatMessage) => void
  setMessages: (msgs: ChatMessage[]) => void
  appendChunk: (chunk: string) => void
  finalizeStream: (sources?: ChatMessage['sources']) => void
  setStreaming: (v: boolean) => void
  setSuggestedQuestions: (qs: string[]) => void
  clearMessages: () => void
  getHistory: () => ChatMessage[]
}

const emptyChat: PlanChatData = { messages: [], suggestedQuestions: [] }

function snapshot(s: ChatStore): PlanChatData {
  return { messages: s.messages, suggestedQuestions: s.suggestedQuestions }
}

export const useChatStore = create<ChatStore>()(
  persist(
    (set, get) => ({
      ...emptyChat,
      _cache: {},
      _activePlanId: '',
      isStreaming: false,
      streamingContent: '',

      setActivePlan: (planId) => set((s) => {
        const cache = { ...s._cache }
        if (s._activePlanId) cache[s._activePlanId] = snapshot(s as unknown as ChatStore)
        const restored = cache[planId] || emptyChat
        return { ...restored, _cache: cache, _activePlanId: planId, streamingContent: '', isStreaming: false }
      }),

      addMessage: (msg) =>
        set((s) => ({ messages: [...s.messages, msg] })),

      setMessages: (msgs) => set({ messages: msgs }),

      appendChunk: (chunk) =>
        set((s) => ({ streamingContent: s.streamingContent + chunk })),

      finalizeStream: (sources) =>
        set((s) => {
          if (!s.streamingContent.trim()) {
            return { streamingContent: '', isStreaming: false }
          }
          const assistantMsg: ChatMessage = {
            id: `msg-${Date.now()}`,
            role: 'assistant',
            content: s.streamingContent,
            createdAt: new Date().toISOString(),
            sources,
          }
          return {
            messages: [...s.messages, assistantMsg],
            streamingContent: '',
            isStreaming: false,
          }
        }),

      setStreaming: (v) => set({ isStreaming: v }),
      setSuggestedQuestions: (qs) => set({ suggestedQuestions: qs }),
      clearMessages: () => set({ messages: [], streamingContent: '', suggestedQuestions: [] }),

      getHistory: () => {
        const { messages } = get()
        return messages.slice(-12)
      },
    }),
    {
      name: 'chat-store',
      partialize: (s) => ({
        _cache: (() => {
          const cache = { ...s._cache }
          if (s._activePlanId) cache[s._activePlanId] = snapshot(s as unknown as ChatStore)
          return cache
        })(),
        _activePlanId: s._activePlanId,
        messages: s.messages,
        suggestedQuestions: s.suggestedQuestions,
      }),
    }
  )
)
