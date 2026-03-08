"""Tests for App.services.youtube_learning.knowledge_builder"""
import pytest
from App.services.youtube_learning.knowledge_builder import (
    build_document,
    build_metadata,
    _energy_to_text,
    _danceability_to_text,
    _popularity_tier,
)


class TestBuildDocument:
    def test_full_data(self, sample_video_data, sample_audio_features):
        doc = build_document(sample_video_data, sample_audio_features, "energetic")

        assert '"Never Gonna Give You Up" by Rick Astley' in doc
        assert "Genre: pop" in doc
        assert "Tempo: 113.0 BPM" in doc
        assert "Key: A major" in doc
        assert "Mood: energetic" in doc
        assert "Energy level:" in doc
        assert "Danceability:" in doc
        assert "Tonal character:" in doc
        assert "Popularity:" in doc
        assert "Tags:" in doc

    def test_minimal_data(self, sample_video_data_minimal, empty_audio_features):
        doc = build_document(sample_video_data_minimal, empty_audio_features, "unknown")

        assert '"Test Song"' in doc
        assert "Genre: unknown" in doc
        # Should NOT contain fields for None/empty values
        assert "Tempo:" not in doc
        assert "Key:" not in doc
        assert "Mood:" not in doc
        assert "Energy level:" not in doc
        assert "Danceability:" not in doc
        assert "Popularity:" not in doc
        assert "Tags:" not in doc

    def test_partial_features(self, sample_video_data):
        features = {"bpm": 120.0, "key": None, "energy": None, "danceability": None, "spectral_centroid": None}
        doc = build_document(sample_video_data, features, "chill")

        assert "Tempo: 120.0 BPM" in doc
        assert "Mood: chill" in doc
        assert "Key:" not in doc

    def test_tags_limited_to_10(self, sample_video_data, sample_audio_features):
        sample_video_data["tags"] = [f"tag{i}" for i in range(20)]
        doc = build_document(sample_video_data, sample_audio_features, "happy")

        tags_line = [l for l in doc.split("\n") if l.startswith("Tags:")][0]
        # Should only contain first 10 tags
        assert "tag9" in tags_line
        assert "tag10" not in tags_line

    def test_empty_features_dict(self, sample_video_data):
        doc = build_document(sample_video_data, {}, "unknown")
        assert '"Never Gonna Give You Up"' in doc
        assert "Genre: pop" in doc

    def test_spectral_brightness_categories(self, sample_video_data):
        # Dark
        doc = build_document(sample_video_data, {"bpm": None, "key": None, "energy": None, "danceability": None, "spectral_centroid": 1000.0}, "")
        assert "dark" in doc

        # Warm
        doc = build_document(sample_video_data, {"bpm": None, "key": None, "energy": None, "danceability": None, "spectral_centroid": 2000.0}, "")
        assert "warm" in doc

        # Bright
        doc = build_document(sample_video_data, {"bpm": None, "key": None, "energy": None, "danceability": None, "spectral_centroid": 4000.0}, "")
        assert "bright" in doc


class TestBuildMetadata:
    def test_full_metadata(self, sample_video_data, sample_audio_features):
        meta = build_metadata(sample_video_data, sample_audio_features, "energetic")

        assert meta["video_id"] == "dQw4w9WgXcQ"
        assert meta["title"] == "Never Gonna Give You Up"
        assert meta["artist"] == "Rick Astley"
        assert meta["genre"] == "pop"
        assert meta["bpm"] == 113.0
        assert meta["key"] == "A major"
        assert meta["energy"] == 0.095
        assert meta["danceability"] == 0.72
        assert meta["mood"] == "energetic"
        assert meta["view_count"] == 1_500_000_000

    def test_metadata_defaults_for_none(self, sample_video_data_minimal, empty_audio_features):
        meta = build_metadata(sample_video_data_minimal, empty_audio_features, None)

        assert meta["bpm"] == 0.0
        assert meta["key"] == ""
        assert meta["energy"] == 0.0
        assert meta["danceability"] == 0.0
        assert meta["mood"] == "unknown"
        assert meta["view_count"] == 0

    def test_title_truncation(self, sample_video_data, sample_audio_features):
        sample_video_data["title"] = "X" * 300
        meta = build_metadata(sample_video_data, sample_audio_features, "happy")
        assert len(meta["title"]) == 200

    def test_artist_truncation(self, sample_video_data, sample_audio_features):
        sample_video_data["artist"] = "Y" * 200
        meta = build_metadata(sample_video_data, sample_audio_features, "happy")
        assert len(meta["artist"]) == 100

    def test_all_values_are_chromadb_compatible(self, sample_video_data, sample_audio_features):
        """ChromaDB metadata values must be str, int, float, or bool."""
        meta = build_metadata(sample_video_data, sample_audio_features, "chill")
        for key, value in meta.items():
            assert isinstance(value, (str, int, float, bool)), (
                f"Key '{key}' has type {type(value)}, which is not ChromaDB-compatible"
            )


class TestHelperFunctions:
    @pytest.mark.parametrize("energy,expected", [
        (0.20, "very high"),
        (0.10, "high"),
        (0.05, "moderate"),
        (0.015, "low"),
        (0.005, "very low"),
    ])
    def test_energy_to_text(self, energy, expected):
        assert _energy_to_text(energy) == expected

    @pytest.mark.parametrize("danceability,expected", [
        (0.8, "very danceable"),
        (0.6, "danceable"),
        (0.4, "moderate"),
        (0.2, "low danceability"),
    ])
    def test_danceability_to_text(self, danceability, expected):
        assert _danceability_to_text(danceability) == expected

    @pytest.mark.parametrize("views,expected", [
        (200_000_000, "mega-hit"),
        (50_000_000, "very popular"),
        (5_000_000, "popular"),
        (500_000, "well-known"),
        (50_000, "emerging"),
    ])
    def test_popularity_tier(self, views, expected):
        assert _popularity_tier(views) == expected
