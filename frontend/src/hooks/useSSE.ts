/**
 * useSSE — SSE 流式对话 hook
 *
 * 事件格式（来自 /api/chat）：
 *   data: {"type": "chunk",   "content": "..."}
 *   data: {"type": "sources", "sources": [...]}
 *   data: {"type": "questions","questions": [...]}
 *   data: {"type": "done"}
 *   data: {"type": "error",   "message": "..."}
 *
 * 特性：
 * - 自动重连，最多 3 次，失败后降级为普通 HTTP
 * - AbortController 支持取消
 */

import { useCallback, useRef } from 'react'
import { useChatStore } from '../store/chatStore'
import { useStudioStore } from '../store/studioStore'
import type { ChatMessage } from '../types'

const MAX_RETRIES = 3
const RETRY_DELAY = 1000  // ms

export function useSSE(planId: string) {
  const abortRef = useRef<AbortController | null>(null)
  const retryCount = useRef(0)

  const {
    addMessage,
    appendChunk,
    finalizeStream,
    setStreaming,
    setSuggestedQuestions,
    getHistory,
  } = useChatStore()

  const cancel = useCallback(() => {
    abortRef.current?.abort()
    setStreaming(false)
  }, [setStreaming])

  const sendMessage = useCallback(async (text: string) => {
    // 添加用户消息
    const userMsg: ChatMessage = {
      id: `msg-${Date.now()}`,
      role: 'user',
      content: text,
      createdAt: new Date().toISOString(),
    }
    addMessage(userMsg)
    setStreaming(true)
    retryCount.current = 0

    const history = getHistory().slice(0, -1)  // 不含刚加的用户消息

    const _attempt = async (): Promise<void> => {
      abortRef.current?.abort()
      abortRef.current = new AbortController()

      try {
        const res = await fetch('/api/chat', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            planId,
            message: text,
            history: history.map(m => ({ role: m.role, content: m.content })),
          }),
          signal: abortRef.current.signal,
        })

        if (!res.ok || !res.body) {
          throw new Error(`HTTP ${res.status}`)
        }

        const reader = res.body.getReader()
        const decoder = new TextDecoder()
        let buffer = ''
        let pendingSources: ChatMessage['sources'] | undefined

        while (true) {
          const { done, value } = await reader.read()
          if (done) break

          buffer += decoder.decode(value, { stream: true })
          const lines = buffer.split('\n')
          buffer = lines.pop() ?? ''

          for (const line of lines) {
            if (!line.startsWith('data: ')) continue
            try {
              const evt = JSON.parse(line.slice(6))
              if (evt.type === 'chunk') {
                appendChunk(evt.content ?? '')
              } else if (evt.type === 'sources') {
                pendingSources = evt.sources
              } else if (evt.type === 'questions') {
                setSuggestedQuestions(evt.questions ?? [])
              } else if (evt.type === 'studio_update') {
                const { addGeneratedContent } = useStudioStore.getState()
                addGeneratedContent({
                  id: `${evt.toolType}-${Date.now()}`,
                  type: evt.content.type,
                  title: evt.content.title,
                  content: evt.content.content,
                  createdAt: evt.content.createdAt || new Date().toISOString(),
                })
              } else if (evt.type === 'done') {
                finalizeStream(pendingSources)
                setStreaming(false)
                retryCount.current = 0
                return
              } else if (evt.type === 'error') {
                throw new Error(evt.message ?? 'SSE error')
              }
            } catch (parseErr) {
              // 忽略单行解析错误
            }
          }
        }

        // 流结束但没收到 done 事件，也 finalize
        finalizeStream(pendingSources)
        setStreaming(false)
      } catch (err: any) {
        if (err.name === 'AbortError') {
          setStreaming(false)
          return
        }

        retryCount.current++
        if (retryCount.current < MAX_RETRIES) {
          await new Promise(r => setTimeout(r, RETRY_DELAY * retryCount.current))
          return _attempt()
        }

        // 超过重试次数，降级为普通 HTTP
        await _fallbackHttp(text, history)
      }
    }

    await _attempt()
  }, [planId, addMessage, appendChunk, finalizeStream, setStreaming, setSuggestedQuestions, getHistory])

  /** 降级：普通 HTTP POST，不流式 */
  const _fallbackHttp = async (text: string, history: ChatMessage[]) => {
    try {
      const res = await fetch('/api/chat/sync', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          planId,
          message: text,
          history: history.map(m => ({ role: m.role, content: m.content })),
        }),
      })
      if (res.ok) {
        const data = await res.json()
        appendChunk(data.content ?? '（AI 暂时不可用，请稍后重试）')
      } else {
        appendChunk('（AI 暂时不可用，请稍后重试）')
      }
    } catch {
      appendChunk('（网络错误，请检查连接后重试）')
    } finally {
      finalizeStream()
      setStreaming(false)
    }
  }

  return { sendMessage, cancel }
}
