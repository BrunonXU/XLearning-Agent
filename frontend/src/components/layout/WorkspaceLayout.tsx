import React, { useState, useCallback, useRef } from 'react'

interface WorkspaceLayoutProps {
  left: React.ReactNode
  center: React.ReactNode
  right: React.ReactNode
  topNav: React.ReactNode
}

const MIN_LEFT = 15
const MIN_CENTER = 35
const MIN_RIGHT = 18

export const WorkspaceLayout: React.FC<WorkspaceLayoutProps> = ({
  left, center, right, topNav,
}) => {
  const [leftPct, setLeftPct] = useState(22)
  const [rightPct, setRightPct] = useState(28)
  const containerRef = useRef<HTMLDivElement>(null)

  const centerPct = 100 - leftPct - rightPct

  const startDragLeft = useCallback((e: React.MouseEvent) => {
    e.preventDefault()
    const startX = e.clientX
    const startLeft = leftPct
    const onMove = (ev: MouseEvent) => {
      if (!containerRef.current) return
      const totalW = containerRef.current.offsetWidth
      const delta = ((ev.clientX - startX) / totalW) * 100
      const newLeft = Math.max(MIN_LEFT, startLeft + delta)
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
  }, [leftPct, rightPct])

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

        {/* 左拖拽条 — 宽 5px，hover 变蓝，中间有竖线视觉提示 */}
        <div
          className="relative flex-shrink-0 flex items-center justify-center cursor-col-resize group"
          style={{ width: '5px', background: '#DADCE0' }}
          onMouseDown={startDragLeft}
          role="separator"
          aria-orientation="vertical"
          aria-label="调整左侧面板宽度"
        >
          <div className="absolute inset-y-0 w-px bg-[#DADCE0] group-hover:bg-primary transition-colors duration-150" />
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
          style={{ width: '5px', background: '#DADCE0' }}
          onMouseDown={startDragRight}
          role="separator"
          aria-orientation="vertical"
          aria-label="调整右侧面板宽度"
        >
          <div className="absolute inset-y-0 w-px bg-[#DADCE0] group-hover:bg-primary transition-colors duration-150" />
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
