import { useEffect, useRef, useState } from 'react'
import WaveSurfer from 'wavesurfer.js'
import { getAudioUrl } from '../../api/music'
import { useT } from '../../hooks/useT'

interface Props {
  trackId: number
  stem: string
  label: string
}

export default function TrackPlayer({ trackId, stem, label }: Props) {
  const containerRef = useRef<HTMLDivElement>(null)
  const wsRef = useRef<WaveSurfer | null>(null)
  const [playing, setPlaying] = useState(false)
  const [ready, setReady] = useState(false)
  const t = useT()

  const url = getAudioUrl(trackId, stem)

  useEffect(() => {
    if (!containerRef.current) return

    const ws = WaveSurfer.create({
      container: containerRef.current,
      waveColor: '#4c1d95',
      progressColor: '#7c3aed',
      height: 48,
      barWidth: 2,
      barGap: 1,
      barRadius: 2,
      url,
    })

    ws.on('ready', () => setReady(true))
    ws.on('play', () => setPlaying(true))
    ws.on('pause', () => setPlaying(false))
    ws.on('finish', () => setPlaying(false))

    wsRef.current = ws
    return () => ws.destroy()
  }, [url])

  const toggle = () => wsRef.current?.playPause()

  return (
    <div className="flex items-center gap-3 px-3 py-2 bg-studio-bg rounded-xl border border-studio-border">
      <button
        onClick={toggle}
        disabled={!ready}
        className="w-8 h-8 flex items-center justify-center bg-studio-accent hover:bg-studio-accent-hover disabled:opacity-40 rounded-full text-white text-xs transition-colors flex-shrink-0"
        aria-label={playing ? t.pause : t.play}
      >
        {playing ? '⏸' : '▶'}
      </button>
      <div className="flex-1 min-w-0">
        <p className="text-xs text-gray-400 mb-1 uppercase tracking-wide">{label}</p>
        <div ref={containerRef} className="w-full" />
      </div>
    </div>
  )
}
