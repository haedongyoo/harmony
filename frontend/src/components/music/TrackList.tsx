import { useQuery } from '@tanstack/react-query'
import { fetchTracks } from '../../api/music'
import { downloadTrack } from '../../api/export'
import { useMusicStore } from '../../stores/musicStore'
import { useT } from '../../hooks/useT'
import TrackPlayer from './TrackPlayer'

export default function TrackList() {
  const { sessionId, generation } = useMusicStore()
  const t = useT()

  const stems = [
    { key: 'master', label: t.stemMaster },
    { key: 'vocals', label: t.stemVocals },
    { key: 'drums', label: t.stemDrums },
    { key: 'bass', label: t.stemBass },
    { key: 'other', label: t.stemOther },
  ]

  const { data: tracks = [] } = useQuery({
    queryKey: ['tracks', sessionId],
    queryFn: () => fetchTracks(sessionId),
    refetchInterval: generation.status === 'done' ? false : 5000,
  })

  if (tracks.length === 0) {
    return (
      <div className="flex-1 flex items-center justify-center text-gray-500 text-sm">
        {t.noTracks}
      </div>
    )
  }

  return (
    <div className="flex-1 overflow-y-auto space-y-4 p-4">
      {tracks.map((track) => (
        <div key={track.id} className="bg-studio-panel border border-studio-border rounded-2xl p-4">
          <div className="flex items-start justify-between mb-3">
            <div className="flex-1 min-w-0">
              <p className="text-xs text-gray-400 truncate">{track.prompt}</p>
              <p className="text-xs text-gray-600 mt-1">{track.duration}{t.seconds} · {track.created_at?.slice(0, 10)}</p>
            </div>
            {track.status === 'done' && (
              <button
                onClick={() => downloadTrack(sessionId, track.id)}
                className="ml-3 px-3 py-1.5 text-xs bg-studio-accent hover:bg-studio-accent-hover rounded-lg transition-colors flex-shrink-0"
              >
                {t.zipDownload}
              </button>
            )}
          </div>

          {track.status === 'done' ? (
            <div className="space-y-2">
              {stems.map(({ key, label }) => (
                <TrackPlayer key={key} trackId={track.id} stem={key} label={label} />
              ))}
            </div>
          ) : (
            <div className="text-center text-xs text-gray-500 py-4">
              {track.status === 'error' ? t.generationFailed : t.generating}
            </div>
          )}
        </div>
      ))}
    </div>
  )
}
