"""Tests for App.services.youtube_learning.youtube_collector"""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from App.services.youtube_learning.youtube_collector import (
    _infer_genre, _sync_extract, _parse_iso8601_duration,
    _sync_api_v3_search, _sync_api_v3_playlist_items,
    collect_videos,
)


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


class TestParseISO8601Duration:
    def test_full_duration(self):
        assert _parse_iso8601_duration("PT1H2M3S") == 3723

    def test_minutes_seconds(self):
        assert _parse_iso8601_duration("PT3M30S") == 210

    def test_seconds_only(self):
        assert _parse_iso8601_duration("PT45S") == 45

    def test_hours_only(self):
        assert _parse_iso8601_duration("PT2H") == 7200

    def test_empty(self):
        assert _parse_iso8601_duration("") is None

    def test_none(self):
        assert _parse_iso8601_duration(None) is None

    def test_invalid(self):
        assert _parse_iso8601_duration("invalid") is None


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


class TestAPIv3Search:
    def test_search_returns_video_metadata(self):
        mock_youtube = MagicMock()
        mock_search = MagicMock()
        mock_search.list.return_value.execute.return_value = {
            "items": [{
                "id": {"videoId": "abc123"},
                "snippet": {
                    "title": "Trending Song",
                    "channelTitle": "Artist Channel",
                    "description": "A great song",
                    "publishedAt": "2026-01-15T00:00:00Z",
                },
            }],
        }
        mock_youtube.search.return_value = mock_search

        mock_videos = MagicMock()
        mock_videos.list.return_value.execute.return_value = {
            "items": [{
                "id": "abc123",
                "snippet": {"tags": ["pop", "trending"], "categoryId": "10"},
                "statistics": {"viewCount": "5000000"},
                "contentDetails": {"duration": "PT3M45S"},
            }],
        }
        mock_youtube.videos.return_value = mock_videos

        with patch(
            "App.services.youtube_learning.youtube_collector.settings"
        ) as mock_settings:
            mock_settings.youtube_api_key = "test-key"
            with patch("googleapiclient.discovery.build", return_value=mock_youtube):
                results = _sync_api_v3_search("trending music", 5)

        assert len(results) == 1
        assert results[0]["video_id"] == "abc123"
        assert results[0]["title"] == "Trending Song"
        assert results[0]["view_count"] == 5000000
        assert results[0]["duration_seconds"] == 225

    def test_search_handles_empty_response(self):
        mock_youtube = MagicMock()
        mock_search = MagicMock()
        mock_search.list.return_value.execute.return_value = {"items": []}
        mock_youtube.search.return_value = mock_search

        with patch(
            "App.services.youtube_learning.youtube_collector.settings"
        ) as mock_settings:
            mock_settings.youtube_api_key = "test-key"
            with patch("googleapiclient.discovery.build", return_value=mock_youtube):
                results = _sync_api_v3_search("nonexistent", 5)

        assert results == []


class TestAPIv3PlaylistItems:
    def test_playlist_returns_items(self):
        mock_youtube = MagicMock()
        mock_playlist = MagicMock()
        mock_playlist.list.return_value.execute.return_value = {
            "items": [{
                "snippet": {
                    "resourceId": {"videoId": "xyz789"},
                    "title": "Playlist Song",
                    "channelTitle": "Playlist Owner",
                    "videoOwnerChannelTitle": "Song Artist",
                    "description": "From a playlist",
                    "publishedAt": "2026-02-01T00:00:00Z",
                },
            }],
        }
        mock_youtube.playlistItems.return_value = mock_playlist

        mock_videos = MagicMock()
        mock_videos.list.return_value.execute.return_value = {
            "items": [{
                "id": "xyz789",
                "snippet": {"tags": ["rock"], "categoryId": "10"},
                "statistics": {"viewCount": "1000000"},
                "contentDetails": {"duration": "PT4M20S"},
            }],
        }
        mock_youtube.videos.return_value = mock_videos

        with patch(
            "App.services.youtube_learning.youtube_collector.settings"
        ) as mock_settings:
            mock_settings.youtube_api_key = "test-key"
            with patch("googleapiclient.discovery.build", return_value=mock_youtube):
                results = _sync_api_v3_playlist_items("PLtest123", 10)

        assert len(results) == 1
        assert results[0]["video_id"] == "xyz789"
        assert results[0]["channel"] == "Song Artist"


class TestCollectVideosFallback:
    @pytest.mark.asyncio
    async def test_falls_back_to_api_v3_when_ytdlp_fails(self, tmp_dir):
        """When yt-dlp returns nothing and API key is set, should try API v3."""
        with patch(
            "App.services.youtube_learning.youtube_collector._collect_via_ytdlp",
            new_callable=AsyncMock,
            return_value=[],
        ) as mock_ytdlp, patch(
            "App.services.youtube_learning.youtube_collector._collect_via_api_v3",
            new_callable=AsyncMock,
            return_value=[{"video_id": "fallback1", "title": "Fallback Song"}],
        ) as mock_api, patch(
            "App.services.youtube_learning.youtube_collector.settings"
        ) as mock_settings:
            mock_settings.youtube_max_videos_per_run = 5
            mock_settings.youtube_temp_path = str(tmp_dir)
            mock_settings.youtube_api_key = "test-key"

            results = await collect_videos(5)

            mock_ytdlp.assert_called_once()
            mock_api.assert_called_once()
            assert len(results) == 1
            assert results[0]["video_id"] == "fallback1"

    @pytest.mark.asyncio
    async def test_no_fallback_without_api_key(self, tmp_dir):
        """When yt-dlp returns nothing and no API key, should return empty."""
        with patch(
            "App.services.youtube_learning.youtube_collector._collect_via_ytdlp",
            new_callable=AsyncMock,
            return_value=[],
        ), patch(
            "App.services.youtube_learning.youtube_collector._collect_via_api_v3",
            new_callable=AsyncMock,
        ) as mock_api, patch(
            "App.services.youtube_learning.youtube_collector.settings"
        ) as mock_settings:
            mock_settings.youtube_max_videos_per_run = 5
            mock_settings.youtube_temp_path = str(tmp_dir)
            mock_settings.youtube_api_key = ""

            results = await collect_videos(5)

            mock_api.assert_not_called()
            assert results == []

    @pytest.mark.asyncio
    async def test_no_fallback_when_ytdlp_succeeds(self, tmp_dir):
        """When yt-dlp succeeds, should NOT call API v3."""
        with patch(
            "App.services.youtube_learning.youtube_collector._collect_via_ytdlp",
            new_callable=AsyncMock,
            return_value=[{"video_id": "yt1"}],
        ), patch(
            "App.services.youtube_learning.youtube_collector._collect_via_api_v3",
            new_callable=AsyncMock,
        ) as mock_api, patch(
            "App.services.youtube_learning.youtube_collector.settings"
        ) as mock_settings:
            mock_settings.youtube_max_videos_per_run = 5
            mock_settings.youtube_temp_path = str(tmp_dir)
            mock_settings.youtube_api_key = "test-key"

            results = await collect_videos(5)

            mock_api.assert_not_called()
            assert len(results) == 1
