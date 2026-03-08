from datetime import datetime
from sqlalchemy import String, Integer, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column
from ..internal.db import Base


class Track(Base):
    __tablename__ = "tracks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(String(36), ForeignKey("sessions.id"), nullable=False)
    prompt: Mapped[str] = mapped_column(String(2048), nullable=False)
    duration: Mapped[int] = mapped_column(Integer, default=30)
    # Paths to generated files
    master_path: Mapped[str] = mapped_column(String(512), nullable=True)
    vocals_path: Mapped[str] = mapped_column(String(512), nullable=True)
    drums_path: Mapped[str] = mapped_column(String(512), nullable=True)
    bass_path: Mapped[str] = mapped_column(String(512), nullable=True)
    other_path: Mapped[str] = mapped_column(String(512), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="pending")  # pending | generating | splitting | done | error
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
