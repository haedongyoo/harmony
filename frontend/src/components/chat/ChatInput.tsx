import { useState, KeyboardEvent } from 'react'
import { useT } from '../../hooks/useT'

interface Props {
  onSend: (message: string) => void
  disabled?: boolean
}

export default function ChatInput({ onSend, disabled }: Props) {
  const [value, setValue] = useState('')
  const t = useT()

  const handleSend = () => {
    const trimmed = value.trim()
    if (!trimmed || disabled) return
    onSend(trimmed)
    setValue('')
  }

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="flex gap-2 p-3 border-t border-studio-border">
      <textarea
        className="flex-1 bg-studio-panel border border-studio-border rounded-xl px-3 py-2 text-sm text-white resize-none outline-none focus:border-studio-accent transition-colors"
        rows={2}
        placeholder={t.chatPlaceholder}
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={handleKeyDown}
        disabled={disabled}
      />
      <button
        onClick={handleSend}
        disabled={disabled || !value.trim()}
        className="px-4 py-2 bg-studio-accent hover:bg-studio-accent-hover disabled:opacity-40 disabled:cursor-not-allowed rounded-xl text-sm font-medium transition-colors self-end"
      >
        {t.send}
      </button>
    </div>
  )
}
