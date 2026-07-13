from __future__ import annotations

import json
import sqlite3
from contextlib import closing
from datetime import UTC, datetime
from pathlib import Path


def _connect(database: str | Path) -> sqlite3.Connection:
    Path(database).parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(database)
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS deploy_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            environment TEXT NOT NULL,
            version TEXT NOT NULL,
            artifact TEXT NOT NULL,
            deployed_at TEXT NOT NULL,
            status TEXT NOT NULL,
            metadata TEXT NOT NULL
        )
        """
    )
    connection.commit()
    return connection


def record_deploy(
    database: str | Path,
    environment: str,
    version: str,
    artifact: str,
    status: str = "success",
    metadata: dict[str, object] | None = None,
) -> dict[str, object]:
    deployed_at = datetime.now(UTC).isoformat()
    with closing(_connect(database)) as connection:
        cursor = connection.execute(
            "INSERT INTO deploy_history (environment, version, artifact, deployed_at, status, metadata) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (environment, version, artifact, deployed_at, status, json.dumps(metadata or {})),
        )
        connection.commit()
        return {"id": cursor.lastrowid, "environment": environment, "version": version, "deployed_at": deployed_at}


def history(database: str | Path, environment: str, limit: int = 20) -> list[dict[str, object]]:
    with closing(_connect(database)) as connection:
        rows = connection.execute(
            "SELECT id, version, artifact, deployed_at, status, metadata FROM deploy_history "
            "WHERE environment = ? ORDER BY id DESC LIMIT ?",
            (environment, limit),
        ).fetchall()
    return [
        {
            "id": row[0],
            "version": row[1],
            "artifact": row[2],
            "deployed_at": row[3],
            "status": row[4],
            "metadata": json.loads(row[5]),
        }
        for row in rows
    ]


def plan_rollback(database: str | Path, environment: str) -> dict[str, object]:
    entries = history(database, environment, limit=50)
    successful = [entry for entry in entries if entry["status"] == "success"]
    if len(successful) < 2:
        return {"possible": False, "reason": "Não há versão anterior bem-sucedida registrada"}
    current, previous = successful[0], successful[1]
    return {
        "possible": True,
        "environment": environment,
        "current_version": current["version"],
        "target_version": previous["version"],
        "target_artifact": previous["artifact"],
        "steps": [
            f"Validar disponibilidade do artefato {previous['artifact']}",
            f"Reimplantar versão {previous['version']} em {environment}",
            "Executar health-check pós-rollback",
            f"Registrar rollback como novo deploy de {previous['version']}",
        ],
    }
