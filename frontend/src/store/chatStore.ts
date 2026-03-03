import { create } from 'zustand'
import type { ChatMessage } from '../types'

interface ChatStore {
  messages: ChatMessage[]
  isStreaming: boolean
  suggestedQuestions: string[]
  streamingContent: string

  addMessage: (msg: ChatMessage) => void
  setMessages: (msgs: ChatMessage[]) => void
  appendChunk: (chunk: string) => void
  finalizeStream: (sources?: ChatMessage['sources']) => void
  setStreaming: (v: boolean) => void
  setSuggestedQuestions: (qs: string[]) => void
  clearMessages: () => void
  /** 保留最近 6 轮（12 条）对话历史 */
  getHistory: () => ChatMessage[]
}

export const useChatStore = create<ChatStore>((set, get) => ({
  messages: [],
  isStreaming: false,
  suggestedQuestions: [],
  streamingContent: '',

  addMessage: (msg) =>
    set((s) => ({ messages: [...s.messages, msg] })),

  setMessages: (msgs) => set({ messages: msgs }),

  appendChunk: (chunk) =>
    set((s) => ({ streamingContent: s.streamingContent + chunk })),

  finalizeStream: (sources) =>
    set((s) => {
      // streamingContent 为空时不添加消息（避免空气泡）
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
    // 最近 12 条（6 轮）
    return messages.slice(-12)
  },
}))
