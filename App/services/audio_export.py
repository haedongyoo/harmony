import io
import zipfile
from pathlib import Path
from datetime import datetime
from typing import Dict


def build_zip(session_id: str, track_paths: Dict[str, str]) -> bytes:
    """
    track_paths: { "master": "/path/to/master.wav", "vocals": ..., ... }
    Returns ZIP bytes.
    """
    buf = io.BytesIO()
    ts = datetime.utcnow().strftime("%Y%m%d%H%M%S")

    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for instrument, path in track_paths.items():
            if not path:
                continue
            p = Path(path)
            if not p.exists():
                continue
            filename = f"{session_id}_{instrument}_{ts}.wav"
            zf.write(p, arcname=filename)

    buf.seek(0)
    return buf.read()
