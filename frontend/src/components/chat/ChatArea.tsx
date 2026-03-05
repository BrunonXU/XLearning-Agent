import React, { useRef, useEffect } from 'react'
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
  const {
    messages,
    isStreaming,
    streamingContent,
  } = useChatStore()
  const { materials } = useSourceStore()
  const hasMaterials = materials.length > 0
  const { sendMessage, cancel } = useSSE(planId)

  // 新消息/流式内容变化时滚动到底部
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages.length, streamingContent])

  return (
    <div className="flex flex-col h-full overflow-hidden">
      {/* 顶部留白防粘连区域（固定不滚动） */}
      <div className="h-4 flex-shrink-0" />

      {/* 消息列表 */}
      <div className="flex-1 overflow-y-auto scrollbar-thin flex flex-col items-center">
        <div className="w-full max-w-4xl px-8 pt-4 pb-6 flex-1 flex flex-col">
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

      {/* 无材料提示横幅 */}
      {!hasMaterials && (
        <div className="flex justify-center w-full">
          <div className="w-full max-w-4xl mx-8 mb-3 bg-[#FFF7ED] border border-[#F97316] text-[#F97316] text-sm rounded-xl px-4 py-2.5 flex items-center gap-2">
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
  )
}
