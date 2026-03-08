"""Tests for App.routers.learning_service (API integration tests)"""
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from httpx import AsyncClient, ASGITransport


@pytest.fixture
async def client():
    """Create test client with mocked internals."""
    with patch("App.internal.db.init_db", new_callable=AsyncMock):
        import App.services.youtube_learning.scheduler as sched
        original = sched.settings.youtube_learning_enabled
        object.__setattr__(sched.settings, "youtube_learning_enabled", False)

        try:
            from App.main import app
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                yield ac
        finally:
            object.__setattr__(sched.settings, "youtube_learning_enabled", original)


class TestStatusEndpoint:
    @pytest.mark.asyncio
    async def test_status_returns_200(self, client):
        with patch(
            "App.services.youtube_learning.scheduler.get_scheduler",
            return_value=None,
        ), patch(
            "App.services.youtube_learning.scheduler.get_last_run_status",
            return_value={"status": "never_run", "timestamp": None, "detail": None},
        ), patch(
            "App.services.youtube_learning.rag_indexer.get_collection_stats",
            return_value={"total_documents": 0},
        ), patch(
            "App.internal.db.AsyncSessionLocal",
        ) as mock_session_cls:
            mock_db = AsyncMock()
            mock_result = MagicMock()
            mock_result.scalar.return_value = 0
            mock_db.execute.return_value = mock_result
            mock_db.__aenter__ = AsyncMock(return_value=mock_db)
            mock_db.__aexit__ = AsyncMock(return_value=False)
            mock_session_cls.return_value = mock_db

            resp = await client.get("/api/learning/status")
            assert resp.status_code == 200
            data = resp.json()
            assert "youtube_learning_enabled" in data
            assert "scheduler_running" in data
            assert "total_documents_indexed" in data
            assert "last_run" in data


class TestCollectEndpoint:
    @pytest.mark.asyncio
    async def test_collect_starts_task(self, client):
        import App.routers.learning_service as ls
        original = ls.settings.youtube_learning_enabled
        object.__setattr__(ls.settings, "youtube_learning_enabled", True)

        try:
            with patch(
                "App.services.youtube_learning.scheduler.run_manual_collection",
                new_callable=AsyncMock,
            ):
                resp = await client.post("/api/learning/collect", json={"max_videos": 3})
                assert resp.status_code == 200
                data = resp.json()
                assert data["status"] == "started"
                assert "3" in data["message"]
        finally:
            object.__setattr__(ls.settings, "youtube_learning_enabled", original)

    @pytest.mark.asyncio
    async def test_collect_disabled(self, client):
        import App.routers.learning_service as ls
        original = ls.settings.youtube_learning_enabled
        object.__setattr__(ls.settings, "youtube_learning_enabled", False)

        try:
            resp = await client.post("/api/learning/collect", json={"max_videos": 3})
            assert resp.status_code == 503
        finally:
            object.__setattr__(ls.settings, "youtube_learning_enabled", original)

    @pytest.mark.asyncio
    async def test_collect_validates_max_videos(self, client):
        import App.routers.learning_service as ls
        original = ls.settings.youtube_learning_enabled
        object.__setattr__(ls.settings, "youtube_learning_enabled", True)

        try:
            resp = await client.post("/api/learning/collect", json={"max_videos": 0})
            assert resp.status_code == 422

            resp = await client.post("/api/learning/collect", json={"max_videos": 100})
            assert resp.status_code == 422
        finally:
            object.__setattr__(ls.settings, "youtube_learning_enabled", original)


class TestToggleEndpoint:
    @pytest.mark.asyncio
    async def test_toggle_rag_on(self, client):
        resp = await client.post("/api/learning/toggle", params={"enabled": True})
        assert resp.status_code == 200
        assert resp.json()["rag_enabled"] is True

    @pytest.mark.asyncio
    async def test_toggle_rag_off(self, client):
        resp = await client.post("/api/learning/toggle", params={"enabled": False})
        assert resp.status_code == 200
        assert resp.json()["rag_enabled"] is False


class TestRecentEndpoint:
    @pytest.mark.asyncio
    async def test_recent_tracks(self, client):
        with patch("App.internal.db.AsyncSessionLocal") as mock_session_cls:
            mock_track = MagicMock()
            mock_track.video_id = "vid1"
            mock_track.title = "Song 1"
            mock_track.artist = "Artist 1"
            mock_track.genre = "pop"
            mock_track.bpm = 120.0
            mock_track.key = "C major"
            mock_track.mood = "happy"
            mock_track.energy = 0.1
            mock_track.view_count = 1000
            mock_track.processed_at = None

            mock_result = MagicMock()
            mock_scalars = MagicMock()
            mock_scalars.all.return_value = [mock_track]
            mock_result.scalars.return_value = mock_scalars

            mock_db = AsyncMock()
            mock_db.execute.return_value = mock_result
            mock_db.__aenter__ = AsyncMock(return_value=mock_db)
            mock_db.__aexit__ = AsyncMock(return_value=False)
            mock_session_cls.return_value = mock_db

            resp = await client.get("/api/learning/recent", params={"limit": 5})
            assert resp.status_code == 200
            data = resp.json()
            assert len(data) == 1
            assert data[0]["video_id"] == "vid1"
            assert data[0]["title"] == "Song 1"
            assert data[0]["bpm"] == 120.0
