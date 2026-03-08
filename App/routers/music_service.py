import json
import uuid
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse, FileResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..internal.db import get_db
from ..internal.config import get_settings
from ..models.sessions import MusicSession
from ..models.tracks import Track
from ..services.music_gen_service import generate_music
from ..services.track_splitter import split_tracks

router = APIRouter()
settings = get_settings()


class GenerateRequest(BaseModel):
    prompt: str
    duration: int = Field(default=30, ge=5, le=60)
    session_id: str
    use_trend: bool = False
    genre: str = "pop"


@router.post("/generate")
async def generate(req: GenerateRequest, db: AsyncSession = Depends(get_db)):
    # 세션 확인/생성
    session = await db.get(MusicSession, req.session_id)
    if not session:
        session = MusicSession(id=req.session_id)
        db.add(session)
        await db.commit()

    prompt = req.prompt
    if req.use_trend and settings.trend_enabled:
        try:
            from ..services.trend_agent.prompt_enhancer import enhance_prompt
            prompt = await enhance_prompt(req.prompt, req.genre)
        except Exception:
            pass  # fallback to original

    track = Track(
        session_id=req.session_id,
        prompt=prompt,
        duration=req.duration,
        status="generating",
    )
    db.add(track)
    await db.commit()
    await db.refresh(track)
    track_id = track.id

    async def progress_stream():
        import asyncio

        yield f"data: {json.dumps({'status': 'generating', 'progress': 5})}\n\n"
        await asyncio.sleep(0)  # flush

        # 음악 생성 (스레드 풀에서 실행 — 이벤트 루프 차단 없음)
        gen_task = asyncio.create_task(
            generate_music(prompt, req.duration, req.session_id)
        )

        # 생성 중 진행률 시뮬레이션 (CPU 기준 ~2-5분 소요)
        pct = 10
        while not gen_task.done():
            yield f"data: {json.dumps({'status': 'generating', 'progress': pct})}\n\n"
            await asyncio.sleep(3)
            if pct < 65:
                pct += 3

        try:
            wav_path = gen_task.result()
        except Exception as e:
            t = await db.get(Track, track_id)
            t.status = "error"
            await db.commit()
            yield f"data: {json.dumps({'status': 'error', 'detail': str(e)})}\n\n"
            return

        yield f"data: {json.dumps({'status': 'splitting', 'progress': 75})}\n\n"
        await asyncio.sleep(0)

        try:
            stem_paths = await split_tracks(wav_path)
        except Exception:
            stem_paths = {}

        # DB 업데이트
        t = await db.get(Track, track_id)
        t.master_path = wav_path
        t.vocals_path = stem_paths.get("vocals")
        t.drums_path = stem_paths.get("drums")
        t.bass_path = stem_paths.get("bass")
        t.other_path = stem_paths.get("other")
        t.status = "done"
        await db.commit()

        yield f"data: {json.dumps({'status': 'done', 'progress': 100, 'track_id': track_id})}\n\n"

    return StreamingResponse(
        progress_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.get("/tracks/{session_id}")
async def list_tracks(session_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Track).where(Track.session_id == session_id).order_by(Track.created_at.desc())
    )
    tracks = result.scalars().all()
    return [
        {
            "id": t.id,
            "prompt": t.prompt,
            "duration": t.duration,
            "status": t.status,
            "has_stems": bool(t.vocals_path),
            "created_at": t.created_at.isoformat() if t.created_at else None,
        }
        for t in tracks
    ]


@router.get("/audio/{track_id}/{stem}")
async def get_audio(track_id: int, stem: str, db: AsyncSession = Depends(get_db)):
    track = await db.get(Track, track_id)
    if not track:
        raise HTTPException(status_code=404, detail="Track not found")

    path_map = {
        "master": track.master_path,
        "vocals": track.vocals_path,
        "drums": track.drums_path,
        "bass": track.bass_path,
        "other": track.other_path,
    }
    path = path_map.get(stem)
    if not path:
        raise HTTPException(status_code=404, detail=f"Stem '{stem}' not available")

    return FileResponse(path, media_type="audio/wav", filename=f"{stem}.wav")
