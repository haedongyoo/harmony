from datetime import datetime
from sqlalchemy import String, Integer, Float, Text, DateTime, Boolean, func
from sqlalchemy.orm import Mapped, mapped_column
from ..internal.db import Base


class YouTubeTrack(Base):
    __tablename__ = "youtube_tracks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    video_id: Mapped[str] = mapped_column(String(32), unique=True, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    artist: Mapped[str] = mapped_column(String(256), nullable=True)
    channel: Mapped[str] = mapped_column(String(256), nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    tags: Mapped[str] = mapped_column(Text, nullable=True)
    genre: Mapped[str] = mapped_column(String(64), nullable=True)
    view_count: Mapped[int] = mapped_column(Integer, nullable=True)
    duration_seconds: Mapped[int] = mapped_column(Integer, nullable=True)
    upload_date: Mapped[str] = mapped_column(String(16), nullable=True)

    # Audio features (from librosa analysis)
    bpm: Mapped[float] = mapped_column(Float, nullable=True)
    key: Mapped[str] = mapped_column(String(8), nullable=True)
    energy: Mapped[float] = mapped_column(Float, nullable=True)
    danceability: Mapped[float] = mapped_column(Float, nullable=True)
    spectral_centroid: Mapped[float] = mapped_column(Float, nullable=True)
    mood: Mapped[str] = mapped_column(String(64), nullable=True)

    # Processing state
    is_embedded: Mapped[bool] = mapped_column(Boolean, default=False)
    chromadb_doc_id: Mapped[str] = mapped_column(String(64), nullable=True)
    processed_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
