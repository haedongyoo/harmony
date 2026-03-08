export interface Message {
  role: 'user' | 'assistant'
  content: string
}

export interface ChatStreamOptions {
  message: string
  sessionId: string
  history: Message[]
  onToken: (token: string) => void
  onDone: () => void
  onError: (err: Error) => void
}

export function streamChat(options: ChatStreamOptions): () => void {
  const { message, sessionId, history, onToken, onDone, onError } = options

  const controller = new AbortController()

  fetch('/api/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, session_id: sessionId, history }),
    signal: controller.signal,
  })
    .then(async (res) => {
      if (!res.ok) throw new Error(`Chat request failed: ${res.status}`)
      const reader = res.body!.getReader()
      const decoder = new TextDecoder()

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        const chunk = decoder.decode(value, { stream: true })
        for (const line of chunk.split('\n')) {
          if (!line.startsWith('data: ')) continue
          const data = JSON.parse(line.slice(6))
          if (data.token) onToken(data.token)
          if (data.done) onDone()
        }
      }
    })
    .catch((err) => {
      if (err.name !== 'AbortError') onError(err)
    })

  return () => controller.abort()
}
