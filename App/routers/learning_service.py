import asyncio
from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ..internal.config import get_settings

router = APIRouter()
settings = get_settings()


class CollectionStatus(BaseModel):
    status: str
    timestamp: Optional[str] = None
    detail: Optional[str] = None


class CollectionStats(BaseModel):
    youtube_learning_enabled: bool
    scheduler_running: bool
    collection_interval_hours: int
    total_documents_indexed: int
    total_youtube_tracks: int
    last_run: CollectionStatus
    embedding_model: str
    rag_enabled: bool


class ManualCollectRequest(BaseModel):
    max_videos: int = Field(default=5, ge=1, le=50)


class ManualCollectResponse(BaseModel):
    message: str
    status: str


@router.get("/status")
async def learning_status() -> CollectionStats:
    """Get the current status of the YouTube learning system."""
    from ..services.youtube_learning.scheduler import get_scheduler, get_last_run_status
    from ..services.youtube_learning.rag_indexer import get_collection_stats
    from ..internal.db import AsyncSessionLocal
    from ..models.youtube_tracks import YouTubeTrack
    from sqlalchemy import func, select

    scheduler = get_scheduler()
    last_run = get_last_run_status()
    chroma_stats = get_collection_stats()

    track_count = 0
    try:
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(func.count(YouTubeTrack.id)))
            track_count = result.scalar() or 0
    except Exception:
        pass

    return CollectionStats(
        youtube_learning_enabled=settings.youtube_learning_enabled,
        scheduler_running=scheduler is not None and scheduler.running if scheduler else False,
        collection_interval_hours=settings.youtube_collection_interval_hours,
        total_documents_indexed=chroma_stats.get("total_documents", 0),
        total_youtube_tracks=track_count,
        last_run=CollectionStatus(**last_run),
        embedding_model=settings.embedding_model,
        rag_enabled=settings.rag_enabled,
    )


@router.post("/collect")
async def trigger_collection(req: ManualCollectRequest) -> ManualCollectResponse:
    """Manually trigger a YouTube collection run."""
    if not settings.youtube_learning_enabled:
        raise HTTPException(status_code=503, detail="YouTube learning system is disabled")

    from ..services.youtube_learning.scheduler import run_manual_collection

    asyncio.create_task(run_manual_collection(req.max_videos))

    return ManualCollectResponse(
        message=f"Collection started for up to {req.max_videos} videos",
        status="started",
    )


@router.post("/toggle")
async def toggle_rag(enabled: bool = True):
    """Enable or disable RAG context injection in chat (runtime toggle)."""
    object.__setattr__(settings, "rag_enabled", enabled)
    return {"rag_enabled": enabled}


@router.get("/recent")
async def recent_tracks(limit: int = 20):
    """List recently processed YouTube tracks."""
    from ..internal.db import AsyncSessionLocal
    from ..models.youtube_tracks import YouTubeTrack
    from sqlalchemy import select

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(YouTubeTrack)
            .order_by(YouTubeTrack.created_at.desc())
            .limit(limit)
        )
        tracks = result.scalars().all()

        return [
            {
                "video_id": t.video_id,
                "title": t.title,
                "artist": t.artist,
                "genre": t.genre,
                "bpm": t.bpm,
                "key": t.key,
                "mood": t.mood,
                "energy": t.energy,
                "view_count": t.view_count,
                "processed_at": t.processed_at.isoformat() if t.processed_at else None,
            }
            for t in tracks
        ]
