from __future__ import annotations

import random
import sqlite3
import uuid
from pathlib import Path


FIRST_NAMES = ["Ana", "Bruno", "Carla", "Diego", "Elisa", "Fabio", "Gabriela", "Hugo"]
LAST_NAMES = ["Silva", "Souza", "Oliveira", "Santos", "Costa", "Lima"]


def generate_customers(count: int, seed: int = 42) -> list[dict[str, str]]:
    rng = random.Random(seed)
    rows = []
    for index in range(count):
        first, last = rng.choice(FIRST_NAMES), rng.choice(LAST_NAMES)
        rows.append(
            {
                "id": str(uuid.UUID(int=rng.getrandbits(128))),
                "name": f"{first} {last}",
                "email": f"{first.lower()}.{last.lower()}{index}@example.test",
                "document": f"{rng.randrange(10**10, 10**11 - 1):011d}",
            }
        )
    return rows


def persist_sqlite(rows: list[dict[str, str]], path: str | Path) -> int:
    with sqlite3.connect(path) as db:
        db.execute("CREATE TABLE IF NOT EXISTS customers(id TEXT PRIMARY KEY,name TEXT,email TEXT,document TEXT)")
        db.executemany(
            "INSERT OR REPLACE INTO customers VALUES(:id,:name,:email,:document)", rows
        )
    return len(rows)
