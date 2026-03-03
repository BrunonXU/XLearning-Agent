import React, { useState } from 'react'
import ReactMarkdown from 'react-markdown'
import { SourceCitation } from './SourceCitation'
import { TypingIndicator } from '../ui/Spinner'
import type { ChatMessage } from '../../types'

interface MessageBubbleProps {
  message: ChatMessage
  isStreaming?: boolean
}

export const MessageBubble: React.FC<MessageBubbleProps> = ({ message, isStreaming }) => {
  const isUser = message.role === 'user'

  if (isUser) {
    return (
      <div className="flex justify-end">
        <div className="bg-[#1A73E8] text-white rounded-2xl rounded-tr-sm px-5 py-3.5 max-w-[72%] shadow-sm">
          <p className="text-[15px] leading-relaxed whitespace-pre-wrap">{message.content}</p>
        </div>
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-2 max-w-[85%]">
      <div className="bg-[#F8F9FA] rounded-2xl rounded-tl-sm px-5 py-4 shadow-sm">
        {isStreaming && !message.content ? (
          <TypingIndicator />
        ) : (
          <div className="prose prose-sm max-w-none text-[#202124] prose-p:my-1 prose-headings:my-2 prose-li:my-0.5 prose-code:bg-[#F1F3F4] prose-code:px-1 prose-code:rounded prose-pre:bg-[#F1F3F4] prose-pre:rounded-xl">
            <ReactMarkdown>{message.content}</ReactMarkdown>
            {isStreaming && (
              <span className="inline-block w-0.5 h-[1em] bg-[#202124] animate-pulse ml-0.5 align-middle" />
            )}
          </div>
        )}
      </div>
      {message.sources && message.sources.length > 0 && !isStreaming && (
        <SourceCitation sources={message.sources} />
      )}
    </div>
  )
}
