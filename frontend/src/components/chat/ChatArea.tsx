import React, { useRef, useEffect, useState } from 'react'
import ReactMarkdown from 'react-markdown'
import { MessageList } from './MessageList'
import { ChatInput } from './ChatInput'
import { useChatStore } from '../../store/chatStore'
import { useSourceStore } from '../../store/sourceStore'
import { useSSE } from '../../hooks/useSSE'

interface ChatAreaProps {
  planId?: string
}

export const ChatArea: React.FC<ChatAreaProps> = ({ planId = '' }) => {
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const [dragOver, setDragOver] = useState(false)
  const {
    messages,
    isStreaming,
    streamingContent,
    attachMaterial,
  } = useChatStore()
  const { materials } = useSourceStore()
  const hasMaterials = materials.length > 0
  const { sendMessage, cancel } = useSSE(planId)

  // 新消息/流式内容变化时滚动到底部
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages.length, streamingContent])

  const handleDragOver = (e: React.DragEvent) => {
    if (e.dataTransfer.types.includes('application/material')) {
      e.preventDefault()
      setDragOver(true)
    }
  }
  const handleDragLeave = (e: React.DragEvent) => {
    // 只在离开整个区域时取消
    if (e.currentTarget.contains(e.relatedTarget as Node)) return
    setDragOver(false)
  }
  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setDragOver(false)
    try {
      const raw = e.dataTransfer.getData('application/material')
      if (raw) {
        const mat = JSON.parse(raw)
        attachMaterial(mat)
      }
    } catch { /* ignore */ }
  }

  return (
    <div
      className="flex flex-col h-full overflow-hidden bg-white relative"
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
    >
      {/* 拖拽覆盖层 */}
      {dragOver && (
        <div className="absolute inset-0 z-50 bg-[#D97757]/5 border-2 border-dashed border-[#D97757]/40 rounded-xl flex items-center justify-center pointer-events-none">
          <div className="bg-white/90 px-6 py-4 rounded-2xl shadow-lg text-center">
            <span className="text-2xl block mb-1">📎</span>
            <span className="text-sm text-[#D97757] font-medium">松开以附加材料到对话</span>
          </div>
        </div>
      )}

      {/* 顶部标题栏 */}
      <div className="h-[68px] flex items-center px-8 flex-shrink-0 border-b border-[#E5E5E5] bg-white z-10">
        <span className="text-base font-semibold text-[#1A1A18]">对话</span>
      </div>

      {/* 消息和输入框的共同滚动容器（统一背景色消除断层） */}
      <div className="flex-1 overflow-hidden flex flex-col bg-[#FDFDFD]">
        {/* 标题栏下方留白（与其他面板一致） */}
        <div className="h-4 flex-shrink-0" />

        {/* 消息列表（只有这里滚动） */}
        <div className="flex-1 overflow-y-auto scrollbar-thin flex flex-col items-center">
          <div className="w-full max-w-3xl px-8 pt-4 pb-6 flex-1 flex flex-col">
            <MessageList messages={messages} isStreaming={isStreaming && !streamingContent} />

            {/* 流式输出气泡 */}
            {isStreaming && streamingContent && (
              <div className="flex flex-col gap-2 max-w-[85%] mt-6">
                <div className="bg-[#F8F9FA] rounded-2xl rounded-tl-sm px-6 py-5 shadow-sm">
                  <div className="prose max-w-none text-[#202124] prose-p:my-1.5 prose-headings:my-2.5 prose-li:my-0.5 prose-code:bg-[#F1F3F4] prose-code:px-1 prose-code:rounded">
                    <ReactMarkdown>{streamingContent}</ReactMarkdown>
                    <span className="inline-block w-0.5 h-[1em] bg-[#D97757] animate-pulse ml-0.5 align-middle" />
                  </div>
                </div>
              </div>
            )}

            {/* 等待 AI 响应的 typing 动画 */}
            {isStreaming && !streamingContent && (
              <div className="flex flex-col gap-2 max-w-[85%] mt-6">
                <div className="bg-[#F8F9FA] rounded-2xl rounded-tl-sm px-5 py-4 shadow-sm">
                  <div className="flex gap-1 items-center h-5">
                    <span className="w-2 h-2 rounded-full bg-[#9AA0A6] animate-bounce [animation-delay:0ms]" />
                    <span className="w-2 h-2 rounded-full bg-[#9AA0A6] animate-bounce [animation-delay:150ms]" />
                    <span className="w-2 h-2 rounded-full bg-[#9AA0A6] animate-bounce [animation-delay:300ms]" />
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        </div>

        {/* 底部固定区域（提示横幅 + 输入框） */}
        <div className="flex-shrink-0 flex flex-col items-center">
          {/* 无材料提示横幅 */}
          {!hasMaterials && (
            <div className="flex justify-center w-full bg-transparent">
              <div className="w-full max-w-3xl mx-8 mb-2 bg-[#FFF7ED] border border-[#F97316] text-[#F97316] text-sm rounded-xl px-4 py-2.5 flex items-center gap-2">
                <span>⚠️</span>
                <span>添加学习材料后，AI 将基于你的材料回答</span>
              </div>
            </div>
          )}

          {/* 输入框 */}
          <ChatInput
            onSend={sendMessage}
            disabled={isStreaming}
            onCancel={isStreaming ? cancel : undefined}
          />
        </div>
      </div>
    </div>
  )
}
