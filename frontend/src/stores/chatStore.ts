import { create } from 'zustand'
import { Message } from '../api/chat'

interface ChatState {
  messages: Message[]
  isStreaming: boolean
  streamingContent: string
  addUserMessage: (content: string) => void
  startStreaming: () => void
  appendToken: (token: string) => void
  commitAssistantMessage: () => void
  reset: () => void
}

export const useChatStore = create<ChatState>((set, get) => ({
  messages: [],
  isStreaming: false,
  streamingContent: '',

  addUserMessage: (content) =>
    set((s) => ({
      messages: [...s.messages, { role: 'user', content }],
    })),

  startStreaming: () => set({ isStreaming: true, streamingContent: '' }),

  appendToken: (token) =>
    set((s) => ({ streamingContent: s.streamingContent + token })),

  commitAssistantMessage: () => {
    const { streamingContent, messages } = get()
    set({
      messages: [...messages, { role: 'assistant', content: streamingContent }],
      isStreaming: false,
      streamingContent: '',
    })
  },

  reset: () => set({ messages: [], isStreaming: false, streamingContent: '' }),
}))
