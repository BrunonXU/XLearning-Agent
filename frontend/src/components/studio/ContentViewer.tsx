/**
 * ContentViewer — AI 生成内容查看弹窗
 * 渲染 Markdown，支持导出为 .md 文件
 */
import React from 'react'
import ReactMarkdown from 'react-markdown'
import type { GeneratedContent } from '../../types'

interface ContentViewerProps {
  content: GeneratedContent
  onClose: () => void
}

export const ContentViewer: React.FC<ContentViewerProps> = ({ content, onClose }) => {
  const handleExport = () => {
    const blob = new Blob([content.content], { type: 'text/markdown;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${content.title}.md`
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm">
      <div className="bg-white dark:bg-dark-surface rounded-2xl shadow-2xl w-[720px] max-h-[82vh] flex flex-col overflow-hidden">
        {/* 标题栏 */}
        <div className="flex items-center justify-between px-5 py-3.5 border-b border-[#DADCE0] dark:border-dark-border flex-shrink-0">
          <span className="text-base font-semibold text-[#202124] dark:text-dark-text">
            {content.title}
          </span>
          <div className="flex items-center gap-2">
            <button
              onClick={handleExport}
              aria-label="导出为 Markdown"
              className="h-7 px-3 rounded-lg text-xs text-[#5F6368] hover:bg-[#F1F3F4] dark:hover:bg-dark-border transition-colors duration-150 flex items-center gap-1"
            >
              ↓ 导出 .md
            </button>
            <button
              onClick={onClose}
              aria-label="关闭"
              className="text-[#5F6368] hover:text-[#202124] transition-colors duration-150 text-xl leading-none"
            >
              ×
            </button>
          </div>
        </div>

        {/* Markdown 内容 */}
        <div className="flex-1 overflow-y-auto px-6 py-5 prose prose-sm max-w-none dark:prose-invert">
          <ReactMarkdown>{content.content || '（内容为空）'}</ReactMarkdown>
        </div>
      </div>
    </div>
  )
}
