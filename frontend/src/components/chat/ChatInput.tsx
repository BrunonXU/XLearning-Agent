import React, { useState, useRef, useCallback } from 'react'

interface ChatInputProps {
  onSend: (text: string) => void
  disabled?: boolean
  placeholder?: string
  onCancel?: () => void
}

export const ChatInput: React.FC<ChatInputProps> = ({
  onSend, disabled = false, placeholder = '向 AI 提问...', onCancel,
}) => {
  const [value, setValue] = useState('')
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  const handleSend = useCallback(() => {
    const text = value.trim()
    if (!text || disabled) return
    onSend(text)
    setValue('')
    if (textareaRef.current) textareaRef.current.style.height = 'auto'
  }, [value, disabled, onSend])

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend() }
  }

  const handleInput = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setValue(e.target.value)
    const el = e.target
    el.style.height = 'auto'
    el.style.height = Math.min(el.scrollHeight, 200) + 'px'
  }

  const canSend = value.trim().length > 0 && !disabled

  return (
    <div className="border-t border-[#DADCE0] px-6 py-4 bg-white flex-shrink-0">
      <div className="relative flex items-end gap-3 rounded-2xl border border-[#DADCE0] focus-within:border-[#1A73E8] focus-within:ring-2 focus-within:ring-[#1A73E8]/20 bg-white px-5 py-3 shadow-sm transition-all duration-150">
        <textarea
          ref={textareaRef}
          value={value}
          onChange={handleInput}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          disabled={disabled}
          rows={1}
          className="flex-1 resize-none bg-transparent text-[15px] text-[#202124] placeholder:text-[#9AA0A6] outline-none min-h-[44px] max-h-[200px] py-2"
          aria-label="输入消息"
        />
        {onCancel ? (
          <button
            onClick={onCancel}
            aria-label="停止生成"
            className="flex-shrink-0 mb-1 px-4 py-2 rounded-xl text-sm font-medium bg-[#F1F3F4] text-[#5F6368] hover:bg-[#DADCE0] transition-all duration-150"
          >
            ⏹ 停止
          </button>
        ) : (
          <button
            onClick={handleSend}
            disabled={!canSend}
            aria-label="发送消息"
            className={`flex-shrink-0 mb-1 px-4 py-2 rounded-xl text-sm font-medium transition-all duration-150 ${
              canSend
                ? 'bg-[#1A73E8] text-white hover:bg-[#1557B0] active:scale-95 shadow-sm'
                : 'bg-[#F1F3F4] text-[#9AA0A6] cursor-not-allowed'
            }`}
          >
            发送
          </button>
        )}
      </div>
      <p className="text-xs text-[#9AA0A6] mt-1.5 px-1">Enter 发送 · Shift+Enter 换行</p>
    </div>
  )
}
