"""Small SQLite cache for repeatable demos and API rate limits."""
import hashlib
import json
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "pipeline.db"


def _connection():
    connection = sqlite3.connect(DB_PATH)
    connection.execute("CREATE TABLE IF NOT EXISTS cache (cache_key TEXT PRIMARY KEY, value TEXT NOT NULL)")
    connection.execute("CREATE TABLE IF NOT EXISTS events (id INTEGER PRIMARY KEY, stage TEXT, message TEXT, payload TEXT)")
    return connection


def key_for(namespace: str, value: object) -> str:
    raw = json.dumps(value, sort_keys=True, default=str)
    return hashlib.sha256(f"{namespace}:{raw}".encode()).hexdigest()


def get(key: str):
    with _connection() as connection:
        row = connection.execute("SELECT value FROM cache WHERE cache_key = ?", (key,)).fetchone()
    return json.loads(row[0]) if row else None


def put(key: str, value: object) -> None:
    with _connection() as connection:
        connection.execute("INSERT OR REPLACE INTO cache VALUES (?, ?)", (key, json.dumps(value)))


def event(stage: str, message: str, payload: dict | None = None) -> None:
    with _connection() as connection:
        connection.execute("INSERT INTO events(stage, message, payload) VALUES (?, ?, ?)", (stage, message, json.dumps(payload or {})))
