from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator


class Database:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.initialize()

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        try:
            yield connection
            connection.commit()
        finally:
            connection.close()

    def initialize(self) -> None:
        with self.connect() as db:
            db.executescript(
                """
                CREATE TABLE IF NOT EXISTS events (
                  id INTEGER PRIMARY KEY, kind TEXT NOT NULL, subject TEXT NOT NULL,
                  status TEXT NOT NULL, payload TEXT NOT NULL, created_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_events_kind_created ON events(kind, created_at);
                CREATE TABLE IF NOT EXISTS state (
                  namespace TEXT NOT NULL, key TEXT NOT NULL, value TEXT NOT NULL,
                  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                  PRIMARY KEY(namespace, key)
                );
                """
            )

    def add_event(self, kind: str, subject: str, status: str, payload: dict[str, Any]) -> None:
        with self.connect() as db:
            db.execute(
                "INSERT INTO events(kind,subject,status,payload,created_at) VALUES(?,?,?,?,datetime('now'))",
                (kind, subject, status, json.dumps(payload, ensure_ascii=False, default=str)),
            )

    def set_state(self, namespace: str, key: str, value: Any) -> None:
        with self.connect() as db:
            db.execute(
                """INSERT INTO state(namespace,key,value) VALUES(?,?,?)
                ON CONFLICT(namespace,key) DO UPDATE SET value=excluded.value,
                updated_at=CURRENT_TIMESTAMP""",
                (namespace, key, json.dumps(value, ensure_ascii=False, default=str)),
            )

    def get_state(self, namespace: str, key: str, default: Any = None) -> Any:
        with self.connect() as db:
            row = db.execute(
                "SELECT value FROM state WHERE namespace=? AND key=?", (namespace, key)
            ).fetchone()
        return json.loads(row["value"]) if row else default
