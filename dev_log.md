# Development Log

## Session: 2026-03-07 — YouTube Learning System & Initial Setup

### What Was Built

A complete **YouTube-based Continuous Learning System** with RAG pipeline for the Harmony AI Music Studio.

| Component | Files | Status |
|-----------|-------|--------|
| YouTube Collector (yt-dlp) | `youtube_collector.py` | Built, 403 errors from YouTube |
| Audio Analyzer (librosa) | `audio_analyzer.py` | Working |
| Knowledge Builder | `knowledge_builder.py` | Working |
| ChromaDB RAG Indexer | `rag_indexer.py` | Working |
| RAG Retriever | `rag_retriever.py` | Working |
| APScheduler | `scheduler.py` | Running (6h interval) |
| Learning API | `learning_service.py` | 4 endpoints working |
| Chat RAG Integration | `ollama_client.py` | Working |
| Test Suite | 7 test files, 83+ tests | All passing |

### Session Fixes

- Recreated broken venv (Python symlink issue)
- Installed `greenlet`, `sentencepiece`, `pkg-config`, `ffmpeg`, `audiocraft` + all deps
- xformers stub installed for macOS compatibility
- Made `torchaudio`/`demucs` imports lazy (app starts without heavy ML libs)
- Fixed music generation stuck at 0% (moved `model.generate()` to thread pool, added SSE progress polling)
- Fixed hardcoded trend values ("120-130 BPM, 808 bass...") in `trend_analyzer.py`
- Added SSE no-cache headers to prevent buffering

### Known Issues

1. **YouTube 403 errors** — yt-dlp blocked by YouTube anti-scraping. Needs `yt-dlp` update or YouTube API v3 fallback
2. **Python 3.9 deprecation warnings** — System Python is 3.9.6, should upgrade to 3.10+

### Architecture

```
Background (APScheduler, every 6h):
  youtube_collector.py (yt-dlp) -> audio + metadata
       |
  audio_analyzer.py (librosa) -> BPM, key, energy, mood
       |
  knowledge_builder.py -> structured text documents
       |
  rag_indexer.py (sentence-transformers) -> ChromaDB embeddings

Chat flow (RAG-enhanced):
  User message -> rag_retriever.py -> ChromaDB query (top 5)
       |
  ollama_client.chat_stream_with_rag() -> system prompt + RAG context
       |
  Streaming response -> frontend
```

### New Files Created

```
App/
├── models/youtube_tracks.py
├── routers/learning_service.py
└── services/youtube_learning/
    ├── __init__.py
    ├── youtube_collector.py
    ├── audio_analyzer.py
    ├── knowledge_builder.py
    ├── rag_indexer.py
    ├── rag_retriever.py
    └── scheduler.py

tests/
├── conftest.py
├── test_youtube_collector.py
├── test_audio_analyzer.py
├── test_knowledge_builder.py
├── test_scheduler.py
├── test_learning_service.py
├── test_rag_pipeline.py
└── test_ollama_rag_integration.py
```

### Modified Files

- `App/main.py` — Lifespan hooks for scheduler start/stop, learning_service router
- `App/internal/config.py` — 11 new YouTube/ChromaDB/RAG settings
- `App/services/ollama_client.py` — Added `chat_stream_with_rag()` function
- `App/routers/chat_service.py` — Conditional RAG-enhanced chat stream
- `App/routers/music_service.py` — SSE progress polling with thread pool generation
- `App/services/music_gen_service.py` — `model.generate()` moved to `run_in_executor`
- `App/services/track_splitter.py` — Lazy imports for torchaudio/demucs
- `App/services/trend_agent/trend_analyzer.py` — Removed hardcoded example values
- `requirements.txt` — Added yt-dlp, chromadb, sentence-transformers, librosa, apscheduler, soundfile
- `env.example` — New environment variables
- `Dockerfile.backend` — New dependencies and directories
- `docker-compose.yml` — New volumes and env vars

### Dependencies Added

```
yt-dlp>=2024.1.0
chromadb>=0.4.22
sentence-transformers>=2.2.2
librosa>=0.10.1
apscheduler>=3.10.4
soundfile>=0.12.1
```

### API Endpoints Added

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/learning/status` | System status: scheduler state, doc count, last run |
| POST | `/api/learning/collect` | Manual trigger: `{ max_videos: 5 }` |
| POST | `/api/learning/toggle?enabled=true` | Runtime RAG on/off toggle |
| GET | `/api/learning/recent?limit=20` | Recently processed YouTube tracks |

### Recommended Next Steps

1. Fix YouTube collector (upgrade yt-dlp, add YouTube API v3 key)
2. Run manual collection to seed ChromaDB: `POST /api/learning/collect`
3. Upgrade Python to 3.10+
4. Tune RAG cosine distance thresholds with real data
5. Add Prometheus metrics for monitoring

### Git

- Initial commit: `de1ca2c` (86 files, 7,941 lines)
- Remote: https://github.com/haedongyoo/harmony (public)
