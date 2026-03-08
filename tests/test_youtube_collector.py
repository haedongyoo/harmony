"""Tests for App.services.youtube_learning.youtube_collector"""
import pytest
from unittest.mock import patch, MagicMock
from App.services.youtube_learning.youtube_collector import _infer_genre, _sync_extract


class TestInferGenre:
    def test_pop(self):
        assert _infer_genre({"categories": ["Music"], "tags": ["pop", "2024"]}) == "pop"

    def test_kpop(self):
        assert _infer_genre({"categories": [], "tags": ["k-pop", "idol"]}) == "pop"

    def test_hiphop(self):
        assert _infer_genre({"categories": [], "tags": ["hip hop", "rap", "freestyle"]}) == "hiphop"

    def test_trap(self):
        assert _infer_genre({"categories": [], "tags": ["trap", "beat"]}) == "hiphop"

    def test_electronic(self):
        assert _infer_genre({"categories": [], "tags": ["edm", "festival"]}) == "electronic"

    def test_rock(self):
        assert _infer_genre({"categories": [], "tags": ["rock", "guitar"]}) == "rock"

    def test_rnb(self):
        assert _infer_genre({"categories": [], "tags": ["r&b", "smooth"]}) == "rnb"

    def test_jazz(self):
        assert _infer_genre({"categories": [], "tags": ["jazz", "improvisation"]}) == "jazz"

    def test_classical(self):
        assert _infer_genre({"categories": [], "tags": ["classical", "symphony"]}) == "classical"

    def test_latin(self):
        assert _infer_genre({"categories": [], "tags": ["reggaeton", "latin"]}) == "latin"

    def test_default_pop(self):
        assert _infer_genre({"categories": [], "tags": ["ambient", "noise"]}) == "pop"

    def test_empty_tags(self):
        assert _infer_genre({"categories": [], "tags": []}) == "pop"

    def test_none_tags(self):
        assert _infer_genre({"categories": [], "tags": None}) == "pop"

    def test_case_insensitive(self):
        assert _infer_genre({"categories": ["MUSIC"], "tags": ["HIP HOP"]}) == "hiphop"

    def test_categories_also_checked(self):
        assert _infer_genre({"categories": ["EDM Music"], "tags": []}) == "electronic"


class TestSyncExtract:
    def test_returns_empty_on_failure(self, tmp_dir):
        """When yt-dlp fails, should return empty list."""
        mock_ydl = MagicMock()
        mock_ydl.__enter__ = MagicMock(return_value=mock_ydl)
        mock_ydl.__exit__ = MagicMock(return_value=False)
        mock_ydl.extract_info.side_effect = Exception("Network error")

        with patch("yt_dlp.YoutubeDL", return_value=mock_ydl):
            results = _sync_extract("ytsearch5:test", str(tmp_dir), 5)
            assert results == []

    def test_returns_empty_on_none_info(self, tmp_dir):
        mock_ydl = MagicMock()
        mock_ydl.__enter__ = MagicMock(return_value=mock_ydl)
        mock_ydl.__exit__ = MagicMock(return_value=False)
        mock_ydl.extract_info.return_value = None

        with patch("yt_dlp.YoutubeDL", return_value=mock_ydl):
            results = _sync_extract("ytsearch5:test", str(tmp_dir), 5)
            assert results == []

    def test_skips_none_entries(self, tmp_dir):
        mock_ydl = MagicMock()
        mock_ydl.__enter__ = MagicMock(return_value=mock_ydl)
        mock_ydl.__exit__ = MagicMock(return_value=False)
        mock_ydl.extract_info.return_value = {"entries": [None, None]}

        with patch("yt_dlp.YoutubeDL", return_value=mock_ydl):
            results = _sync_extract("playlist_url", str(tmp_dir), 5)
            assert results == []

    def test_extracts_metadata_correctly(self, tmp_dir):
        audio_path = tmp_dir / "testid123.wav"
        audio_path.write_bytes(b"fake wav data")

        entry = {
            "id": "testid123",
            "title": "Test Title",
            "artist": "Test Artist",
            "creator": None,
            "uploader": "Test Channel",
            "channel": "Test Channel",
            "description": "A test description",
            "tags": ["pop", "test"],
            "categories": ["Music"],
            "view_count": 1000000,
            "duration": 180,
            "upload_date": "20240101",
        }

        mock_ydl = MagicMock()
        mock_ydl.__enter__ = MagicMock(return_value=mock_ydl)
        mock_ydl.__exit__ = MagicMock(return_value=False)
        mock_ydl.extract_info.return_value = {"entries": [entry]}

        with patch("yt_dlp.YoutubeDL", return_value=mock_ydl):
            results = _sync_extract("ytsearch1:test", str(tmp_dir), 5)

            assert len(results) == 1
            r = results[0]
            assert r["video_id"] == "testid123"
            assert r["title"] == "Test Title"
            assert r["artist"] == "Test Artist"
            assert r["channel"] == "Test Channel"
            assert r["view_count"] == 1000000
            assert r["duration_seconds"] == 180
            assert r["genre"] == "pop"
            assert str(audio_path) in r["audio_path"]

    def test_description_truncated(self, tmp_dir):
        audio_path = tmp_dir / "longdesc.wav"
        audio_path.write_bytes(b"fake")

        entry = {
            "id": "longdesc",
            "title": "Long",
            "artist": None,
            "creator": None,
            "uploader": "X",
            "channel": "X",
            "description": "A" * 5000,
            "tags": [],
            "categories": [],
            "view_count": 100,
            "duration": 60,
            "upload_date": "20240101",
        }

        mock_ydl = MagicMock()
        mock_ydl.__enter__ = MagicMock(return_value=mock_ydl)
        mock_ydl.__exit__ = MagicMock(return_value=False)
        mock_ydl.extract_info.return_value = {"entries": [entry]}

        with patch("yt_dlp.YoutubeDL", return_value=mock_ydl):
            results = _sync_extract("url", str(tmp_dir), 1)
            assert len(results[0]["description"]) == 2000

    def test_respects_max_items(self, tmp_dir):
        entries = []
        for i in range(10):
            vid = f"vid{i}"
            (tmp_dir / f"{vid}.wav").write_bytes(b"fake")
            entries.append({
                "id": vid, "title": f"Song {i}", "artist": None, "creator": None,
                "uploader": "X", "channel": "X", "description": "",
                "tags": [], "categories": [], "view_count": 0, "duration": 60,
                "upload_date": "20240101",
            })

        mock_ydl = MagicMock()
        mock_ydl.__enter__ = MagicMock(return_value=mock_ydl)
        mock_ydl.__exit__ = MagicMock(return_value=False)
        mock_ydl.extract_info.return_value = {"entries": entries}

        with patch("yt_dlp.YoutubeDL", return_value=mock_ydl):
            results = _sync_extract("url", str(tmp_dir), 3)
            assert len(results) == 3
