import { Message } from '../../api/chat'

interface Props {
  message: Message
}

// [MUSIC_PROMPT: ...] 태그를 하이라이트 처리
function renderContent(content: string) {
  const parts = content.split(/(\[MUSIC_PROMPT:[^\]]+\])/g)
  return parts.map((part, i) => {
    if (part.startsWith('[MUSIC_PROMPT:')) {
      const prompt = part.slice('[MUSIC_PROMPT:'.length, -1).trim()
      return (
        <span
          key={i}
          className="block mt-2 px-3 py-2 bg-studio-accent/20 border border-studio-accent rounded text-sm text-purple-300 font-mono"
        >
          {prompt}
        </span>
      )
    }
    return <span key={i}>{part}</span>
  })
}

export default function ChatMessage({ message }: Props) {
  const isUser = message.role === 'user'

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-3`}>
      <div
        className={`max-w-[80%] px-4 py-3 rounded-2xl text-sm leading-relaxed ${
          isUser
            ? 'bg-studio-accent text-white rounded-br-sm'
            : 'bg-studio-panel border border-studio-border text-gray-200 rounded-bl-sm'
        }`}
      >
        {renderContent(message.content)}
      </div>
    </div>
  )
}
