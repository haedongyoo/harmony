import { useParams, Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { fetchTracks } from '../api/music'
import { downloadTrack, downloadSession } from '../api/export'
import TrackPlayer from '../components/music/TrackPlayer'
import LangToggle from '../components/ui/LangToggle'
import { useT } from '../hooks/useT'

export default function Export() {
  const { sessionId } = useParams<{ sessionId: string }>()
  const t = useT()

  const stems = [
    { key: 'master', label: t.stemMaster },
    { key: 'vocals', label: t.stemVocals },
    { key: 'drums', label: t.stemDrums },
    { key: 'bass', label: t.stemBass },
    { key: 'other', label: t.stemOther },
  ]

  const { data: tracks = [], isLoading } = useQuery({
    queryKey: ['tracks', sessionId],
    queryFn: () => fetchTracks(sessionId!),
    enabled: !!sessionId,
  })

  const doneTracks = tracks.filter((track) => track.status === 'done')

  return (
    <div className="min-h-screen bg-studio-bg p-6">
      <div className="max-w-3xl mx-auto">
        <div className="flex items-center gap-4 mb-8">
          <Link to="/studio" className="text-sm text-gray-400 hover:text-white transition-colors">
            {t.backToStudio}
          </Link>
          <h1 className="text-xl font-bold">{t.multitrackDownload}</h1>
          <div className="ml-auto flex items-center gap-3">
            <LangToggle />
            {doneTracks.length > 0 && (
              <button
                onClick={() => downloadSession(sessionId!)}
                className="px-4 py-2 text-sm bg-studio-accent hover:bg-studio-accent-hover rounded-xl transition-colors"
              >
                {t.downloadAllZip}
              </button>
            )}
          </div>
        </div>

        {isLoading && <p className="text-gray-500 text-sm">{t.loading}</p>}

        {!isLoading && doneTracks.length === 0 && (
          <p className="text-gray-500 text-sm">{t.noCompletedTracks}</p>
        )}

        <div className="space-y-6">
          {doneTracks.map((track) => (
            <div key={track.id} className="bg-studio-panel border border-studio-border rounded-2xl p-5">
              <div className="flex items-start justify-between mb-4">
                <div>
                  <p className="text-sm text-gray-300 font-medium">{track.prompt}</p>
                  <p className="text-xs text-gray-500 mt-1">
                    {track.duration}{t.seconds} · {track.created_at?.slice(0, 10)}
                  </p>
                </div>
                <button
                  onClick={() => downloadTrack(sessionId!, track.id)}
                  className="px-3 py-1.5 text-xs bg-studio-accent hover:bg-studio-accent-hover rounded-lg transition-colors"
                >
                  {t.downloadTrack}
                </button>
              </div>

              <div className="space-y-2">
                {stems.map(({ key, label }) => (
                  <TrackPlayer key={key} trackId={track.id} stem={key} label={label} />
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
