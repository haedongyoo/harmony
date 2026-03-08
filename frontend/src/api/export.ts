export function downloadSession(sessionId: string): void {
  const url = `/api/export/${sessionId}`
  const a = document.createElement('a')
  a.href = url
  a.download = `music_studio_export_${sessionId}.zip`
  a.click()
}

export function downloadTrack(sessionId: string, trackId: number): void {
  const url = `/api/export/${sessionId}/${trackId}`
  const a = document.createElement('a')
  a.href = url
  a.download = `music_studio_export_${sessionId}.zip`
  a.click()
}
