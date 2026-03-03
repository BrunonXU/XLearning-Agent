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
      for (const file of Array.from(files)) {
        if (!file.name.endsWith('.pdf')) {
          setError('目前仅支持 PDF 文件')
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
        className={`flex flex-col items-center justify-center gap-2 h-28 rounded-xl border-2 border-dashed cursor-pointer transition-all duration-150 ${
          dragging
            ? 'border-[#1A73E8] bg-[#E8F0FE]'
            : 'border-[#DADCE0] hover:border-[#1A73E8] hover:bg-[#F8F9FA]'
        }`}
        role="button"
        aria-label="点击或拖拽上传 PDF"
      >
        <span className="text-2xl">{uploading ? '⏳' : '📄'}</span>
        <p className="text-sm text-[#5F6368] text-center leading-tight">
          {uploading ? '上传中...' : '拖拽 PDF 到此处\n或点击选择文件'}
        </p>
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf"
          multiple
          className="hidden"
          onChange={e => handleFiles(e.target.files)}
          aria-label="选择 PDF 文件"
        />
      </div>

      {/* URL 输入 */}
      <div className="flex gap-1.5">
        <input
          value={urlInput}
          onChange={e => setUrlInput(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && handleUrlSubmit()}
          placeholder="粘贴 GitHub / 网页 URL..."
          className="flex-1 h-9 rounded-lg border border-[#DADCE0] px-3 text-sm focus:outline-none focus:ring-2 focus:ring-[#1A73E8]/30 focus:border-[#1A73E8] dark:bg-dark-surface dark:border-dark-border dark:text-dark-text"
          aria-label="粘贴 URL"
        />
        <button
          onClick={handleUrlSubmit}
          disabled={!urlInput.trim() || uploading}
          aria-label="添加 URL"
          className="h-9 px-3 bg-[#1A73E8] text-white rounded-lg text-sm hover:bg-[#1557B0] disabled:opacity-40 transition-colors duration-150"
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
