from __future__ import annotations

import logging
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Dict, Iterator, Optional

import bcrypt

LOGGER = logging.getLogger(__name__)
DB_PATH = Path(__file__).resolve().parent / "users.db"


def _ensure_parent() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)


@contextmanager
def _connect() -> Iterator[sqlite3.Connection]:
    _ensure_parent()
    conn = sqlite3.connect(DB_PATH)
    try:
        yield conn
    finally:
        conn.close()


def init_db() -> None:
    with _connect() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL
            )
            """
        )
        conn.commit()
    LOGGER.info("User database initialized at %s", DB_PATH)


def has_users() -> bool:
    with _connect() as conn:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(1) FROM users")
        (count,) = cur.fetchone() or (0,)
    return count > 0


def create_user(username: str, password: str, role: str) -> None:
    password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    with _connect() as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
            (username, password_hash, role),
        )
        conn.commit()


def get_user(username: str) -> Optional[Dict[str, str]]:
    with _connect() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT username, password_hash, role FROM users WHERE username=?",
            (username,),
        )
        row = cur.fetchone()
    if not row:
        return None
    return {"username": row[0], "password_hash": row[1], "role": row[2]}


__all__ = ["init_db", "create_user", "get_user", "has_users"]

