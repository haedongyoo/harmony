import { useEffect, useRef } from 'react'
import WaveSurfer from 'wavesurfer.js'

interface Props {
  url: string
  height?: number
  color?: string
}

export default function WaveformViewer({ url, height = 60, color = '#7c3aed' }: Props) {
  const containerRef = useRef<HTMLDivElement>(null)
  const wsRef = useRef<WaveSurfer | null>(null)

  useEffect(() => {
    if (!containerRef.current) return

    wsRef.current = WaveSurfer.create({
      container: containerRef.current,
      waveColor: color,
      progressColor: '#a78bfa',
      height,
      barWidth: 2,
      barGap: 1,
      barRadius: 2,
      interact: false,
      url,
    })

    return () => {
      wsRef.current?.destroy()
    }
  }, [url, height, color])

  return <div ref={containerRef} className="w-full" />
}
