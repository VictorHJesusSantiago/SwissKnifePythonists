from __future__ import annotations

import json
import sqlite3
from contextlib import closing
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from swissknife.core.utils import atomic_write


def _connect(database: str | Path) -> sqlite3.Connection:
    Path(database).parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(database)
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS maintenance_windows (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            starts_at TEXT NOT NULL,
            ends_at TEXT NOT NULL,
            affected TEXT NOT NULL,
            notified INTEGER NOT NULL DEFAULT 0
        )
        """
    )
    connection.commit()
    return connection


@dataclass(slots=True)
class MaintenanceWindow:
    id: int
    title: str
    starts_at: str
    ends_at: str
    affected: list[str]
    notified: bool


def schedule(database: str | Path, title: str, starts_at: datetime, ends_at: datetime, affected: list[str]) -> dict[str, object]:
    with closing(_connect(database)) as connection:
        cursor = connection.execute(
            "INSERT INTO maintenance_windows (title, starts_at, ends_at, affected, notified) VALUES (?, ?, ?, ?, 0)",
            (title, starts_at.isoformat(), ends_at.isoformat(), json.dumps(affected)),
        )
        connection.commit()
        return {"id": cursor.lastrowid, "title": title, "starts_at": starts_at.isoformat(), "ends_at": ends_at.isoformat()}


def list_windows(database: str | Path, upcoming_only: bool = False) -> list[MaintenanceWindow]:
    with closing(_connect(database)) as connection:
        rows = connection.execute(
            "SELECT id, title, starts_at, ends_at, affected, notified FROM maintenance_windows ORDER BY starts_at ASC"
        ).fetchall()
    windows = [
        MaintenanceWindow(row[0], row[1], row[2], row[3], json.loads(row[4]), bool(row[5])) for row in rows
    ]
    if upcoming_only:
        now = datetime.now(UTC).isoformat()
        windows = [window for window in windows if window.ends_at >= now]
    return windows


def notify(database: str | Path, window_id: int, notifications_dir: str | Path) -> dict[str, object]:
    with closing(_connect(database)) as connection:
        row = connection.execute(
            "SELECT id, title, starts_at, ends_at, affected FROM maintenance_windows WHERE id = ?", (window_id,)
        ).fetchone()
        if row is None:
            raise ValueError(f"Janela de manutenção {window_id} não encontrada")
        connection.execute("UPDATE maintenance_windows SET notified = 1 WHERE id = ?", (window_id,))
        connection.commit()
    content = (
        f"Manutenção agendada: {row[1]}\nInício: {row[2]}\nFim: {row[3]}\nAfetados: {', '.join(json.loads(row[4]))}\n"
    )
    output_path = Path(notifications_dir) / f"manutencao-{window_id}.txt"
    atomic_write(output_path, content)
    return {"notified": True, "path": str(output_path)}
