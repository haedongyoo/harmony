import os
import sys
import types
import pytest

# Ensure App package is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set test environment variables before any App imports
os.environ.setdefault("DATABASE_URL", "sqlite:///./test_music_studio.db")
os.environ.setdefault("OLLAMA_BASE_URL", "http://localhost:11434")
os.environ.setdefault("YOUTUBE_LEARNING_ENABLED", "false")
os.environ.setdefault("RAG_ENABLED", "true")
os.environ.setdefault("TREND_ENABLED", "false")

# Stub out heavy dependencies not installed in test env.
# Each stub needs __spec__ to satisfy importlib.util.find_spec checks.
for mod_name in [
    "torchaudio", "torchaudio.transforms",
    "demucs", "demucs.pretrained", "demucs.apply",
    "audiocraft", "audiocraft.models", "audiocraft.models.musicgen",
]:
    if mod_name not in sys.modules:
        stub = types.ModuleType(mod_name)
        stub.__spec__ = types.SimpleNamespace(
            name=mod_name, loader=None, origin=None, submodule_search_locations=[]
        )
        sys.modules[mod_name] = stub


@pytest.fixture
def tmp_dir(tmp_path):
    """Provide a temporary directory for test artifacts."""
    return tmp_path


@pytest.fixture
def sample_video_data():
    """Sample video metadata as returned by youtube_collector."""
    return {
        "video_id": "dQw4w9WgXcQ",
        "title": "Never Gonna Give You Up",
        "artist": "Rick Astley",
        "channel": "Rick Astley",
        "description": "The official video for Rick Astley - Never Gonna Give You Up",
        "tags": ["pop", "80s", "dance", "rick astley"],
        "genre": "pop",
        "view_count": 1_500_000_000,
        "duration_seconds": 213,
        "upload_date": "20091025",
        "audio_path": "/tmp/test_audio.wav",
    }


@pytest.fixture
def sample_audio_features():
    """Sample audio features as returned by audio_analyzer."""
    return {
        "bpm": 113.0,
        "key": "A major",
        "energy": 0.095,
        "danceability": 0.72,
        "spectral_centroid": 2850.5,
    }


@pytest.fixture
def sample_video_data_minimal():
    """Minimal video data with missing optional fields."""
    return {
        "video_id": "abc123",
        "title": "Test Song",
        "artist": "",
        "channel": "",
        "description": "",
        "tags": [],
        "genre": "unknown",
        "view_count": None,
        "duration_seconds": None,
        "upload_date": None,
        "audio_path": None,
    }


@pytest.fixture
def empty_audio_features():
    """Empty audio features (analysis failed)."""
    return {
        "bpm": None,
        "key": None,
        "energy": None,
        "danceability": None,
        "spectral_centroid": None,
    }
