from pathlib import Path
from pydantic_settings import BaseSettings
from functools import lru_cache

# App/.env — 항상 이 파일 기준 절대 경로로 찾음
_ENV_FILE = Path(__file__).parent.parent / ".env"


class Settings(BaseSettings):
    database_url: str = "sqlite:///./music_studio.db"

    ollama_base_url: str = "http://localhost:11434"
    ollama_chat_model: str = "llama3.2"

    music_output_path: str = "./outputs"
    max_music_duration: int = 60

    lastfm_api_key: str = ""
    trend_cache_ttl: int = 86400
    trend_enabled: bool = True

    log_level: str = "INFO"

    # YouTube Learning System
    youtube_learning_enabled: bool = True
    youtube_collection_interval_hours: int = 6
    youtube_max_videos_per_run: int = 20
    youtube_audio_keep: bool = False
    youtube_temp_path: str = "./outputs/youtube_temp"
    youtube_api_key: str = ""

    # ChromaDB
    chromadb_path: str = "./chromadb_data"
    chromadb_collection_name: str = "music_knowledge"

    # Embedding / RAG
    embedding_model: str = "all-MiniLM-L6-v2"
    rag_top_k: int = 5
    rag_enabled: bool = True

    model_config = {"env_file": str(_ENV_FILE), "env_file_encoding": "utf-8", "extra": "ignore"}


@lru_cache()
def get_settings() -> Settings:
    return Settings()
