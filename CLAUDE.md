# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**AI Music Studio** — 사용자의 프롬프트를 통해 음악을 생성하고, 악기별 멀티트랙으로 다운로드할 수 있는 웹 애플리케이션. Ollama 기반의 AI 채팅 인터페이스를 통해 사용자와 대화하며 음악을 제작한다.

## Tech Stack

| Layer | 기술 |
|-------|------|
| Frontend | React 18 + TypeScript + Vite |
| Backend | FastAPI (Python 3.11+) |
| AI Chat | Ollama (로컬 LLM) |
| Music Generation | MusicGen (Meta, via audiocraft) |
| Audio Processing | pydub, ffmpeg |
| Trend Agent | Last.fm API + Deezer API + MusicBrainz API |
| Styling | Tailwind CSS |
| State Management | Zustand |
| API Client | TanStack Query (React Query v5) |

## Commands

### Backend (FastAPI)

```bash
# 최초 세팅
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp env.example App/.env

# 실행 (프로젝트 루트에서)
uvicorn App.main:app --host 0.0.0.0 --port 8001 --reload

# 테스트
pytest
pytest tests/ -v
```

### Frontend (React + Vite)

```bash
cd frontend
npm install
npm run dev       # 개발 서버: http://localhost:5173 (/api → 백엔드 프록시)
npm run build     # 프로덕션 빌드 → frontend/dist/
```

### Ollama 세팅

```bash
brew install ollama
ollama pull llama3.2         # 기본 채팅 모델
ollama serve                 # 기본 포트: http://localhost:11434
```

### ffmpeg (오디오 처리 필수)

```bash
brew install ffmpeg
```

### Docker

```bash
# 전체 스택 빌드 & 실행 (Ollama 모델 자동 pull 포함)
docker compose up --build

# 백그라운드 실행
docker compose up --build -d

# 로그 확인
docker compose logs -f backend
docker compose logs -f ollama

# 중지
docker compose down

# 볼륨까지 삭제 (DB, 생성 음악, 모델 캐시 전부 초기화)
docker compose down -v
```

**포트 구성 (Docker)**
| 서비스 | 호스트 포트 | 설명 |
|--------|------------|------|
| frontend | 5173 | React UI (Nginx) |
| backend | 8001 | FastAPI (직접 접근 가능) |
| ollama | 11434 | Ollama API |

**볼륨**
- `ollama_models` — llama3.2 모델
- `audio_outputs` — 생성된 WAV 파일
- `db_data` — SQLite DB
- `hf_cache` — MusicGen 모델 캐시 (~1.5GB, 최초 음악 생성 시 다운로드)
- `torch_cache` — Demucs 모델 캐시

**xformers 참고**: real xformers는 CPU/macOS 환경에서 빌드 불가. `docker/xformers_stub/`의 stub 패키지로 대체 (torch SDPA fallback).

---

## Architecture

```
harmony/
├── App/                          # FastAPI 백엔드
│   ├── internal/
│   │   ├── config.py             # Pydantic settings (App/.env 읽기)
│   │   └── db.py                 # DB 엔진, 세션
│   ├── models/                   # SQLAlchemy ORM
│   │   ├── sessions.py           # 음악 세션 (사용자별 제작 히스토리)
│   │   ├── tracks.py             # 생성된 트랙 메타데이터
│   │   └── chat_messages.py      # 채팅 히스토리
│   ├── routers/                  # API 라우터
│   │   ├── chat_service.py       # /api/chat — Ollama 채팅
│   │   ├── music_service.py      # /api/music — 음악 생성 및 트랙 관리
│   │   ├── export_service.py     # /api/export — 멀티트랙 ZIP 다운로드
│   │   └── trend_service.py      # /api/trend — 트렌드 조회 및 프롬프트 강화
│   ├── services/                 # 비즈니스 로직
│   │   ├── ollama_client.py      # Ollama LLM 클라이언트
│   │   ├── music_gen_service.py  # MusicGen 음악 생성 서비스
│   │   ├── track_splitter.py     # 악기별 트랙 분리 (Demucs)
│   │   ├── audio_export.py       # pydub 기반 오디오 파일 처리
│   │   └── trend_agent/          # 트렌드 수집 에이전트
│   │       ├── trend_crawler.py      # Last.fm / Deezer / MusicBrainz 수집
│   │       ├── trend_analyzer.py     # Ollama로 트렌드 분석 → 음악 특성 추출
│   │       ├── prompt_enhancer.py    # 트렌드 + 사용자 입력 → 강화된 프롬프트
│   │       └── trend_cache.py        # 수집 데이터 캐싱 (24시간 TTL)
│   └── main.py                   # FastAPI 앱 진입점
├── frontend/                     # React 18 + TypeScript + Vite
│   └── src/
│       ├── pages/
│       │   ├── Studio.tsx        # 메인 음악 제작 화면
│       │   └── Export.tsx        # 멀티트랙 다운로드 화면
│       ├── components/
│       │   ├── chat/
│       │   │   ├── ChatPanel.tsx       # 채팅 UI 컨테이너
│       │   │   ├── ChatMessage.tsx     # 개별 메시지 버블
│       │   │   └── ChatInput.tsx       # 입력창 + 전송 버튼
│       │   └── music/
│       │       ├── TrackList.tsx       # 생성된 트랙 목록
│       │       ├── TrackPlayer.tsx     # 개별 트랙 재생 컨트롤
│       │       ├── WaveformViewer.tsx  # 오디오 파형 시각화
│       │       └── PromptInput.tsx     # 음악 생성 프롬프트 입력
│       ├── stores/
│       │   ├── chatStore.ts      # Zustand: 채팅 상태
│       │   └── musicStore.ts     # Zustand: 트랙 및 세션 상태
│       └── api/                  # TanStack Query API 클라이언트
│           ├── chat.ts
│           ├── music.ts
│           └── export.ts
├── outputs/                      # 생성된 오디오 파일 저장소
├── env.example
├── requirements.txt
├── docker-compose.yml
└── CLAUDE.md
```

---

## Key Features & Implementation Rules

### 1. AI 채팅 (Ollama)

- 엔드포인트: `POST /api/chat`
- 요청: `{ message: string, session_id: string, history: Message[] }`
- 응답: 스트리밍(`text/event-stream`) 방식으로 토큰 단위 전송
- Ollama 모델: `OLLAMA_CHAT_MODEL` 환경변수 따를 것 (기본값: `llama3.2`)
- 채팅 히스토리는 전체를 매 요청마다 포함해서 전송 (무상태 서버)
- 시스템 프롬프트: "당신은 음악 제작 전문가 AI입니다. 사용자가 원하는 음악을 구체적인 프롬프트로 변환해 주세요."
- AI가 음악 생성 프롬프트를 제안할 경우, 응답에 `[MUSIC_PROMPT: ...]` 태그 포함 → 프론트에서 파싱하여 자동으로 PromptInput에 채워줌

### 2. 음악 생성

- 엔드포인트: `POST /api/music/generate`
- 요청: `{ prompt: string, duration: int, session_id: string }`
- 음악 생성 라이브러리: Meta `audiocraft` (MusicGen 모델)
- 기본 생성 시간: 30초 (`duration` 파라미터로 조정, 최대 60초)
- 생성된 오디오는 `outputs/{session_id}/` 폴더에 WAV로 저장
- 생성 완료 후 `track_splitter.py`로 악기별 트랙 자동 분리 (Demucs 사용)
  - 분리 트랙: `vocals`, `drums`, `bass`, `other` (기본 4트랙)
- 긴 생성 시간을 고려해 SSE로 진행 상태(progress %) 전송

### 3. 멀티트랙 다운로드

- 엔드포인트: `GET /api/export/{session_id}`
- 각 악기 트랙을 개별 WAV 파일로 묶어 ZIP으로 반환
- 파일명 규칙: `{session_id}_{instrument}_{timestamp}.wav`
- ZIP 파일명: `music_studio_export_{session_id}.zip`
- 다운로드 전 트랙별 미리듣기 가능하게 할 것

### 4. 세션 관리

- 사용자별 `session_id` (UUID)로 작업 구분
- 세션에 연결된 채팅 히스토리 + 생성된 트랙 목록 보존
- 세션 데이터는 SQLite (개발) / PostgreSQL (프로덕션) 에 저장

---

## 트렌드 에이전트 (Trend Agent)

### 역할

모델을 재학습하는 대신, 최신 차트/장르 트렌드 데이터를 수집하여 MusicGen 프롬프트를 자동 강화하는 서브 에이전트.

```
사용자: "요즘 유행하는 팝 만들어줘"
         ↓
trend_crawler.py — Deezer/Last.fm에서 현재 팝 차트 Top 50 수집
         ↓
trend_analyzer.py — Ollama로 분석: BPM 범위, 악기 구성, 분위기 키워드 추출
         ↓
prompt_enhancer.py — 원본 프롬프트 + 트렌드 특성 → 강화된 MusicGen 프롬프트
         ↓
"upbeat pop, 120 BPM, synthesizer, 808 bass, bright vocals, 2025 trend"
```

### 구현 규칙

- `trend_crawler.py`는 Deezer → Last.fm → MusicBrainz 순서로 호출 (Deezer가 키 불필요라 우선)
- 수집한 트렌드 데이터는 `trend_cache.py`에서 SQLite에 캐싱, TTL 24시간
- TTL 만료 전엔 캐시 데이터 사용 (외부 API 불필요한 호출 방지)
- `trend_analyzer.py`는 기존 `ollama_client.py` 재사용하여 트렌드 텍스트 분석
- `prompt_enhancer.py`는 사용자 원본 의도를 훼손하지 않도록 트렌드 요소를 **추가**만 할 것 (덮어쓰기 금지)
- 트렌드 강화 여부는 사용자가 채팅에서 "트렌드 반영해줘" 또는 `use_trend: true` 파라미터로 선택 가능하게 할 것
- 에이전트 오류 시 원본 프롬프트로 fallback (트렌드 에이전트 실패가 음악 생성을 막으면 안 됨)

---

## Frontend 규칙

- 컴포넌트는 함수형 + React Hooks만 사용 (클래스 컴포넌트 금지)
- 파일명: `PascalCase.tsx` (컴포넌트), `camelCase.ts` (유틸/스토어)
- API 호출은 반드시 `src/api/` 폴더의 함수를 통해서만 할 것 (직접 fetch 금지)
- 전역 상태는 Zustand 사용 (Context API 사용 금지)
- 서버 상태(API 데이터)는 TanStack Query 사용
- 스타일은 Tailwind CSS만 사용 (인라인 style 속성 금지)
- 오디오 파형 시각화는 `WaveSurfer.js` 사용
- 스트리밍 응답(채팅/음악 생성 진행률)은 `EventSource` API 사용

---

## Backend 규칙

- 라우터는 `routers/` 폴더, 비즈니스 로직은 `services/` 폴더로 분리
- 새로운 LLM/오디오 클라이언트는 기존 `ollama_client.py` 패턴 따를 것
- 오디오 파일 직접 응답 시 `FileResponse` 사용
- ZIP 스트리밍은 `StreamingResponse` + `zipfile` 모듈 사용
- 모든 엔드포인트에 Pydantic 요청/응답 모델 정의 필수
- 오류 응답 형식 통일: `{ "error": "...", "detail": "..." }`

---

## Environment Variables

`App/.env` (env.example에서 복사):

```env
# 필수
DATABASE_URL=sqlite:///./music_studio.db

# Ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_CHAT_MODEL=llama3.2

# 음악 생성
MUSIC_OUTPUT_PATH=./outputs
MAX_MUSIC_DURATION=60

# 트렌드 에이전트
LASTFM_API_KEY=           # https://www.last.fm/api/account/create 에서 무료 발급
TREND_CACHE_TTL=86400     # 캐시 유효시간 (초), 기본 24시간
TREND_ENABLED=true        # false로 설정 시 트렌드 에이전트 비활성화

# 선택
LOG_LEVEL=INFO
```

---

## Audio Processing Notes

- 모든 오디오 중간 처리는 WAV (44100Hz, stereo) 기준으로 통일
- 최종 다운로드 파일도 WAV로 제공 (MP3 변환은 선택 옵션)
- ffmpeg이 시스템에 설치되어 있어야 pydub가 정상 동작함
- Demucs 트랙 분리는 GPU 있으면 자동으로 CUDA 사용, 없으면 CPU fallback
