import React, { useState } from 'react'
import { Modal } from '../ui/Modal'
import { Button } from '../ui/Button'

type CreateMode = 'pdf' | 'link' | 'topic' | null

interface NewPlanModalProps {
  open: boolean
  onClose: () => void
  onCreate: (title: string, mode: CreateMode, input: string) => void
}

export const NewPlanModal: React.FC<NewPlanModalProps> = ({ open, onClose, onCreate }) => {
  const [title, setTitle] = useState('')
  const [mode, setMode] = useState<CreateMode>(null)
  const [input, setInput] = useState('')

  const handleCreate = () => {
    if (!mode) return
    onCreate(title || '新建学习规划', mode, input)
    setTitle(''); setMode(null); setInput('')
    onClose()
  }

  const modes: { key: CreateMode; icon: string; label: string; desc: string }[] = [
    { key: 'pdf', icon: '📄', label: '上传 PDF', desc: '拖拽或点击选择文件' },
    { key: 'link', icon: '🔗', label: '粘贴链接', desc: 'GitHub / 网页链接' },
    { key: 'topic', icon: '💬', label: '直接开始', desc: '描述学习主题' },
  ]

  return (
    <Modal open={open} onClose={onClose} title="新建学习规划" width="max-w-lg">
      {/* 规划名称 */}
      <div className="mb-4">
        <label className="text-sm text-text-secondary mb-1 block">规划名称（可选）</label>
        <input
          value={title}
          onChange={e => setTitle(e.target.value)}
          placeholder="例：Transformer 架构学习"
          className="w-full h-10 rounded-lg border border-border px-3 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
        />
      </div>

      {/* 创建方式 */}
      <p className="text-sm text-text-secondary mb-2">选择开始方式：</p>
      <div className="grid grid-cols-3 gap-2 mb-4">
        {modes.map(m => (
          <button
            key={m.key}
            onClick={() => setMode(m.key)}
            className={`flex flex-col items-center gap-1 p-3 rounded-xl border transition-all duration-150 ${
              mode === m.key
                ? 'border-primary bg-primary-light'
                : 'border-border hover:border-primary/50 hover:bg-surface-tertiary'
            }`}
          >
            <span className="text-2xl">{m.icon}</span>
            <span className="text-sm font-medium text-text-primary">{m.label}</span>
            <span className="text-xs text-text-secondary text-center">{m.desc}</span>
          </button>
        ))}
      </div>

      {/* 输入区 */}
      {mode === 'topic' && (
        <textarea
          value={input}
          onChange={e => setInput(e.target.value)}
          placeholder="我想学习 Transformer 架构，从注意力机制开始..."
          rows={3}
          className="w-full rounded-lg border border-border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary resize-none mb-4"
        />
      )}
      {mode === 'link' && (
        <input
          value={input}
          onChange={e => setInput(e.target.value)}
          placeholder="https://github.com/..."
          className="w-full h-10 rounded-lg border border-border px-3 text-sm focus:outline-none focus:ring-2 focus:ring-primary mb-4"
        />
      )}

      {/* 操作按钮 */}
      <div className="flex justify-end gap-2">
        <Button variant="secondary" onClick={onClose}>取消</Button>
        <Button variant="primary" disabled={!mode} onClick={handleCreate}>
          创建规划 →
        </Button>
      </div>
    </Modal>
  )
}
