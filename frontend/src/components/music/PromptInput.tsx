import { useState, useEffect } from 'react'
import { useMusicStore } from '../../stores/musicStore'
import { generateMusic } from '../../api/music'
import { useT } from '../../hooks/useT'

export default function PromptInput() {
  const { sessionId, generation, setGeneration, pendingPrompt, clearPendingPrompt } = useMusicStore()
  const [prompt, setPrompt] = useState('')
  const [duration, setDuration] = useState(30)
  const [useTrend, setUseTrend] = useState(false)
  const [genre, setGenre] = useState('pop')
  const t = useT()

  // AI 채팅에서 [MUSIC_PROMPT: ...] 태그로 자동 채워주기
  useEffect(() => {
    if (pendingPrompt) {
      setPrompt(pendingPrompt)
      clearPendingPrompt()
    }
  }, [pendingPrompt, clearPendingPrompt])

  const isGenerating = generation.status === 'generating' || generation.status === 'splitting'

  const handleGenerate = () => {
    if (!prompt.trim() || isGenerating) return

    setGeneration({ status: 'generating', progress: 0, error: null })

    generateMusic({
      prompt: prompt.trim(),
      duration,
      sessionId,
      useTrend,
      genre,
      onProgress: (status, pct) => {
        setGeneration({
          status: status as 'generating' | 'splitting',
          progress: pct,
        })
      },
      onDone: () => setGeneration({ status: 'done', progress: 100 }),
      onError: (err) => setGeneration({ status: 'error', progress: 0, error: err }),
    })
  }

  return (
    <div className="p-4 border-t border-studio-border space-y-3">
      {generation.status === 'error' && (
        <p className="text-xs text-red-400">{generation.error}</p>
      )}

      <textarea
        className="w-full bg-studio-bg border border-studio-border rounded-xl px-3 py-2 text-sm text-white resize-none outline-none focus:border-studio-accent transition-colors"
        rows={3}
        placeholder={t.promptPlaceholder}
        value={prompt}
        onChange={(e) => setPrompt(e.target.value)}
        disabled={isGenerating}
      />

      <div className="flex items-center gap-3 flex-wrap">
        <div className="flex items-center gap-2">
          <label className="text-xs text-gray-400">{t.duration}</label>
          <input
            type="number"
            min={5}
            max={60}
            value={duration}
            onChange={(e) => setDuration(Number(e.target.value))}
            className="w-16 bg-studio-bg border border-studio-border rounded-lg px-2 py-1 text-xs text-white text-center outline-none focus:border-studio-accent"
            disabled={isGenerating}
          />
          <span className="text-xs text-gray-400">{t.seconds}</span>
        </div>

        <label className="flex items-center gap-2 text-xs text-gray-400 cursor-pointer">
          <input
            type="checkbox"
            checked={useTrend}
            onChange={(e) => setUseTrend(e.target.checked)}
            className="accent-studio-accent"
            disabled={isGenerating}
          />
          {t.applyTrend}
        </label>

        {useTrend && (
          <select
            value={genre}
            onChange={(e) => setGenre(e.target.value)}
            className="bg-studio-bg border border-studio-border rounded-lg px-2 py-1 text-xs text-white outline-none focus:border-studio-accent"
            disabled={isGenerating}
          >
            {['pop', 'rock', 'hiphop', 'electronic', 'jazz', 'classical'].map((g) => (
              <option key={g} value={g}>{g}</option>
            ))}
          </select>
        )}
      </div>

      <button
        onClick={handleGenerate}
        disabled={isGenerating || !prompt.trim()}
        className="w-full py-2.5 bg-studio-accent hover:bg-studio-accent-hover disabled:opacity-40 disabled:cursor-not-allowed rounded-xl text-sm font-semibold transition-colors"
      >
        {isGenerating
          ? `${generation.status === 'generating' ? t.generatingMusic : t.splittingTracks} ${generation.progress}%`
          : t.generateMusic}
      </button>
    </div>
  )
}
