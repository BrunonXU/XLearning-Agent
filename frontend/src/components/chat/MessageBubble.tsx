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
      <div className="flex justify-end mt-2 mb-4">
        <div className="bg-[#F3F4F6] text-[#202124] rounded-2xl px-5 py-3.5 max-w-[72%]">
          <p className="text-[16px] leading-relaxed whitespace-pre-wrap">{message.content}</p>
        </div>
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-2 max-w-[95%] mb-6">
      <div className="text-[#202124] w-fit max-w-[90%] pb-2">
        {isStreaming && !message.content ? (
          <TypingIndicator />
        ) : (
          <div className="prose max-w-none text-[#202124] leading-8 prose-p:my-5 prose-headings:my-6 prose-li:my-3 prose-code:bg-gray-100 prose-code:px-1.5 prose-code:py-0.5 prose-code:rounded-md prose-pre:bg-[#1E1E1E] prose-pre:text-gray-100 prose-pre:rounded-xl prose-pre:border-none text-[17px] tracking-wide">
            <ReactMarkdown>{message.content}</ReactMarkdown>
            {isStreaming && (
              <span className="inline-block w-0.5 h-[1em] bg-[#D97757] animate-pulse ml-1 align-middle" />
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
