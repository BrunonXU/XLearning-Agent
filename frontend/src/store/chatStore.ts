import { create } from 'zustand'
import type { ChatMessage } from '../types'

interface ChatStore {
  messages: ChatMessage[]
  suggestedQuestions: string[]
  isStreaming: boolean
  streamingContent: string
  loading: boolean

  loadMessages: (planId: string) => Promise<void>
  addMessage: (msg: ChatMessage) => void
  setMessages: (msgs: ChatMessage[]) => void
  appendChunk: (chunk: string) => void
  finalizeStream: (sources?: ChatMessage['sources']) => void
  setStreaming: (v: boolean) => void
  setSuggestedQuestions: (qs: string[]) => void
  clearMessages: () => void
  getHistory: () => ChatMessage[]
}

export const useChatStore = create<ChatStore>()((set, get) => ({
  messages: [],
  suggestedQuestions: [],
  isStreaming: false,
  streamingContent: '',
  loading: false,

  loadMessages: async (planId: string) => {
    set({ loading: true })
    try {
      const res = await fetch(`/api/plans/${planId}/messages`)
      if (!res.ok) throw new Error('加载失败')
      const data = await res.json()
      set({ messages: data, loading: false })
    } catch {
      set({ loading: false })
    }
  },

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
}))
