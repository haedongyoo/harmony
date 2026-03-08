import json
import time
import sqlite3
from pathlib import Path
from typing import Optional

_DB_PATH = Path(__file__).parent.parent.parent / "trend_cache.db"


def _conn() -> sqlite3.Connection:
    con = sqlite3.connect(str(_DB_PATH))
    con.execute(
        "CREATE TABLE IF NOT EXISTS trend_cache "
        "(key TEXT PRIMARY KEY, value TEXT, expires_at REAL)"
    )
    con.commit()
    return con


def get(key: str) -> Optional[dict]:
    with _conn() as con:
        row = con.execute(
            "SELECT value, expires_at FROM trend_cache WHERE key = ?", (key,)
        ).fetchone()
    if row is None:
        return None
    value, expires_at = row
    if time.time() > expires_at:
        return None
    return json.loads(value)


def set(key: str, value: dict, ttl: int) -> None:
    expires_at = time.time() + ttl
    with _conn() as con:
        con.execute(
            "INSERT OR REPLACE INTO trend_cache (key, value, expires_at) VALUES (?, ?, ?)",
            (key, json.dumps(value), expires_at),
        )
        con.commit()
