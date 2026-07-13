from __future__ import annotations

import sqlite3
from contextlib import closing
from datetime import UTC, datetime
from pathlib import Path


def _connect(database: str | Path) -> sqlite3.Connection:
    Path(database).parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(database)
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS sla_measurements (
            service TEXT NOT NULL,
            recorded_at TEXT NOT NULL,
            good INTEGER NOT NULL,
            total INTEGER NOT NULL
        )
        """
    )
    connection.commit()
    return connection


def record(database: str | Path, service: str, good: int, total: int, recorded_at: datetime | None = None) -> dict[str, object]:
    recorded_at = recorded_at or datetime.now(UTC)
    with closing(_connect(database)) as connection:
        connection.execute(
            "INSERT INTO sla_measurements (service, recorded_at, good, total) VALUES (?, ?, ?, ?)",
            (service, recorded_at.isoformat(), good, total),
        )
        connection.commit()
    return {"service": service, "recorded_at": recorded_at.isoformat(), "good": good, "total": total}


def history(database: str | Path, service: str, since: datetime | None = None) -> list[dict[str, object]]:
    with closing(_connect(database)) as connection:
        query = "SELECT recorded_at, good, total FROM sla_measurements WHERE service = ?"
        params: list[object] = [service]
        if since is not None:
            query += " AND recorded_at >= ?"
            params.append(since.isoformat())
        query += " ORDER BY recorded_at ASC"
        rows = connection.execute(query, params).fetchall()
    return [{"recorded_at": row[0], "good": row[1], "total": row[2]} for row in rows]


def summarize(database: str | Path, service: str, since: datetime | None = None) -> dict[str, object]:
    entries = history(database, service, since)
    good = sum(int(entry["good"]) for entry in entries)
    total = sum(int(entry["total"]) for entry in entries)
    percent = round((good / total) * 100, 4) if total else 0.0
    return {"service": service, "samples": len(entries), "good": good, "total": total, "achieved_percent": percent}
