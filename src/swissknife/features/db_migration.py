from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


class Connection(Protocol):
    def execute(self, statement: Any, parameters: Any = None) -> Any: ...
    def commit(self) -> None: ...
    def rollback(self) -> None: ...


@dataclass(slots=True)
class MigrationStats:
    read: int = 0
    written: int = 0
    batches: int = 0


def migrate(
    source: Connection,
    target: Connection,
    select_sql: str,
    insert_sql: str,
    batch_size: int = 1000,
    execute: bool = False,
) -> MigrationStats:
    cursor = source.execute(select_sql)
    stats = MigrationStats()
    while True:
        rows = cursor.fetchmany(batch_size)
        if not rows:
            break
        stats.read += len(rows)
        if execute:
            try:
                target.executemany(insert_sql, rows)  # type: ignore[attr-defined]
                target.commit()
            except Exception:
                target.rollback()
                raise
            stats.written += len(rows)
        stats.batches += 1
    return stats
