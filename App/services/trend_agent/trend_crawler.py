import httpx
from typing import List, Dict
from ..trend_agent import trend_cache
from ...internal.config import get_settings

settings = get_settings()

DEEZER_BASE = "https://api.deezer.com"
LASTFM_BASE = "https://ws.audioscrobbler.com/2.0/"

GENRE_IDS = {
    "pop": 132,
    "rock": 152,
    "hiphop": 116,
    "electronic": 106,
    "jazz": 129,
    "classical": 98,
}


async def get_trending_tracks(genre: str = "pop") -> List[Dict]:
    """Deezer → Last.fm 순서로 트렌딩 트랙 수집. 캐시 우선."""
    cache_key = f"trending:{genre}"
    cached = trend_cache.get(cache_key)
    if cached:
        return cached["tracks"]

    tracks = await _deezer_trending(genre)
    if not tracks:
        tracks = await _lastfm_trending(genre)

    result = {"tracks": tracks}
    trend_cache.set(cache_key, result, settings.trend_cache_ttl)
    return tracks


async def _deezer_trending(genre: str) -> List[Dict]:
    genre_id = GENRE_IDS.get(genre.lower(), 0)
    url = f"{DEEZER_BASE}/chart/{genre_id}/tracks"
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(url, params={"limit": 50})
            resp.raise_for_status()
            data = resp.json()
            return [
                {
                    "title": t.get("title", ""),
                    "artist": t.get("artist", {}).get("name", ""),
                    "bpm": t.get("bpm"),
                    "genre": genre,
                    "source": "deezer",
                }
                for t in data.get("data", [])
            ]
    except Exception:
        return []


async def _lastfm_trending(genre: str) -> List[Dict]:
    if not settings.lastfm_api_key:
        return []
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                LASTFM_BASE,
                params={
                    "method": "tag.getTopTracks",
                    "tag": genre,
                    "api_key": settings.lastfm_api_key,
                    "format": "json",
                    "limit": 50,
                },
            )
            resp.raise_for_status()
            data = resp.json()
            tracks_data = data.get("tracks", {}).get("track", [])
            return [
                {
                    "title": t.get("name", ""),
                    "artist": t.get("artist", {}).get("name", ""),
                    "bpm": None,
                    "genre": genre,
                    "source": "lastfm",
                }
                for t in tracks_data
            ]
    except Exception:
        return []
