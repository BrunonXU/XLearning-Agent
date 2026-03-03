import React from 'react'
import { MessageBubble } from './MessageBubble'
import type { ChatMessage } from '../../types'

interface MessageListProps {
  messages: ChatMessage[]
  isStreaming?: boolean
}

export const MessageList: React.FC<MessageListProps> = ({ messages, isStreaming }) => {
  if (messages.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-center py-16">
        <span className="text-5xl mb-4">💬</span>
        <p className="text-text-secondary text-base">向 AI 提问，开始学习之旅</p>
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-6">
      {messages.map((msg, i) => (
        <MessageBubble
          key={msg.id}
          message={msg}
          isStreaming={isStreaming && i === messages.length - 1}
        />
      ))}
    </div>
  )
}
