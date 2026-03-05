/**
 * UploadArea — PDF 拖拽上传 + GitHub URL 粘贴
 */
import React, { useState, useRef, useCallback } from 'react'
import { useMaterialUpload } from '../../hooks/useMaterialUpload'

interface UploadAreaProps {
  planId: string
}

export const UploadArea: React.FC<UploadAreaProps> = ({ planId }) => {
  const [dragging, setDragging] = useState(false)
  const [urlInput, setUrlInput] = useState('')
  const [error, setError] = useState('')
  const [uploading, setUploading] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const { uploadFile, uploadUrl } = useMaterialUpload(planId)

  const handleFiles = useCallback(async (files: FileList | null) => {
    if (!files?.length) return
    setError('')
    setUploading(true)
    try {
      const ALLOWED_EXTS = ['.pdf', '.md', '.markdown', '.txt']
      for (const file of Array.from(files)) {
        const ext = file.name.slice(file.name.lastIndexOf('.')).toLowerCase()
        if (!ALLOWED_EXTS.includes(ext)) {
          setError('支持 PDF、Markdown、TXT 文件')
          continue
        }
        await uploadFile(file)
      }
    } catch {
      setError('上传失败，请重试')
    } finally {
      setUploading(false)
    }
  }, [uploadFile])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setDragging(false)
    handleFiles(e.dataTransfer.files)
  }, [handleFiles])

  const handleUrlSubmit = async () => {
    const url = urlInput.trim()
    if (!url) return
    if (!url.startsWith('http')) { setError('请输入有效的 URL'); return }
    setError('')
    setUploading(true)
    try {
      await uploadUrl(url)
      setUrlInput('')
    } catch {
      setError('URL 添加失败，请重试')
    } finally {
      setUploading(false)
    }
  }

  return (
    <div className="flex flex-col gap-3">
      {/* 拖拽区域 */}
      <div
        onDragOver={e => { e.preventDefault(); setDragging(true) }}
        onDragLeave={() => setDragging(false)}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        className={`flex flex-col items-center justify-center gap-2 h-32 rounded-xl border-2 border-dashed cursor-pointer transition-all duration-150 ${dragging
            ? 'border-[#D97757] bg-[#F2DFD3]'
            : 'border-[#DADCE0] hover:border-[#D97757] hover:bg-[#F8F9FA]'
          }`}
        role="button"
        aria-label="点击或拖拽上传文件（PDF、MD、TXT）"
      >
        <span className="text-3xl">{uploading ? '⏳' : '📄'}</span>
        <p className="text-sm text-[#5F6368] text-center leading-tight">
          {uploading ? '上传中...' : '拖拽文件到此处\n或点击选择（PDF / MD / TXT）'}
        </p>
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,.md,.markdown,.txt"
          multiple
          className="hidden"
          onChange={e => handleFiles(e.target.files)}
          aria-label="选择 PDF 文件"
        />
      </div>

      {/* URL 输入 */}
      <div className="flex gap-2">
        <input
          value={urlInput}
          onChange={e => setUrlInput(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && handleUrlSubmit()}
          placeholder="粘贴 GitHub / 网页 URL..."
          className="flex-1 h-10 rounded-lg border border-[#DADCE0] px-3 text-sm focus:outline-none focus:ring-2 focus:ring-[#D97757]/30 focus:border-[#D97757] dark:bg-dark-surface dark:border-dark-border dark:text-dark-text"
          aria-label="粘贴 URL"
        />
        <button
          onClick={handleUrlSubmit}
          disabled={!urlInput.trim() || uploading}
          aria-label="添加 URL"
          className="h-10 px-4 bg-[#D97757] text-white rounded-lg text-sm hover:bg-[#C06144] disabled:opacity-40 transition-colors duration-150"
        >
          添加
        </button>
      </div>

      {error && (
        <p className="text-xs text-red-500 px-1">{error}</p>
      )}
    </div>
  )
}
