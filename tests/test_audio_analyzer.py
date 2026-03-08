"""Tests for App.services.youtube_learning.audio_analyzer"""
import struct
import wave
import pytest
from unittest.mock import patch, AsyncMock


def _create_test_wav(path, duration_sec=2, sample_rate=22050, frequency=440.0):
    """Create a simple sine wave WAV file for testing."""
    import math

    n_samples = int(sample_rate * duration_sec)
    with wave.open(str(path), "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        for i in range(n_samples):
            sample = int(32767 * 0.5 * math.sin(2 * math.pi * frequency * i / sample_rate))
            wf.writeframes(struct.pack("<h", sample))


class TestAnalyzeAudio:
    @pytest.mark.asyncio
    async def test_analyze_valid_wav(self, tmp_dir):
        # Use longer duration for reliable beat detection
        wav_path = tmp_dir / "test_tone.wav"
        _create_test_wav(wav_path, duration_sec=10, frequency=440.0)

        from App.services.youtube_learning.audio_analyzer import analyze_audio

        features = await analyze_audio(str(wav_path))

        # BPM may be 0 for pure sine waves (no rhythmic content), so just check it's a number
        assert features["bpm"] is not None
        assert isinstance(features["bpm"], float)

        assert features["key"] is not None
        parts = features["key"].split()
        assert len(parts) == 2
        assert parts[0] in ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
        assert parts[1] in ["major", "minor"]

        assert features["energy"] is not None
        assert features["energy"] >= 0.0

        assert features["spectral_centroid"] is not None
        assert features["spectral_centroid"] > 0

        assert features["danceability"] is not None
        assert isinstance(features["danceability"], float)

    @pytest.mark.asyncio
    async def test_analyze_nonexistent_file(self):
        from App.services.youtube_learning.audio_analyzer import analyze_audio

        features = await analyze_audio("/nonexistent/path/audio.wav")

        assert features["bpm"] is None
        assert features["key"] is None
        assert features["energy"] is None

    @pytest.mark.asyncio
    async def test_analyze_empty_wav(self, tmp_dir):
        """An empty WAV (0 samples) should return None features."""
        wav_path = tmp_dir / "empty.wav"
        with wave.open(str(wav_path), "w") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(22050)

        from App.services.youtube_learning.audio_analyzer import analyze_audio

        features = await analyze_audio(str(wav_path))
        assert features["bpm"] is None

    @pytest.mark.asyncio
    async def test_analyze_short_wav(self, tmp_dir):
        """Very short audio (0.5s) should still work or fail gracefully."""
        wav_path = tmp_dir / "short.wav"
        _create_test_wav(wav_path, duration_sec=0.5)

        from App.services.youtube_learning.audio_analyzer import analyze_audio

        features = await analyze_audio(str(wav_path))
        assert isinstance(features, dict)
        assert "bpm" in features


class TestDeriveMood:
    @pytest.mark.asyncio
    async def test_derive_mood_success(self):
        from App.services.youtube_learning.audio_analyzer import derive_mood_from_features

        features = {"bpm": 128.0, "key": "C major", "energy": 0.12, "danceability": 0.8}

        with patch("App.services.ollama_client.complete", new_callable=AsyncMock) as mock_complete:
            mock_complete.return_value = "energetic"
            mood = await derive_mood_from_features(features, "Test Song", "pop")
            assert mood == "energetic"
            mock_complete.assert_called_once()

    @pytest.mark.asyncio
    async def test_derive_mood_ollama_failure(self):
        from App.services.youtube_learning.audio_analyzer import derive_mood_from_features

        features = {"bpm": 128.0, "key": "C major", "energy": 0.12, "danceability": 0.8}

        with patch("App.services.ollama_client.complete", new_callable=AsyncMock) as mock_complete:
            mock_complete.side_effect = Exception("Ollama unavailable")
            mood = await derive_mood_from_features(features, "Test Song", "pop")
            assert mood == "unknown"

    @pytest.mark.asyncio
    async def test_derive_mood_cleans_response(self):
        from App.services.youtube_learning.audio_analyzer import derive_mood_from_features

        features = {"bpm": 90.0, "key": "D minor", "energy": 0.03, "danceability": 0.3}

        with patch("App.services.ollama_client.complete", new_callable=AsyncMock) as mock_complete:
            mock_complete.return_value = '"Melancholic." is the mood.'
            mood = await derive_mood_from_features(features, "Sad Song", "rnb")
            assert mood == "melancholic"
