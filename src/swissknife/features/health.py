from __future__ import annotations

import socket
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass

from swissknife.core.http import request
from swissknife.core.models import Result, Status


@dataclass(slots=True)
class HealthTarget:
    name: str
    host: str
    port: int = 443
    url: str | None = None
    timeout: float = 5


def check(target: HealthTarget) -> Result:
    started = time.monotonic()
    try:
        with socket.create_connection((target.host, target.port), timeout=target.timeout):
            tcp_ms = round((time.monotonic() - started) * 1000, 2)
        metrics: dict[str, float | int | str] = {"tcp_ms": tcp_ms}
        if target.url:
            status_code, _, elapsed = request(target.url, timeout=target.timeout, retries=0)
            metrics.update(http_status=status_code, http_ms=round(elapsed * 1000, 2))
            if status_code >= 400:
                return Result(target.name, Status.CRITICAL, f"HTTP {status_code}", metrics)
        return Result(target.name, Status.OK, "Serviço disponível", metrics)
    except Exception as exc:
        return Result(target.name, Status.CRITICAL, str(exc))


def check_all(targets: list[HealthTarget], workers: int = 10) -> list[Result]:
    with ThreadPoolExecutor(max_workers=workers) as pool:
        return list(pool.map(check, targets))
