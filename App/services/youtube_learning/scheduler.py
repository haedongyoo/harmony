import logging
import asyncio
from pathlib import Path
from typing import Optional
from datetime import datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from ...internal.config import get_settings
from ...internal.db import AsyncSessionLocal

settings = get_settings()
logger = logging.getLogger(__name__)

_scheduler: Optional[AsyncIOScheduler] = None
_last_run_status: dict = {"status": "never_run", "timestamp": None, "detail": None}


def get_scheduler() -> Optional[AsyncIOScheduler]:
    return _scheduler


def get_last_run_status() -> dict:
    return _last_run_status.copy()


async def start_scheduler():
    """Initialize and start the APScheduler. Called from FastAPI lifespan."""
    global _scheduler

    if not settings.youtube_learning_enabled:
        logger.info("YouTube learning system is disabled")
        return

    _scheduler = AsyncIOScheduler()

    _scheduler.add_job(
        run_collection_pipeline,
        trigger=IntervalTrigger(hours=settings.youtube_collection_interval_hours),
        id="youtube_collection",
        name="YouTube Music Collection",
        replace_existing=True,
        max_instances=1,
        misfire_grace_time=3600,
    )

    _scheduler.start()
    logger.info(
        f"YouTube learning scheduler started "
        f"(interval: {settings.youtube_collection_interval_hours}h)"
    )

    # Run first collection after a short delay to let app finish starting
    asyncio.get_event_loop().call_later(
        30, lambda: asyncio.ensure_future(run_collection_pipeline())
    )


async def stop_scheduler():
    """Graceful shutdown. Called from FastAPI lifespan."""
    global _scheduler
    if _scheduler:
        _scheduler.shutdown(wait=False)
        _scheduler = None
        logger.info("YouTube learning scheduler stopped")


async def run_collection_pipeline():
    """
    Full pipeline: collect -> analyze -> build docs -> index.
    This is the main scheduled job.
    """
    global _last_run_status
    _last_run_status = {
        "status": "running",
        "timestamp": datetime.utcnow().isoformat(),
        "detail": None,
    }

    logger.info("Starting YouTube collection pipeline...")

    try:
        from .youtube_collector import collect_videos
        from .audio_analyzer import analyze_audio, derive_mood_from_features
        from .knowledge_builder import build_document, build_metadata
        from .rag_indexer import index_document
        from ...models.youtube_tracks import YouTubeTrack

        # Step 1: Collect videos
        videos = await collect_videos()
        if not videos:
            _last_run_status = {
                "status": "completed",
                "timestamp": datetime.utcnow().isoformat(),
                "detail": "No new videos found",
            }
            logger.info("No new videos collected")
            return

        processed_count = 0
        error_count = 0

        async with AsyncSessionLocal() as db:
            # Get already-processed video IDs
            from sqlalchemy import select

            result = await db.execute(select(YouTubeTrack.video_id))
            existing_ids = {row[0] for row in result.fetchall()}

            for video in videos:
                video_id = video.get("video_id")
                if not video_id or video_id in existing_ids:
                    continue

                try:
                    audio_path = video.get("audio_path")

                    # Step 2: Analyze audio features
                    features = {}
                    mood = "unknown"
                    if audio_path and Path(audio_path).exists():
                        features = await analyze_audio(audio_path)
                        mood = await derive_mood_from_features(
                            features, video.get("title", ""), video.get("genre", "pop")
                        )

                    # Step 3: Build text document for embedding
                    document = build_document(video, features, mood)
                    metadata = build_metadata(video, features, mood)

                    # Step 4: Index in ChromaDB
                    chroma_id = index_document(video_id, document, metadata)

                    # Step 5: Save to SQLite for tracking
                    yt_track = YouTubeTrack(
                        video_id=video_id,
                        title=video.get("title", "")[:512],
                        artist=video.get("artist", "")[:256],
                        channel=video.get("channel", "")[:256],
                        description=video.get("description", "")[:2000],
                        tags=str(video.get("tags", [])),
                        genre=video.get("genre"),
                        view_count=video.get("view_count"),
                        duration_seconds=video.get("duration_seconds"),
                        upload_date=video.get("upload_date"),
                        bpm=features.get("bpm"),
                        key=features.get("key"),
                        energy=features.get("energy"),
                        danceability=features.get("danceability"),
                        spectral_centroid=features.get("spectral_centroid"),
                        mood=mood,
                        is_embedded=True,
                        chromadb_doc_id=chroma_id,
                    )
                    db.add(yt_track)
                    await db.commit()

                    processed_count += 1

                    # Step 6: Clean up audio file if configured
                    if not settings.youtube_audio_keep and audio_path:
                        _cleanup_audio(audio_path)

                except Exception as e:
                    error_count += 1
                    logger.error(f"Failed to process video {video_id}: {e}")
                    continue

        _last_run_status = {
            "status": "completed",
            "timestamp": datetime.utcnow().isoformat(),
            "detail": f"Processed {processed_count} videos, {error_count} errors",
        }
        logger.info(f"Pipeline complete: {processed_count} processed, {error_count} errors")

    except Exception as e:
        _last_run_status = {
            "status": "error",
            "timestamp": datetime.utcnow().isoformat(),
            "detail": str(e),
        }
        logger.error(f"Collection pipeline failed: {e}")


async def run_manual_collection(max_videos: int = 5):
    """Trigger a manual collection run (from API endpoint)."""
    original = settings.youtube_max_videos_per_run
    try:
        object.__setattr__(settings, "youtube_max_videos_per_run", max_videos)
        await run_collection_pipeline()
    finally:
        object.__setattr__(settings, "youtube_max_videos_per_run", original)


def _cleanup_audio(audio_path: str):
    """Remove temporary audio file after processing."""
    try:
        p = Path(audio_path)
        if p.exists():
            p.unlink()
    except Exception as e:
        logger.debug(f"Failed to clean up {audio_path}: {e}")
