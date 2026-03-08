from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..internal.db import get_db
from ..models.tracks import Track
from ..services.audio_export import build_zip

router = APIRouter()


@router.get("/{session_id}")
async def export_session(session_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Track).where(Track.session_id == session_id, Track.status == "done")
    )
    tracks = result.scalars().all()

    if not tracks:
        raise HTTPException(status_code=404, detail="No completed tracks found for this session")

    # 최신 트랙만 내보내기 (단일 트랙 기준)
    track = tracks[0]
    track_paths = {
        "master": track.master_path,
        "vocals": track.vocals_path,
        "drums": track.drums_path,
        "bass": track.bass_path,
        "other": track.other_path,
    }

    zip_bytes = build_zip(session_id, track_paths)
    filename = f"music_studio_export_{session_id}.zip"

    return Response(
        content=zip_bytes,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/{session_id}/{track_id}")
async def export_track(session_id: str, track_id: int, db: AsyncSession = Depends(get_db)):
    track = await db.get(Track, track_id)
    if not track or track.session_id != session_id:
        raise HTTPException(status_code=404, detail="Track not found")
    if track.status != "done":
        raise HTTPException(status_code=400, detail="Track is not ready")

    track_paths = {
        "master": track.master_path,
        "vocals": track.vocals_path,
        "drums": track.drums_path,
        "bass": track.bass_path,
        "other": track.other_path,
    }

    zip_bytes = build_zip(session_id, track_paths)
    filename = f"music_studio_export_{session_id}.zip"

    return Response(
        content=zip_bytes,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
