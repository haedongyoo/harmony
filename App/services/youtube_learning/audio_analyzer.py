import logging
import asyncio
from typing import Dict

logger = logging.getLogger(__name__)

_KEY_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]


async def analyze_audio(audio_path: str) -> Dict:
    """
    Extract audio features from an audio file using librosa.
    Returns dict with: bpm, key, energy, danceability, spectral_centroid.
    Runs in thread pool (CPU-intensive).
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _sync_analyze, audio_path)


def _sync_analyze(audio_path: str) -> Dict:
    """Synchronous librosa analysis."""
    import librosa
    import numpy as np

    features = {
        "bpm": None,
        "key": None,
        "energy": None,
        "danceability": None,
        "spectral_centroid": None,
    }

    try:
        # Load first 60 seconds only for efficiency
        y, sr = librosa.load(audio_path, sr=22050, duration=60, mono=True)

        if len(y) == 0:
            logger.warning(f"Empty audio file: {audio_path}")
            return features

        # BPM
        tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
        if hasattr(tempo, "__len__"):
            tempo = tempo[0]
        features["bpm"] = round(float(tempo), 1)

        # Key detection (chroma-based + Krumhansl-Schmuckler)
        chroma = librosa.feature.chroma_cqt(y=y, sr=sr)
        chroma_mean = chroma.mean(axis=1)
        key_idx = int(np.argmax(chroma_mean))

        major_profile = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88])
        minor_profile = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17])

        major_corr = np.corrcoef(chroma_mean, np.roll(major_profile, key_idx))[0, 1]
        minor_corr = np.corrcoef(chroma_mean, np.roll(minor_profile, key_idx))[0, 1]

        mode = "major" if major_corr >= minor_corr else "minor"
        features["key"] = f"{_KEY_NAMES[key_idx]} {mode}"

        # Energy (RMS)
        rms = librosa.feature.rms(y=y)
        features["energy"] = round(float(np.mean(rms)), 4)

        # Spectral centroid
        spectral_centroids = librosa.feature.spectral_centroid(y=y, sr=sr)
        features["spectral_centroid"] = round(float(np.mean(spectral_centroids)), 2)

        # Danceability (composite: beat strength + tempo score)
        onset_env = librosa.onset.onset_strength(y=y, sr=sr)
        pulse = librosa.beat.plp(onset_envelope=onset_env, sr=sr)
        beat_strength = float(np.mean(pulse))

        tempo_score = max(0, min(1, (features["bpm"] - 60) / 120)) if features["bpm"] else 0.5
        features["danceability"] = round((beat_strength + tempo_score) / 2, 3)

    except Exception as e:
        logger.error(f"Audio analysis failed for {audio_path}: {e}")

    return features


async def derive_mood_from_features(features: Dict, title: str, genre: str) -> str:
    """
    Use Ollama to derive mood descriptor from audio features.
    Reuses ollama_client.complete() (same pattern as trend_analyzer.py).
    """
    from ..ollama_client import complete

    prompt = (
        f'Based on these audio features of a {genre} song titled "{title}":\n'
        f"- BPM: {features.get('bpm', 'unknown')}\n"
        f"- Key: {features.get('key', 'unknown')}\n"
        f"- Energy: {features.get('energy', 'unknown')}\n"
        f"- Danceability: {features.get('danceability', 'unknown')}\n\n"
        'Respond with a single mood/atmosphere keyword (e.g., "energetic", "melancholic", '
        '"dreamy", "aggressive", "chill"). One word only.'
    )

    try:
        result = await complete(prompt)
        mood = result.strip().split()[0].strip('."\'').lower()
        return mood if len(mood) < 32 else "unknown"
    except Exception:
        return "unknown"
