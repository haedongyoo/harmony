import logging
import asyncio
from pathlib import Path
from typing import List, Dict
from ...internal.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

# YouTube Music discovery sources
DISCOVERY_SOURCES = [
    "https://www.youtube.com/playlist?list=PLrAXtmErZgOeiKm4sgNOknGvNjby9efdf",
    "https://www.youtube.com/playlist?list=PLDcnymzs18LU4Kexrs91TVdfnplU3I5zs",
    "ytsearch20:trending music 2026",
    "ytsearch20:new music releases this week",
    "ytsearch10:popular pop music 2026",
    "ytsearch10:trending hip hop beats",
    "ytsearch10:popular electronic music",
]


async def collect_videos(max_videos: int = None) -> List[Dict]:
    """
    Discover and download audio+metadata from YouTube trending music.
    Returns list of dicts: { video_id, title, artist, metadata..., audio_path }
    """
    max_videos = max_videos or settings.youtube_max_videos_per_run
    temp_dir = Path(settings.youtube_temp_path)
    temp_dir.mkdir(parents=True, exist_ok=True)

    collected = []

    for source_url in DISCOVERY_SOURCES:
        if len(collected) >= max_videos:
            break
        try:
            remaining = max_videos - len(collected)
            results = await _extract_from_source(source_url, temp_dir, remaining)
            collected.extend(results)
        except Exception as e:
            logger.warning(f"Failed to collect from {source_url}: {e}")
            continue

    logger.info(f"Collected {len(collected)} videos total")
    return collected[:max_videos]


async def _extract_from_source(
    url: str, temp_dir: Path, max_items: int
) -> List[Dict]:
    """Run yt-dlp extraction in thread pool."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None, _sync_extract, url, str(temp_dir), max_items
    )


def _sync_extract(url: str, temp_dir: str, max_items: int) -> List[Dict]:
    """Synchronous yt-dlp extraction (runs in thread pool)."""
    import yt_dlp

    ydl_opts = {
        "format": "bestaudio/best",
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "wav",
            "preferredquality": "192",
        }],
        "outtmpl": f"{temp_dir}/%(id)s.%(ext)s",
        "quiet": True,
        "no_warnings": True,
        "extract_flat": False,
        "playlistend": max_items,
        "ignoreerrors": True,
        "noplaylist": False,
        "max_downloads": max_items,
        "socket_timeout": 30,
    }

    results = []

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(url, download=True)
        except Exception as e:
            logger.warning(f"yt-dlp extraction failed for {url}: {e}")
            return []

        if info is None:
            return []

        entries = info.get("entries", [info])

        for entry in entries:
            if entry is None:
                continue
            if len(results) >= max_items:
                break

            video_id = entry.get("id", "")
            audio_path = Path(temp_dir) / f"{video_id}.wav"

            if not audio_path.exists():
                for ext in ["wav", "m4a", "webm", "mp3"]:
                    candidate = Path(temp_dir) / f"{video_id}.{ext}"
                    if candidate.exists():
                        audio_path = candidate
                        break
                else:
                    logger.debug(f"No audio file found for {video_id}")
                    continue

            results.append({
                "video_id": video_id,
                "title": entry.get("title", ""),
                "artist": entry.get("artist") or entry.get("creator") or entry.get("uploader", ""),
                "channel": entry.get("channel", "") or entry.get("uploader", ""),
                "description": (entry.get("description") or "")[:2000],
                "tags": entry.get("tags", []),
                "genre": _infer_genre(entry),
                "view_count": entry.get("view_count"),
                "duration_seconds": entry.get("duration"),
                "upload_date": entry.get("upload_date"),
                "audio_path": str(audio_path),
            })

    return results


def _infer_genre(entry: dict) -> str:
    """Best-effort genre inference from yt-dlp metadata."""
    categories = entry.get("categories", [])
    tags = entry.get("tags", []) or []

    genre_keywords = {
        "pop": ["pop", "k-pop", "kpop"],
        "hiphop": ["hip hop", "hip-hop", "rap", "trap"],
        "electronic": ["edm", "electronic", "house", "techno", "dubstep"],
        "rock": ["rock", "metal", "punk", "alternative"],
        "rnb": ["r&b", "rnb", "soul"],
        "jazz": ["jazz"],
        "classical": ["classical", "orchestra"],
        "latin": ["latin", "reggaeton"],
    }

    combined = " ".join(categories + tags).lower()
    for genre, keywords in genre_keywords.items():
        if any(kw in combined for kw in keywords):
            return genre
    return "pop"
