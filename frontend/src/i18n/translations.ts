export type Lang = 'ko' | 'en'

const translations = {
  ko: {
    // Header / Studio
    appTitle: 'AI Music Studio',
    downloadAll: '세션 전체 다운로드',

    // ChatPanel
    aiChat: 'AI 채팅',
    chatEmptyState: '원하는 음악에 대해 이야기해보세요',

    // ChatInput
    chatPlaceholder: '음악에 대해 이야기해보세요... (Shift+Enter: 줄바꿈)',
    send: '전송',

    // PromptInput
    tracks: '트랙',
    promptPlaceholder: '음악 프롬프트를 입력하세요... (예: upbeat pop, 120 BPM, synthesizer)',
    duration: '길이',
    seconds: '초',
    applyTrend: '트렌드 반영',
    generateMusic: '음악 생성',
    generatingMusic: '음악 생성 중',
    splittingTracks: '트랙 분리 중',

    // TrackList
    noTracks: '생성된 트랙이 없습니다',
    zipDownload: 'ZIP 다운로드',
    generationFailed: '생성 실패',
    generating: '생성 중...',

    // Stems
    stemMaster: '전체',
    stemVocals: '보컬',
    stemDrums: '드럼',
    stemBass: '베이스',
    stemOther: '기타 악기',

    // TrackPlayer
    play: '재생',
    pause: '일시정지',

    // Export page
    backToStudio: '← 스튜디오로',
    multitrackDownload: '멀티트랙 다운로드',
    downloadAllZip: '전체 ZIP 다운로드',
    loading: '불러오는 중...',
    noCompletedTracks: '완료된 트랙이 없습니다.',
    downloadTrack: '이 트랙 다운로드',

    // Error
    errorPrefix: '오류',

    // Genres
    genres: {
      pop: 'pop',
      rock: 'rock',
      hiphop: 'hiphop',
      electronic: 'electronic',
      jazz: 'jazz',
      classical: 'classical',
    },
  },
  en: {
    appTitle: 'AI Music Studio',
    downloadAll: 'Download All',

    aiChat: 'AI Chat',
    chatEmptyState: 'Tell me about the music you want',

    chatPlaceholder: 'Talk about music... (Shift+Enter: new line)',
    send: 'Send',

    tracks: 'Tracks',
    promptPlaceholder: 'Enter a music prompt... (e.g. upbeat pop, 120 BPM, synthesizer)',
    duration: 'Duration',
    seconds: 'sec',
    applyTrend: 'Apply Trends',
    generateMusic: 'Generate Music',
    generatingMusic: 'Generating music',
    splittingTracks: 'Splitting tracks',

    noTracks: 'No tracks generated',
    zipDownload: 'Download ZIP',
    generationFailed: 'Generation failed',
    generating: 'Generating...',

    stemMaster: 'Master',
    stemVocals: 'Vocals',
    stemDrums: 'Drums',
    stemBass: 'Bass',
    stemOther: 'Other',

    play: 'Play',
    pause: 'Pause',

    backToStudio: '← Back to Studio',
    multitrackDownload: 'Multitrack Download',
    downloadAllZip: 'Download All as ZIP',
    loading: 'Loading...',
    noCompletedTracks: 'No completed tracks.',
    downloadTrack: 'Download Track',

    errorPrefix: 'Error',

    genres: {
      pop: 'pop',
      rock: 'rock',
      hiphop: 'hiphop',
      electronic: 'electronic',
      jazz: 'jazz',
      classical: 'classical',
    },
  },
} as const

export type Translations = typeof translations[Lang]
export default translations
