import React, { useState, useCallback, useRef, useEffect } from 'react'

interface WorkspaceLayoutProps {
  left: React.ReactNode
  center: React.ReactNode
  right: React.ReactNode
  topNav: React.ReactNode
  /** 阅读模式：左侧面板自动扩宽，拖拽有上下限 */
  isReading?: boolean
  /** 左侧栏折叠状态 */
  isLeftCollapsed?: boolean
  /** 右侧栏折叠状态 */
  isRightCollapsed?: boolean
}

const MIN_LEFT = 15
const MAX_LEFT_NORMAL = 35
const MIN_LEFT_READING = 28
const MAX_LEFT_READING = 45
const READING_LEFT = 35
const MIN_CENTER = 30
const MIN_RIGHT = 18

export const WorkspaceLayout: React.FC<WorkspaceLayoutProps> = ({
  left, center, right, topNav, isReading = false, isLeftCollapsed = false, isRightCollapsed = false,
}) => {
  const [leftPct, setLeftPct] = useState(22)
  const [rightPct, setRightPct] = useState(18)
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

  // 动态背景色：根据折叠的侧边栏数量变深，加大色阶落差
  const collapsedCount = (isLeftCollapsed ? 1 : 0) + (isRightCollapsed ? 1 : 0)
  let bgClass = 'bg-[#E6DDF2]' // 0个折叠：浅香芋紫（基调）
  if (collapsedCount === 1) bgClass = 'bg-[#D3CFDC]' // 1个折叠：偏暗的灰紫色
  if (collapsedCount === 2) bgClass = 'bg-[#A8A0B8]' // 2个折叠：非常明显的深灰紫，进入沉浸黑夜环境

  return (
    <div className={`flex flex-col h-screen overflow-hidden ${bgClass} transition-colors duration-500 dark:bg-dark-bg`}>
      <div className="flex-shrink-0 bg-transparent px-4 py-2">
        {topNav}
      </div>
      <div
        ref={containerRef}
        className="flex flex-1 overflow-hidden px-4 pb-4 gap-2"
        style={{ height: 'calc(100vh - 80px)' }}
      >
        {/* 左侧面板 */}
        <div
          className={`flex flex-col overflow-hidden bg-white dark:bg-dark-surface flex-shrink-0 rounded-3xl shadow-soft ${isLeftCollapsed ? 'transition-all duration-300' : ''}`}
          style={{ width: isLeftCollapsed ? '72px' : `calc(${leftPct}% - 8px)` }}
        >
          {left}
        </div>

        {/* 左拖拽条 / 占位符 */}
        {isLeftCollapsed ? (
          <div className="flex-shrink-0 -mx-2 z-10" style={{ width: '16px' }} />
        ) : (
          <div
            className="relative flex-shrink-0 cursor-col-resize group flex items-center justify-center -mx-2 z-10"
            style={{ width: '16px' }}
            onMouseDown={startDragLeft}
            role="separator"
            aria-orientation="vertical"
            aria-label="调整左侧面板宽度"
          >
            <div className="w-[4px] h-12 rounded-full bg-[#E0E0E0] opacity-0 group-hover:opacity-100 group-hover:bg-[#1A73E8] transition-all duration-150" />
          </div>
        )}

        {/* 中间对话区 */}
        <div
          className="flex flex-col overflow-hidden bg-white dark:bg-dark-bg flex-shrink-0 rounded-3xl shadow-soft flex-1 min-w-0"
        >
          {center}
        </div>

        {/* 右拖拽条 / 占位符 */}
        {isRightCollapsed ? (
          <div className="flex-shrink-0 -mx-2 z-10" style={{ width: '16px' }} />
        ) : (
          <div
            className="relative flex-shrink-0 cursor-col-resize group flex items-center justify-center -mx-2 z-10"
            style={{ width: '16px' }}
            onMouseDown={startDragRight}
            role="separator"
            aria-orientation="vertical"
            aria-label="调整右侧面板宽度"
          >
            <div className="w-[4px] h-12 rounded-full bg-[#E0E0E0] opacity-0 group-hover:opacity-100 group-hover:bg-[#1A73E8] transition-all duration-150" />
          </div>
        )}

        {/* 右侧 Studio 面板 */}
        <div
          className={`flex flex-col overflow-hidden bg-white dark:bg-dark-surface flex-shrink-0 rounded-3xl shadow-soft ${isRightCollapsed ? 'transition-all duration-300' : ''}`}
          style={{ width: isRightCollapsed ? '72px' : `calc(${rightPct}% - 8px)` }}
        >
          {right}
        </div>
      </div>
    </div>
  )
}
