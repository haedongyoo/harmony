from pathlib import Path
from typing import Dict, Optional, Any

# 모듈 레벨 싱글톤 — 프로세스 수명 동안 Demucs 모델을 메모리에 유지
_model: Optional[Any] = None


def _get_model():
    """Demucs 모델을 최초 1회만 로드하고 이후엔 캐시된 인스턴스 반환."""
    global _model
    if _model is None:
        # macOS Python 3.9는 시스템 인증서를 기본으로 사용하지 않으므로 certifi로 보완
        import os
        try:
            import certifi
            os.environ.setdefault("SSL_CERT_FILE", certifi.where())
        except ImportError:
            pass
        try:
            from demucs.pretrained import get_model
        except ImportError:
            raise RuntimeError(
                "demucs 패키지가 설치되지 않았습니다. pip install demucs 를 실행하세요."
            )
        _model = get_model("htdemucs")
        _model.eval()
    return _model


async def split_tracks(wav_path: str) -> Dict[str, str]:
    """
    Demucs Python API로 WAV를 4개 스템으로 분리 (인메모리, subprocess 없음).
    Returns: { "vocals": path, "drums": path, "bass": path, "other": path }
    """
    import torch
    import torchaudio
    from demucs.apply import apply_model
    from demucs.audio import convert_audio, save_audio

    wav_file = Path(wav_path)
    stems_dir = wav_file.parent / "stems"
    stems_dir.mkdir(parents=True, exist_ok=True)

    model = _get_model()

    # 오디오 로드 및 모델 사양에 맞게 변환 (samplerate, channels)
    mix, sr = torchaudio.load(str(wav_file))
    mix = convert_audio(mix, sr, model.samplerate, model.audio_channels)
    mix = mix.unsqueeze(0)  # (1, channels, samples)

    # 스템 분리 — apply_model 내부가 no_grad를 일부만 감싸므로 전체 래핑
    with torch.no_grad():
        sources = apply_model(
            model, mix,
            device="cpu",
            shifts=1,       # 랜덤 시프트 앙상블로 품질 향상 (2배 느려짐; 속도 우선 시 0으로)
            split=True,
            overlap=0.25,
            progress=False,
        )
    # sources shape: (1, num_sources, channels, samples)

    paths: Dict[str, str] = {}
    for idx, stem_name in enumerate(model.sources):
        stem_wav = sources[0, idx].cpu()  # (channels, samples)
        out_path = stems_dir / f"{stem_name}.wav"
        save_audio(stem_wav, out_path, model.samplerate)
        paths[stem_name] = str(out_path)

    return paths
