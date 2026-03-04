import React, { useState, useCallback, useRef, useEffect } from 'react'

interface WorkspaceLayoutProps {
  left: React.ReactNode
  center: React.ReactNode
  right: React.ReactNode
  topNav: React.ReactNode
  /** 阅读模式：左侧面板自动扩宽，拖拽有上下限 */
  isReading?: boolean
}

const MIN_LEFT = 15
const MAX_LEFT_NORMAL = 35
const MIN_LEFT_READING = 28
const MAX_LEFT_READING = 45
const READING_LEFT = 35
const MIN_CENTER = 30
const MIN_RIGHT = 18

export const WorkspaceLayout: React.FC<WorkspaceLayoutProps> = ({
  left, center, right, topNav, isReading = false,
}) => {
  const [leftPct, setLeftPct] = useState(22)
  const [rightPct, setRightPct] = useState(28)
  const prevReadingRef = useRef(isReading)
  const savedLeftRef = useRef(22)
  const containerRef = useRef<HTMLDivElement>(null)

  // 进入/退出阅读模式时自动调整左侧宽度
  useEffect(() => {
    if (isReading && !prevReadingRef.current) {
      // 进入阅读模式：保存当前宽度，扩宽到 READING_LEFT
      savedLeftRef.current = leftPct
      setLeftPct(READING_LEFT)
    } else if (!isReading && prevReadingRef.current) {
      // 退出阅读模式：恢复之前的宽度
      setLeftPct(savedLeftRef.current)
    }
    prevReadingRef.current = isReading
  }, [isReading]) // eslint-disable-line react-hooks/exhaustive-deps

  const centerPct = 100 - leftPct - rightPct

  const startDragLeft = useCallback((e: React.MouseEvent) => {
    e.preventDefault()
    const startX = e.clientX
    const startLeft = leftPct
    const minL = isReading ? MIN_LEFT_READING : MIN_LEFT
    const maxL = isReading ? MAX_LEFT_READING : MAX_LEFT_NORMAL
    const onMove = (ev: MouseEvent) => {
      if (!containerRef.current) return
      const totalW = containerRef.current.offsetWidth
      const delta = ((ev.clientX - startX) / totalW) * 100
      const newLeft = Math.min(maxL, Math.max(minL, startLeft + delta))
      if (100 - newLeft - rightPct >= MIN_CENTER) setLeftPct(newLeft)
    }
    const onUp = () => {
      document.removeEventListener('mousemove', onMove)
      document.removeEventListener('mouseup', onUp)
      document.body.style.cursor = ''
      document.body.style.userSelect = ''
    }
    document.body.style.cursor = 'col-resize'
    document.body.style.userSelect = 'none'
    document.addEventListener('mousemove', onMove)
    document.addEventListener('mouseup', onUp)
  }, [leftPct, rightPct, isReading])

  const startDragRight = useCallback((e: React.MouseEvent) => {
    e.preventDefault()
    const startX = e.clientX
    const startRight = rightPct
    const onMove = (ev: MouseEvent) => {
      if (!containerRef.current) return
      const totalW = containerRef.current.offsetWidth
      const delta = ((startX - ev.clientX) / totalW) * 100
      const newRight = Math.max(MIN_RIGHT, startRight + delta)
      if (100 - leftPct - newRight >= MIN_CENTER) setRightPct(newRight)
    }
    const onUp = () => {
      document.removeEventListener('mousemove', onMove)
      document.removeEventListener('mouseup', onUp)
      document.body.style.cursor = ''
      document.body.style.userSelect = ''
    }
    document.body.style.cursor = 'col-resize'
    document.body.style.userSelect = 'none'
    document.addEventListener('mousemove', onMove)
    document.addEventListener('mouseup', onUp)
  }, [leftPct, rightPct])

  return (
    <div className="flex flex-col h-screen overflow-hidden bg-[#F8F9FA] dark:bg-dark-bg">
      {topNav}
      <div
        ref={containerRef}
        className="flex flex-1 overflow-hidden"
        style={{ height: 'calc(100vh - 56px)' }}
      >
        {/* 左侧面板 */}
        <div
          className="flex flex-col overflow-hidden bg-[#F8F9FA] dark:bg-dark-surface flex-shrink-0"
          style={{ width: `${leftPct}%` }}
        >
          {left}
        </div>

        {/* 左拖拽条 — 宽 8px，hover 变蓝 */}
        <div
          className="relative flex-shrink-0 flex items-center justify-center cursor-col-resize group"
          style={{ width: '8px', background: '#E8EAED' }}
          onMouseDown={startDragLeft}
          role="separator"
          aria-orientation="vertical"
          aria-label="调整左侧面板宽度"
        >
          <div className="absolute inset-y-0 w-1 rounded-full bg-[#DADCE0] group-hover:bg-primary transition-colors duration-150" />
        </div>

        {/* 中间对话区 */}
        <div
          className="flex flex-col overflow-hidden bg-white dark:bg-dark-bg flex-shrink-0"
          style={{ width: `${centerPct}%` }}
        >
          {center}
        </div>

        {/* 右拖拽条 */}
        <div
          className="relative flex-shrink-0 flex items-center justify-center cursor-col-resize group"
          style={{ width: '8px', background: '#E8EAED' }}
          onMouseDown={startDragRight}
          role="separator"
          aria-orientation="vertical"
          aria-label="调整右侧面板宽度"
        >
          <div className="absolute inset-y-0 w-1 rounded-full bg-[#DADCE0] group-hover:bg-primary transition-colors duration-150" />
        </div>

        {/* 右侧 Studio 面板 */}
        <div
          className="flex flex-col overflow-hidden bg-[#F8F9FA] dark:bg-dark-surface flex-shrink-0"
          style={{ width: `${rightPct}%` }}
        >
          {right}
        </div>
      </div>
    </div>
  )
}
