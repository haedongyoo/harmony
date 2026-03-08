import logging
from typing import Dict

logger = logging.getLogger(__name__)


def build_document(video_data: Dict, audio_features: Dict, mood: str) -> str:
    """
    Build a rich text document from video metadata + audio features.
    This document will be embedded and stored in ChromaDB.
    """
    title = video_data.get("title", "Unknown")
    artist = video_data.get("artist", "Unknown")
    genre = video_data.get("genre", "unknown")
    tags = video_data.get("tags", [])
    view_count = video_data.get("view_count")

    bpm = audio_features.get("bpm")
    key = audio_features.get("key")
    energy = audio_features.get("energy")
    danceability = audio_features.get("danceability")
    spectral_centroid = audio_features.get("spectral_centroid")

    parts = []
    parts.append(f'Song: "{title}" by {artist}')
    parts.append(f"Genre: {genre}")

    if bpm:
        parts.append(f"Tempo: {bpm} BPM")
    if key:
        parts.append(f"Key: {key}")
    if mood and mood != "unknown":
        parts.append(f"Mood: {mood}")
    if energy is not None:
        parts.append(f"Energy level: {_energy_to_text(energy)} ({energy:.3f})")
    if danceability is not None:
        parts.append(f"Danceability: {_danceability_to_text(danceability)} ({danceability:.3f})")
    if spectral_centroid is not None:
        brightness = "bright" if spectral_centroid > 3000 else "warm" if spectral_centroid > 1500 else "dark"
        parts.append(f"Tonal character: {brightness} (spectral centroid: {spectral_centroid:.0f} Hz)")
    if view_count and view_count > 0:
        parts.append(f"Popularity: {_popularity_tier(view_count)} ({view_count:,} views)")
    if tags:
        parts.append(f"Tags: {', '.join(tags[:10])}")

    return "\n".join(parts)


def build_metadata(video_data: Dict, audio_features: Dict, mood: str) -> Dict:
    """Build ChromaDB metadata dict for filtering."""
    return {
        "video_id": video_data.get("video_id", ""),
        "title": video_data.get("title", "")[:200],
        "artist": video_data.get("artist", "")[:100],
        "genre": video_data.get("genre", "unknown"),
        "bpm": audio_features.get("bpm") or 0.0,
        "key": audio_features.get("key") or "",
        "energy": audio_features.get("energy") or 0.0,
        "danceability": audio_features.get("danceability") or 0.0,
        "mood": mood or "unknown",
        "view_count": video_data.get("view_count") or 0,
    }


def _energy_to_text(energy: float) -> str:
    if energy > 0.15:
        return "very high"
    elif energy > 0.08:
        return "high"
    elif energy > 0.03:
        return "moderate"
    elif energy > 0.01:
        return "low"
    return "very low"


def _danceability_to_text(danceability: float) -> str:
    if danceability > 0.7:
        return "very danceable"
    elif danceability > 0.5:
        return "danceable"
    elif danceability > 0.3:
        return "moderate"
    return "low danceability"


def _popularity_tier(view_count: int) -> str:
    if view_count > 100_000_000:
        return "mega-hit"
    elif view_count > 10_000_000:
        return "very popular"
    elif view_count > 1_000_000:
        return "popular"
    elif view_count > 100_000:
        return "well-known"
    return "emerging"
