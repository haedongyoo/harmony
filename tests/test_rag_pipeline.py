"""Tests for App.services.youtube_learning.rag_indexer and rag_retriever"""
import os
import pytest
import pytest_asyncio
from unittest.mock import patch


@pytest.fixture(autouse=True)
def reset_rag_singletons():
    """Reset module-level singletons before each test."""
    import App.services.youtube_learning.rag_indexer as idx
    idx._client = None
    idx._collection = None
    yield
    idx._client = None
    idx._collection = None


@pytest.fixture
def chromadb_dir(tmp_dir):
    """Patch ChromaDB path to use temp directory."""
    path = str(tmp_dir / "chromadb_test")
    with patch.object(
        __import__("App.internal.config", fromlist=["get_settings"]).get_settings(),
        "chromadb_path",
        path,
    ):
        # Also need to reset the module-level settings reference in rag_indexer
        import App.services.youtube_learning.rag_indexer as idx
        original = idx.settings.chromadb_path
        object.__setattr__(idx.settings, "chromadb_path", path)
        yield path
        object.__setattr__(idx.settings, "chromadb_path", original)


class TestRagIndexer:
    def test_index_and_retrieve_document(self, chromadb_dir):
        from App.services.youtube_learning.rag_indexer import index_document, _get_collection

        doc_id = index_document(
            "test1",
            'Song: "Test" by Artist\nGenre: pop\nTempo: 120 BPM',
            {"video_id": "test1", "title": "Test", "artist": "Artist", "genre": "pop",
             "bpm": 120.0, "key": "C major", "energy": 0.1, "danceability": 0.5,
             "mood": "happy", "view_count": 1000},
        )

        assert doc_id == "yt_test1"

        collection = _get_collection()
        assert collection.count() == 1

    def test_upsert_idempotent(self, chromadb_dir):
        from App.services.youtube_learning.rag_indexer import index_document, _get_collection

        meta = {"video_id": "dup1", "title": "X", "artist": "Y", "genre": "pop",
                "bpm": 0.0, "key": "", "energy": 0.0, "danceability": 0.0,
                "mood": "unknown", "view_count": 0}

        index_document("dup1", "Document version 1", meta)
        index_document("dup1", "Document version 2", meta)

        collection = _get_collection()
        assert collection.count() == 1  # Upsert, not duplicate

    def test_batch_index(self, chromadb_dir):
        from App.services.youtube_learning.rag_indexer import index_batch, _get_collection

        ids = [f"batch{i}" for i in range(5)]
        docs = [f"Song {i} description" for i in range(5)]
        metas = [
            {"video_id": f"batch{i}", "title": f"Song {i}", "artist": "A", "genre": "pop",
             "bpm": 120.0 + i, "key": "C major", "energy": 0.1, "danceability": 0.5,
             "mood": "happy", "view_count": 1000}
            for i in range(5)
        ]

        result_ids = index_batch(ids, docs, metas)
        assert len(result_ids) == 5

        collection = _get_collection()
        assert collection.count() == 5

    def test_get_collection_stats(self, chromadb_dir):
        from App.services.youtube_learning.rag_indexer import index_document, get_collection_stats

        index_document(
            "s1", "Doc 1",
            {"video_id": "s1", "title": "T", "artist": "A", "genre": "pop",
             "bpm": 0.0, "key": "", "energy": 0.0, "danceability": 0.0,
             "mood": "unknown", "view_count": 0}
        )

        stats = get_collection_stats()
        assert stats["total_documents"] == 1
        assert "collection_name" in stats
        assert "embedding_model" in stats

    def test_delete_document(self, chromadb_dir):
        from App.services.youtube_learning.rag_indexer import index_document, delete_document, _get_collection

        index_document(
            "del1", "To delete",
            {"video_id": "del1", "title": "T", "artist": "A", "genre": "pop",
             "bpm": 0.0, "key": "", "energy": 0.0, "danceability": 0.0,
             "mood": "unknown", "view_count": 0}
        )
        assert _get_collection().count() == 1

        delete_document("yt_del1")
        assert _get_collection().count() == 0


class TestRagRetriever:
    @pytest.mark.asyncio
    async def test_retrieve_context_empty_collection(self, chromadb_dir):
        from App.services.youtube_learning.rag_retriever import retrieve_context

        result = await retrieve_context("pop music trends")
        assert result == ""

    @pytest.mark.asyncio
    async def test_retrieve_context_with_documents(self, chromadb_dir):
        from App.services.youtube_learning.rag_indexer import index_document
        from App.services.youtube_learning.rag_retriever import retrieve_context

        meta = {"video_id": "pop1", "title": "Pop Hit", "artist": "PopStar", "genre": "pop",
                "bpm": 120.0, "key": "C major", "energy": 0.1, "danceability": 0.7,
                "mood": "happy", "view_count": 1000000}

        index_document(
            "pop1",
            'Song: "Pop Hit" by PopStar\nGenre: pop\nTempo: 120 BPM\nMood: happy\nDanceability: very danceable',
            meta,
        )

        result = await retrieve_context("popular pop music with high energy")
        # Should return context (may or may not match depending on embedding similarity)
        # At minimum, it should not crash
        assert isinstance(result, str)

    @pytest.mark.asyncio
    async def test_retrieve_context_rag_disabled(self, chromadb_dir):
        import App.services.youtube_learning.rag_retriever as ret
        original = ret.settings.rag_enabled
        object.__setattr__(ret.settings, "rag_enabled", False)

        try:
            result = await ret.retrieve_context("anything")
            assert result == ""
        finally:
            object.__setattr__(ret.settings, "rag_enabled", original)

    @pytest.mark.asyncio
    async def test_retrieve_for_prompt_enhancement_empty(self, chromadb_dir):
        from App.services.youtube_learning.rag_retriever import retrieve_for_prompt_enhancement

        result = await retrieve_for_prompt_enhancement("electronic dance music", genre="electronic")
        assert result == []

    @pytest.mark.asyncio
    async def test_retrieve_context_format(self, chromadb_dir):
        from App.services.youtube_learning.rag_indexer import index_document
        from App.services.youtube_learning.rag_retriever import retrieve_context

        meta = {"video_id": "fmt1", "title": "Format Test", "artist": "A", "genre": "pop",
                "bpm": 0.0, "key": "", "energy": 0.0, "danceability": 0.0,
                "mood": "unknown", "view_count": 0}

        index_document("fmt1", "Pop song about love and dancing in the summer", meta)

        result = await retrieve_context("pop song about love")
        if result:  # Only check format if something was retrieved
            assert "참고 음악 지식" in result or "참고" in result
