from __future__ import annotations

import csv
import json
import sqlite3
from pathlib import Path
from typing import Any, Callable, Iterable


Record = dict[str, Any]


def extract_csv(path: str | Path) -> list[Record]:
    with Path(path).open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def extract_json(path: str | Path) -> list[Record]:
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    return value if isinstance(value, list) else [value]


def transform(records: Iterable[Record], mapping: dict[str, str], defaults: Record | None = None) -> list[Record]:
    return [
        {**(defaults or {}), **{target: row.get(source) for source, target in mapping.items()}}
        for row in records
    ]


def load_sqlite(records: Iterable[Record], database: str | Path, table: str) -> int:
    rows = list(records)
    if not rows:
        return 0
    columns = list(rows[0])
    if not table.replace("_", "").isalnum() or any(not c.replace("_", "").isalnum() for c in columns):
        raise ValueError("Identificador SQL inválido")
    with sqlite3.connect(database) as connection:
        connection.execute(
            f"CREATE TABLE IF NOT EXISTS {table} ({','.join(f'{c} TEXT' for c in columns)})"
        )
        connection.executemany(
            f"INSERT INTO {table} ({','.join(columns)}) VALUES ({','.join('?' for _ in columns)})",
            [[row.get(column) for column in columns] for row in rows],
        )
    return len(rows)


def pipeline(extractor: Callable[[], list[Record]], transformer: Callable[[list[Record]], list[Record]], loader: Callable[[list[Record]], int]) -> int:
    return loader(transformer(extractor()))
