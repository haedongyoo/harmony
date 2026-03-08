import os
import uuid
from pathlib import Path
from typing import Optional, Any

from ..internal.config import get_settings

settings = get_settings()

# 모듈 레벨 싱글톤 — 프로세스 수명 동안 모델을 메모리에 유지
_model: Optional[Any] = None
_audio_write = None


def _get_model():
    """MusicGen 모델을 최초 1회만 로드하고 이후엔 캐시된 인스턴스 반환."""
    global _model, _audio_write
    if _model is None:
        try:
            from audiocraft.models import MusicGen
            from audiocraft.data.audio import audio_write as _aw
        except ImportError:
            raise RuntimeError(
                "audiocraft 패키지가 설치되지 않았습니다. pip install audiocraft 를 실행하세요."
            )
        _model = MusicGen.get_pretrained("facebook/musicgen-small")
        _audio_write = _aw
    return _model, _audio_write


def _generate_sync(prompt: str, duration: int, output_dir: Path) -> str:
    """동기 함수: MusicGen 생성 + WAV 저장 (스레드 풀에서 실행)."""
    model, audio_write = _get_model()
    model.set_generation_params(duration=min(duration, settings.max_music_duration))

    descriptions = [prompt]
    wav = model.generate(descriptions)  # shape: (1, channels, samples)

    track_name = str(uuid.uuid4())
    out_path = output_dir / track_name
    audio_write(
        str(out_path),
        wav[0].cpu(),
        model.sample_rate,
        strategy="loudness",
        loudness_compressor=True,
    )
    return str(out_path) + ".wav"


async def generate_music(
    prompt: str,
    duration: int,
    session_id: str,
    progress_callback=None,
) -> str:
    """
    MusicGen(audiocraft)으로 음악 생성.
    블로킹 generate()를 스레드 풀에서 실행하여 이벤트 루프 차단 방지.
    Returns: 생성된 WAV 파일 경로
    """
    import asyncio

    output_dir = Path(settings.music_output_path) / session_id
    output_dir.mkdir(parents=True, exist_ok=True)

    loop = asyncio.get_event_loop()
    wav_path = await loop.run_in_executor(
        None, _generate_sync, prompt, duration, output_dir
    )
    return wav_path
