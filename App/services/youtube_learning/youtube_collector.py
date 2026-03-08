import logging
import asyncio
from pathlib import Path
from typing import List, Dict, Optional
from ...internal.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

# YouTube Music discovery sources (used by yt-dlp)
DISCOVERY_SOURCES = [
    "https://www.youtube.com/playlist?list=PLrAXtmErZgOeiKm4sgNOknGvNjby9efdf",
    "https://www.youtube.com/playlist?list=PLDcnymzs18LU4Kexrs91TVdfnplU3I5zs",
    "ytsearch20:trending music 2026",
    "ytsearch20:new music releases this week",
    "ytsearch10:popular pop music 2026",
    "ytsearch10:trending hip hop beats",
    "ytsearch10:popular electronic music",
]

# YouTube API v3 search queries (used when yt-dlp fails and API key is set)
API_V3_SEARCH_QUERIES = [
    "trending music 2026",
    "new music releases this week",
    "popular pop music 2026",
    "trending hip hop beats",
    "popular electronic music",
]

API_V3_PLAYLIST_IDS = [
    "PLrAXtmErZgOeiKm4sgNOknGvNjby9efdf",
    "PLDcnymzs18LU4Kexrs91TVdfnplU3I5zs",
]


async def collect_videos(max_videos: int = None) -> List[Dict]:
    """
    Discover and download audio+metadata from YouTube trending music.
    Tries yt-dlp first, falls back to YouTube Data API v3 if available.
    Returns list of dicts: { video_id, title, artist, metadata..., audio_path }
    """
    max_videos = max_videos or settings.youtube_max_videos_per_run
    temp_dir = Path(settings.youtube_temp_path)
    temp_dir.mkdir(parents=True, exist_ok=True)

    # Try yt-dlp first
    collected = await _collect_via_ytdlp(max_videos, temp_dir)

    # Fall back to YouTube API v3 if yt-dlp returned nothing and API key is set
    if not collected and settings.youtube_api_key:
        logger.info("yt-dlp returned no results, falling back to YouTube API v3")
        collected = await _collect_via_api_v3(max_videos, temp_dir)

    logger.info(f"Collected {len(collected)} videos total")
    return collected[:max_videos]


async def _collect_via_ytdlp(max_videos: int, temp_dir: Path) -> List[Dict]:
    """Collect videos using yt-dlp (original method)."""
    collected = []
    for source_url in DISCOVERY_SOURCES:
        if len(collected) >= max_videos:
            break
        try:
            remaining = max_videos - len(collected)
            results = await _extract_from_source(source_url, temp_dir, remaining)
            collected.extend(results)
        except Exception as e:
            logger.warning(f"yt-dlp failed for {source_url}: {e}")
            continue
    return collected


async def _collect_via_api_v3(max_videos: int, temp_dir: Path) -> List[Dict]:
    """Collect videos using YouTube Data API v3 for discovery, yt-dlp for audio."""
    collected = []
    seen_ids = set()

    # Search queries
    for query in API_V3_SEARCH_QUERIES:
        if len(collected) >= max_videos:
            break
        remaining = max_videos - len(collected)
        try:
            video_metas = await _api_v3_search(query, remaining)
            for meta in video_metas:
                if meta["video_id"] in seen_ids:
                    continue
                seen_ids.add(meta["video_id"])
                enriched = await _download_audio_for_video(meta, temp_dir)
                collected.append(enriched)
                if len(collected) >= max_videos:
                    break
        except Exception as e:
            logger.warning(f"API v3 search failed for '{query}': {e}")
            continue

    # Playlist items
    for playlist_id in API_V3_PLAYLIST_IDS:
        if len(collected) >= max_videos:
            break
        remaining = max_videos - len(collected)
        try:
            video_metas = await _api_v3_playlist_items(playlist_id, remaining)
            for meta in video_metas:
                if meta["video_id"] in seen_ids:
                    continue
                seen_ids.add(meta["video_id"])
                enriched = await _download_audio_for_video(meta, temp_dir)
                collected.append(enriched)
                if len(collected) >= max_videos:
                    break
        except Exception as e:
            logger.warning(f"API v3 playlist failed for {playlist_id}: {e}")
            continue

    return collected


async def _api_v3_search(query: str, max_results: int) -> List[Dict]:
    """Search YouTube via Data API v3. Returns metadata dicts (no audio)."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None, _sync_api_v3_search, query, max_results
    )


def _sync_api_v3_search(query: str, max_results: int) -> List[Dict]:
    """Synchronous YouTube API v3 search."""
    from googleapiclient.discovery import build

    youtube = build("youtube", "v3", developerKey=settings.youtube_api_key)

    response = youtube.search().list(
        q=query,
        part="snippet",
        type="video",
        videoCategoryId="10",  # Music category
        maxResults=min(max_results, 50),
        order="relevance",
    ).execute()

    results = []
    for item in response.get("items", []):
        snippet = item["snippet"]
        results.append({
            "video_id": item["id"]["videoId"],
            "title": snippet.get("title", ""),
            "artist": snippet.get("channelTitle", ""),
            "channel": snippet.get("channelTitle", ""),
            "description": (snippet.get("description") or "")[:2000],
            "tags": [],
            "genre": "pop",
            "view_count": None,
            "duration_seconds": None,
            "upload_date": snippet.get("publishedAt", "")[:10].replace("-", ""),
            "audio_path": None,
        })

    # Enrich with video details (tags, view count, duration)
    if results:
        video_ids = [r["video_id"] for r in results]
        details = _sync_api_v3_video_details(youtube, video_ids)
        for r in results:
            if r["video_id"] in details:
                r.update(details[r["video_id"]])

    return results


def _sync_api_v3_video_details(youtube, video_ids: List[str]) -> Dict[str, Dict]:
    """Fetch detailed video info (tags, stats, duration) via API v3."""
    details = {}
    # API allows up to 50 IDs per request
    for i in range(0, len(video_ids), 50):
        batch = video_ids[i:i + 50]
        response = youtube.videos().list(
            id=",".join(batch),
            part="snippet,contentDetails,statistics",
        ).execute()

        for item in response.get("items", []):
            vid = item["id"]
            snippet = item.get("snippet", {})
            stats = item.get("statistics", {})
            content = item.get("contentDetails", {})

            details[vid] = {
                "tags": snippet.get("tags", []),
                "genre": _infer_genre({
                    "categories": [snippet.get("categoryId", "")],
                    "tags": snippet.get("tags", []),
                }),
                "view_count": int(stats.get("viewCount", 0)) if stats.get("viewCount") else None,
                "duration_seconds": _parse_iso8601_duration(content.get("duration", "")),
            }

    return details


async def _api_v3_playlist_items(playlist_id: str, max_results: int) -> List[Dict]:
    """Get playlist items via YouTube Data API v3."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None, _sync_api_v3_playlist_items, playlist_id, max_results
    )


def _sync_api_v3_playlist_items(playlist_id: str, max_results: int) -> List[Dict]:
    """Synchronous YouTube API v3 playlist items fetch."""
    from googleapiclient.discovery import build

    youtube = build("youtube", "v3", developerKey=settings.youtube_api_key)

    results = []
    page_token = None

    while len(results) < max_results:
        response = youtube.playlistItems().list(
            playlistId=playlist_id,
            part="snippet",
            maxResults=min(max_results - len(results), 50),
            pageToken=page_token,
        ).execute()

        for item in response.get("items", []):
            snippet = item["snippet"]
            video_id = snippet.get("resourceId", {}).get("videoId")
            if not video_id:
                continue
            results.append({
                "video_id": video_id,
                "title": snippet.get("title", ""),
                "artist": snippet.get("channelTitle", "") or snippet.get("videoOwnerChannelTitle", ""),
                "channel": snippet.get("videoOwnerChannelTitle", "") or snippet.get("channelTitle", ""),
                "description": (snippet.get("description") or "")[:2000],
                "tags": [],
                "genre": "pop",
                "view_count": None,
                "duration_seconds": None,
                "upload_date": snippet.get("publishedAt", "")[:10].replace("-", ""),
                "audio_path": None,
            })

        page_token = response.get("nextPageToken")
        if not page_token:
            break

    # Enrich with video details
    if results:
        video_ids = [r["video_id"] for r in results[:max_results]]
        details = _sync_api_v3_video_details(youtube, video_ids)
        for r in results:
            if r["video_id"] in details:
                r.update(details[r["video_id"]])

    return results[:max_results]


async def _download_audio_for_video(meta: Dict, temp_dir: Path) -> Dict:
    """Try to download audio for a single video using yt-dlp. Returns meta with audio_path."""
    video_id = meta["video_id"]
    url = f"https://www.youtube.com/watch?v={video_id}"

    try:
        loop = asyncio.get_event_loop()
        downloaded = await loop.run_in_executor(
            None, _sync_download_single, url, str(temp_dir)
        )
        if downloaded:
            meta["audio_path"] = downloaded
    except Exception as e:
        logger.debug(f"Audio download failed for {video_id}: {e}")

    return meta


def _sync_download_single(url: str, temp_dir: str) -> Optional[str]:
    """Download audio for a single video. Returns audio file path or None."""
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
        "socket_timeout": 30,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(url, download=True)
        except Exception:
            return None

        if info is None:
            return None

        video_id = info.get("id", "")
        for ext in ["wav", "m4a", "webm", "mp3"]:
            candidate = Path(temp_dir) / f"{video_id}.{ext}"
            if candidate.exists():
                return str(candidate)

    return None


def _parse_iso8601_duration(duration: str) -> Optional[int]:
    """Parse ISO 8601 duration (PT1H2M3S) to seconds."""
    if not duration or not duration.startswith("PT"):
        return None
    import re
    match = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", duration)
    if not match:
        return None
    hours = int(match.group(1) or 0)
    minutes = int(match.group(2) or 0)
    seconds = int(match.group(3) or 0)
    return hours * 3600 + minutes * 60 + seconds


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

    combined = " ".join(str(c) for c in categories + tags).lower()
    for genre, keywords in genre_keywords.items():
        if any(kw in combined for kw in keywords):
            return genre
    return "pop"
