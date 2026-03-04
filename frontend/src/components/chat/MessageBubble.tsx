import React from 'react'
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
        <div className="bg-[#E8F0FE] text-[#202124] rounded-3xl rounded-tr-sm px-6 py-4 max-w-[72%] shadow-sm">
          <p className="text-[16px] leading-relaxed whitespace-pre-wrap">{message.content}</p>
        </div>
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-2 max-w-[95%]">
      <div className="bg-[#F1F3F4] text-[#202124] rounded-3xl rounded-tl-sm px-6 py-4 shadow-sm w-fit max-w-[85%]">
        {isStreaming && !message.content ? (
          <TypingIndicator />
        ) : (
          <div className="prose max-w-none text-[#202124] leading-relaxed prose-p:my-2 prose-headings:my-4 prose-li:my-1 prose-code:bg-white/60 prose-code:px-1.5 prose-code:py-0.5 prose-code:rounded-md prose-pre:bg-white prose-pre:rounded-2xl prose-pre:border prose-pre:border-black/5 text-[16px]">
            <ReactMarkdown>{message.content}</ReactMarkdown>
            {isStreaming && (
              <span className="inline-block w-0.5 h-[1em] bg-[#1A73E8] animate-pulse ml-1 align-middle" />
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
