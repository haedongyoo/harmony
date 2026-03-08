import ChatPanel from '../components/chat/ChatPanel'
import TrackList from '../components/music/TrackList'
import PromptInput from '../components/music/PromptInput'
import LangToggle from '../components/ui/LangToggle'
import { useMusicStore } from '../stores/musicStore'
import { downloadSession } from '../api/export'
import { useT } from '../hooks/useT'

export default function Studio() {
  const { sessionId } = useMusicStore()
  const t = useT()

  return (
    <div className="min-h-screen bg-studio-bg flex flex-col">
      {/* Header */}
      <header className="flex items-center justify-between px-6 py-4 border-b border-studio-border">
        <h1 className="text-lg font-bold tracking-tight">{t.appTitle}</h1>
        <div className="flex items-center gap-3">
          <LangToggle />
          <button
            onClick={() => downloadSession(sessionId)}
            className="px-4 py-2 text-sm bg-studio-panel border border-studio-border hover:border-studio-accent rounded-xl transition-colors"
          >
            {t.downloadAll}
          </button>
        </div>
      </header>

      {/* Main layout: Chat | Music panel */}
      <div className="flex-1 flex gap-4 p-4 overflow-hidden">
        {/* Chat panel */}
        <div className="w-96 flex-shrink-0 flex flex-col">
          <ChatPanel />
        </div>

        {/* Music panel */}
        <div className="flex-1 flex flex-col bg-studio-panel border border-studio-border rounded-2xl overflow-hidden">
          <div className="px-4 py-3 border-b border-studio-border text-sm font-semibold text-gray-300 flex-shrink-0">
            {t.tracks}
          </div>
          <TrackList />
          <PromptInput />
        </div>
      </div>
    </div>
  )
}
