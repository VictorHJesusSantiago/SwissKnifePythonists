from __future__ import annotations

from typing import Any, Protocol

from swissknife.core.models import Result, Status


class QueryConnection(Protocol):
    def execute(self, statement: str) -> Any: ...


QUERIES = {
    "postgresql": "SELECT COALESCE(EXTRACT(EPOCH FROM now() - pg_last_xact_replay_timestamp()), 0)",
    "mysql": "SHOW REPLICA STATUS",
}


def check(connection: QueryConnection, engine: str, warning: float = 10, critical: float = 60) -> Result:
    if engine not in QUERIES:
        raise ValueError(f"Banco não suportado: {engine}")
    result = connection.execute(QUERIES[engine])
    if engine == "postgresql":
        lag = float(result.scalar() if hasattr(result, "scalar") else result[0])
    else:
        row = result.mappings().first() if hasattr(result, "mappings") else result
        lag = float(row.get("Seconds_Behind_Source", row.get("Seconds_Behind_Master", 0)) or 0)
    status = Status.CRITICAL if lag >= critical else Status.WARNING if lag >= warning else Status.OK
    return Result(engine, status, f"Lag de replicação: {lag:.2f}s", {"lag_seconds": lag})
