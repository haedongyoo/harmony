import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .internal.config import get_settings
from .internal.db import init_db
from .routers import chat_service, music_service, export_service, trend_service, learning_service
from .models import youtube_tracks  # noqa: F401  — ensure table is created by init_db

settings = get_settings()
logging.basicConfig(level=settings.log_level)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()

    # Start YouTube learning scheduler
    if settings.youtube_learning_enabled:
        from .services.youtube_learning.scheduler import start_scheduler, stop_scheduler
        await start_scheduler()

    yield

    # Shutdown
    if settings.youtube_learning_enabled:
        from .services.youtube_learning.scheduler import stop_scheduler
        await stop_scheduler()


app = FastAPI(title="AI Music Studio", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://localhost:8001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_service.router, prefix="/api/chat", tags=["chat"])
app.include_router(music_service.router, prefix="/api/music", tags=["music"])
app.include_router(export_service.router, prefix="/api/export", tags=["export"])
app.include_router(trend_service.router, prefix="/api/trend", tags=["trend"])
app.include_router(learning_service.router, prefix="/api/learning", tags=["learning"])


@app.get("/health")
async def health():
    return {"status": "ok"}
