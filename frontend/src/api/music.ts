import axios from 'axios'

export interface TrackMeta {
  id: number
  prompt: string
  duration: number
  status: string
  has_stems: boolean
  created_at: string
}

export interface GenerateOptions {
  prompt: string
  duration: number
  sessionId: string
  useTrend?: boolean
  genre?: string
  onProgress: (status: string, pct: number) => void
  onDone: (trackId: number) => void
  onError: (err: string) => void
}

export function generateMusic(options: GenerateOptions): () => void {
  const { prompt, duration, sessionId, useTrend = false, genre = 'pop', onProgress, onDone, onError } = options

  const controller = new AbortController()

  fetch('/api/music/generate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      prompt,
      duration,
      session_id: sessionId,
      use_trend: useTrend,
      genre,
    }),
    signal: controller.signal,
  })
    .then(async (res) => {
      if (!res.ok) throw new Error(`Generate request failed: ${res.status}`)
      const reader = res.body!.getReader()
      const decoder = new TextDecoder()

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        const chunk = decoder.decode(value, { stream: true })
        for (const line of chunk.split('\n')) {
          if (!line.startsWith('data: ')) continue
          const data = JSON.parse(line.slice(6))
          if (data.status === 'done') {
            onDone(data.track_id)
          } else if (data.status === 'error') {
            onError(data.detail)
          } else {
            onProgress(data.status, data.progress ?? 0)
          }
        }
      }
    })
    .catch((err) => {
      if (err.name !== 'AbortError') onError(err.message)
    })

  return () => controller.abort()
}

export async function fetchTracks(sessionId: string): Promise<TrackMeta[]> {
  const res = await axios.get<TrackMeta[]>(`/api/music/tracks/${sessionId}`)
  return res.data
}

export function getAudioUrl(trackId: number, stem: string): string {
  return `/api/music/audio/${trackId}/${stem}`
}
