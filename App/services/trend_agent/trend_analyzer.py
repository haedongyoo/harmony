import json
from typing import List, Dict
from ..ollama_client import complete


async def analyze_trend(tracks: List[Dict], genre: str) -> Dict:
    """
    Ollama로 트렌딩 트랙 목록 분석 → 음악적 특성 추출.
    Returns: { bpm_range, instruments, mood_keywords, style_tags }
    """
    track_list = "\n".join(
        f"- {t['title']} by {t['artist']}" for t in tracks[:20]
    )
    prompt = f"""다음은 현재 {genre} 장르의 인기 트랙 목록입니다:

{track_list}

이 트랙들의 공통적인 음악적 특성을 분석해서 JSON으로 답해주세요.
형식:
{{
  "bpm_range": "<BPM 범위, 예: 90-110>",
  "instruments": ["<악기1>", "<악기2>", "<악기3>"],
  "mood_keywords": ["<분위기1>", "<분위기2>"],
  "style_tags": ["<스타일1>", "<스타일2>"]
}}

위의 꺾쇠(<>) 안 내용은 예시입니다. 실제 트랙 목록을 분석한 결과로 채워주세요.
JSON만 출력하세요. 설명 없이."""

    raw = await complete(prompt)

    # JSON 파싱 시도
    try:
        start = raw.find("{")
        end = raw.rfind("}") + 1
        return json.loads(raw[start:end])
    except (json.JSONDecodeError, ValueError):
        return {
            "bpm_range": "",
            "instruments": [],
            "mood_keywords": [],
            "style_tags": [genre],
        }
