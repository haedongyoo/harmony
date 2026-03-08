from .trend_crawler import get_trending_tracks
from .trend_analyzer import analyze_trend


async def enhance_prompt(original_prompt: str, genre: str = "pop") -> str:
    """
    원본 프롬프트에 트렌드 특성을 추가. 원본 의도는 절대 덮어쓰지 않음.
    오류 시 원본 프롬프트 반환 (fallback).
    """
    try:
        tracks = await get_trending_tracks(genre)
        if not tracks:
            return original_prompt

        analysis = await analyze_trend(tracks, genre)

        additions = []
        if analysis.get("bpm_range"):
            additions.append(f"{analysis['bpm_range']} BPM")
        if analysis.get("instruments"):
            additions.extend(analysis["instruments"][:3])
        if analysis.get("mood_keywords"):
            additions.extend(analysis["mood_keywords"][:2])
        if analysis.get("style_tags"):
            additions.extend(analysis["style_tags"][:2])

        if not additions:
            return original_prompt

        enhancement = ", ".join(additions)
        return f"{original_prompt}, {enhancement}"

    except Exception:
        # 트렌드 에이전트 실패 시 원본 프롬프트로 fallback
        return original_prompt
