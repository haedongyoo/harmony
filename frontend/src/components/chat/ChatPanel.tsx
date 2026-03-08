import { useEffect, useRef } from 'react'
import { useChatStore } from '../../stores/chatStore'
import { useMusicStore } from '../../stores/musicStore'
import { streamChat } from '../../api/chat'
import { useT } from '../../hooks/useT'
import ChatMessage from './ChatMessage'
import ChatInput from './ChatInput'

const MUSIC_PROMPT_RE = /\[MUSIC_PROMPT:\s*([^\]]+)\]/

export default function ChatPanel() {
  const { messages, isStreaming, streamingContent, addUserMessage, startStreaming, appendToken, commitAssistantMessage } =
    useChatStore()
  const { sessionId, setPendingPrompt } = useMusicStore()
  const t = useT()
  const bottomRef = useRef<HTMLDivElement>(null)
  const stopRef = useRef<(() => void) | null>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, streamingContent])

  const handleSend = (message: string) => {
    addUserMessage(message)
    startStreaming()

    stopRef.current = streamChat({
      message,
      sessionId,
      history: messages,
      onToken: (token) => appendToken(token),
      onDone: () => {
        const full = useChatStore.getState().streamingContent
        commitAssistantMessage()

        // [MUSIC_PROMPT: ...] 파싱
        const match = full.match(MUSIC_PROMPT_RE)
        if (match) setPendingPrompt(match[1].trim())
      },
      onError: (err) => {
        appendToken(`\n\n[${t.errorPrefix}: ${err.message}]`)
        commitAssistantMessage()
      },
    })
  }

  return (
    <div className="flex flex-col h-full bg-studio-panel border border-studio-border rounded-2xl overflow-hidden">
      <div className="px-4 py-3 border-b border-studio-border text-sm font-semibold text-gray-300">
        {t.aiChat}
      </div>
      <div className="flex-1 overflow-y-auto p-4">
        {messages.length === 0 && (
          <p className="text-center text-gray-500 text-sm mt-8">
            {t.chatEmptyState}
          </p>
        )}
        {messages.map((m, i) => (
          <ChatMessage key={i} message={m} />
        ))}
        {isStreaming && streamingContent && (
          <ChatMessage message={{ role: 'assistant', content: streamingContent + '▌' }} />
        )}
        <div ref={bottomRef} />
      </div>
      <ChatInput onSend={handleSend} disabled={isStreaming} />
    </div>
  )
}
