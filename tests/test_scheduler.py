"""Tests for App.services.youtube_learning.scheduler"""
import pytest
from unittest.mock import patch, AsyncMock, MagicMock


class TestSchedulerLifecycle:
    @pytest.mark.asyncio
    async def test_start_scheduler_disabled(self):
        """When youtube_learning_enabled=false, scheduler should not start."""
        import App.services.youtube_learning.scheduler as sched

        original = sched.settings.youtube_learning_enabled
        object.__setattr__(sched.settings, "youtube_learning_enabled", False)

        try:
            await sched.start_scheduler()
            assert sched.get_scheduler() is None
        finally:
            object.__setattr__(sched.settings, "youtube_learning_enabled", original)

    @pytest.mark.asyncio
    async def test_stop_scheduler_when_none(self):
        """stop_scheduler should not raise when scheduler is None."""
        import App.services.youtube_learning.scheduler as sched

        sched._scheduler = None
        await sched.stop_scheduler()

    def test_get_last_run_status_default(self):
        import App.services.youtube_learning.scheduler as sched

        sched._last_run_status = {"status": "never_run", "timestamp": None, "detail": None}
        status = sched.get_last_run_status()
        assert status["status"] == "never_run"
        assert status["timestamp"] is None

    def test_get_last_run_status_returns_copy(self):
        import App.services.youtube_learning.scheduler as sched

        status1 = sched.get_last_run_status()
        status1["status"] = "modified"
        status2 = sched.get_last_run_status()
        assert status2["status"] != "modified"


class TestCollectionPipeline:
    @pytest.mark.asyncio
    async def test_pipeline_no_videos(self):
        """Pipeline should complete gracefully when no videos found."""
        import App.services.youtube_learning.scheduler as sched

        with patch(
            "App.services.youtube_learning.youtube_collector.collect_videos",
            new_callable=AsyncMock,
            return_value=[],
        ):
            await sched.run_collection_pipeline()

            status = sched.get_last_run_status()
            assert status["status"] == "completed"
            assert "No new videos" in status["detail"]

    @pytest.mark.asyncio
    async def test_pipeline_error_handling(self):
        """Pipeline should set error status on failure."""
        import App.services.youtube_learning.scheduler as sched

        with patch(
            "App.services.youtube_learning.youtube_collector.collect_videos",
            new_callable=AsyncMock,
            side_effect=Exception("Network failure"),
        ):
            await sched.run_collection_pipeline()

            status = sched.get_last_run_status()
            assert status["status"] == "error"
            assert "Network failure" in status["detail"]

    @pytest.mark.asyncio
    async def test_pipeline_processes_videos(self):
        """Pipeline should process videos through the full chain."""
        import App.services.youtube_learning.scheduler as sched

        mock_video = {
            "video_id": "pipeline_test",
            "title": "Pipeline Test",
            "artist": "Test",
            "channel": "Test",
            "description": "Test",
            "tags": ["test"],
            "genre": "pop",
            "view_count": 100,
            "duration_seconds": 60,
            "upload_date": "20240101",
            "audio_path": None,
        }

        with patch(
            "App.services.youtube_learning.youtube_collector.collect_videos",
            new_callable=AsyncMock,
            return_value=[mock_video],
        ), patch(
            "App.services.youtube_learning.audio_analyzer.analyze_audio",
            new_callable=AsyncMock,
            return_value={"bpm": 120.0},
        ), patch(
            "App.services.youtube_learning.audio_analyzer.derive_mood_from_features",
            new_callable=AsyncMock,
            return_value="happy",
        ), patch(
            "App.services.youtube_learning.rag_indexer.index_document",
            return_value="yt_pipeline_test",
        ) as mock_index, patch(
            "App.services.youtube_learning.scheduler.AsyncSessionLocal",
        ) as mock_session_cls:
            mock_db = AsyncMock()
            mock_result = MagicMock()
            mock_result.fetchall.return_value = []
            mock_db.execute.return_value = mock_result
            mock_db.__aenter__ = AsyncMock(return_value=mock_db)
            mock_db.__aexit__ = AsyncMock(return_value=False)
            mock_session_cls.return_value = mock_db

            await sched.run_collection_pipeline()

            status = sched.get_last_run_status()
            assert status["status"] == "completed"
            mock_index.assert_called_once()

    @pytest.mark.asyncio
    async def test_pipeline_skips_existing_videos(self):
        """Pipeline should skip videos already in the database."""
        import App.services.youtube_learning.scheduler as sched

        mock_video = {
            "video_id": "existing_video",
            "title": "Already Processed",
            "artist": "X",
            "channel": "X",
            "description": "",
            "tags": [],
            "genre": "pop",
            "view_count": 0,
            "duration_seconds": 60,
            "upload_date": "20240101",
            "audio_path": None,
        }

        with patch(
            "App.services.youtube_learning.youtube_collector.collect_videos",
            new_callable=AsyncMock,
            return_value=[mock_video],
        ), patch(
            "App.services.youtube_learning.rag_indexer.index_document",
        ) as mock_index, patch(
            "App.services.youtube_learning.scheduler.AsyncSessionLocal",
        ) as mock_session_cls:
            mock_db = AsyncMock()
            mock_result = MagicMock()
            mock_result.fetchall.return_value = [("existing_video",)]
            mock_db.execute.return_value = mock_result
            mock_db.__aenter__ = AsyncMock(return_value=mock_db)
            mock_db.__aexit__ = AsyncMock(return_value=False)
            mock_session_cls.return_value = mock_db

            await sched.run_collection_pipeline()

            mock_index.assert_not_called()


class TestCleanupAudio:
    def test_cleanup_existing_file(self, tmp_dir):
        from App.services.youtube_learning.scheduler import _cleanup_audio

        f = tmp_dir / "to_delete.wav"
        f.write_bytes(b"data")
        assert f.exists()

        _cleanup_audio(str(f))
        assert not f.exists()

    def test_cleanup_nonexistent_file(self):
        from App.services.youtube_learning.scheduler import _cleanup_audio

        _cleanup_audio("/nonexistent/path.wav")
