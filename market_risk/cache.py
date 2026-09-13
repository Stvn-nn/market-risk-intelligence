"""Small SQLite cache; parameterized keys and an explicit TTL."""
import json
import os
import sqlite3
import time
from pathlib import Path


def cache_path() -> Path:
    return Path(os.environ.get('MARKET_RISK_CACHE', str(Path.home()/'.market-risk-intelligence'/'cache.sqlite3')))


def connect():
    path = cache_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, timeout=3)
    conn.execute('CREATE TABLE IF NOT EXISTS responses (cache_key TEXT PRIMARY KEY, fetched REAL NOT NULL, payload TEXT NOT NULL)')
    return conn


def get(key: str, ttl: int = 3600):
    with connect() as conn:
        row = conn.execute('SELECT fetched,payload FROM responses WHERE cache_key=?',(key,)).fetchone()
    if row and time.time()-row[0] < ttl:
        return json.loads(row[1]), row[0]
    return None


def put(key: str, payload: dict):
    with connect() as conn:
        conn.execute('INSERT OR REPLACE INTO responses VALUES (?,?,?)',(key,time.time(),json.dumps(payload,allow_nan=False)))
