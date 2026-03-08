from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..internal.config import get_settings
from ..services.trend_agent.trend_crawler import get_trending_tracks
from ..services.trend_agent.trend_analyzer import analyze_trend
from ..services.trend_agent.prompt_enhancer import enhance_prompt

router = APIRouter()
settings = get_settings()


class EnhanceRequest(BaseModel):
    prompt: str
    genre: str = "pop"


@router.get("/tracks")
async def trending_tracks(genre: str = "pop"):
    if not settings.trend_enabled:
        raise HTTPException(status_code=503, detail="Trend agent is disabled")
    tracks = await get_trending_tracks(genre)
    return {"genre": genre, "tracks": tracks}


@router.get("/analysis")
async def trend_analysis(genre: str = "pop"):
    if not settings.trend_enabled:
        raise HTTPException(status_code=503, detail="Trend agent is disabled")
    tracks = await get_trending_tracks(genre)
    analysis = await analyze_trend(tracks, genre)
    return {"genre": genre, "analysis": analysis}


@router.post("/enhance")
async def enhance(req: EnhanceRequest):
    if not settings.trend_enabled:
        return {"original": req.prompt, "enhanced": req.prompt, "trend_applied": False}
    enhanced = await enhance_prompt(req.prompt, req.genre)
    return {
        "original": req.prompt,
        "enhanced": enhanced,
        "trend_applied": enhanced != req.prompt,
    }
