import { create } from 'zustand'
import { TrackMeta } from '../api/music'

interface GenerationState {
  status: 'idle' | 'generating' | 'splitting' | 'done' | 'error'
  progress: number
  error: string | null
}

interface MusicState {
  sessionId: string
  tracks: TrackMeta[]
  generation: GenerationState
  pendingPrompt: string  // [MUSIC_PROMPT: ...] 파싱 결과를 PromptInput에 채워주기 위한 상태

  setTracks: (tracks: TrackMeta[]) => void
  addTrack: (track: TrackMeta) => void
  setGeneration: (update: Partial<GenerationState>) => void
  setPendingPrompt: (prompt: string) => void
  clearPendingPrompt: () => void
}

function generateSessionId(): string {
  return crypto.randomUUID()
}

export const useMusicStore = create<MusicState>((set) => ({
  sessionId: generateSessionId(),
  tracks: [],
  generation: { status: 'idle', progress: 0, error: null },
  pendingPrompt: '',

  setTracks: (tracks) => set({ tracks }),
  addTrack: (track) => set((s) => ({ tracks: [track, ...s.tracks] })),

  setGeneration: (update) =>
    set((s) => ({ generation: { ...s.generation, ...update } })),

  setPendingPrompt: (prompt) => set({ pendingPrompt: prompt }),
  clearPendingPrompt: () => set({ pendingPrompt: '' }),
}))
