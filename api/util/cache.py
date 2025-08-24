import os, sqlite3, time, json
from contextlib import contextmanager
from typing import Any, Optional

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "..", "data", "cache.sqlite")
DB_PATH = os.path.abspath(DB_PATH)
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    try:
        yield conn
    finally:
        conn.close()

def init():
    with get_conn() as conn:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS cache (key TEXT PRIMARY KEY, value TEXT, expires INTEGER)"
        )
        conn.commit()
init()

def set(key: str, value: Any, ttl_seconds: int = 3600) -> None:
    expires = int(time.time()) + ttl_seconds
    payload = json.dumps(value)
    with get_conn() as conn:
        conn.execute(
            "REPLACE INTO cache (key, value, expires) VALUES (?, ?, ?)",
            (key, payload, expires),
        )
        conn.commit()

def get(key: str) -> Optional[Any]:
    now = int(time.time())
    with get_conn() as conn:
        row = conn.execute("SELECT value, expires FROM cache WHERE key = ?", (key,)).fetchone()
    if not row:
        return None
    value, expires = row
    if expires is not None and expires < now:
        with get_conn() as conn:
            conn.execute("DELETE FROM cache WHERE key = ?", (key,))
            conn.commit()
        return None
    return json.loads(value)
