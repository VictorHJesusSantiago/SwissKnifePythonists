from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from typing import Any


def request(
    url: str,
    method: str = "GET",
    payload: dict[str, Any] | None = None,
    timeout: float = 10,
    retries: int = 2,
    headers: dict[str, str] | None = None,
) -> tuple[int, bytes, float]:
    body = json.dumps(payload).encode() if payload is not None else None
    merged = {"User-Agent": "SwissKnifePythonists/1.0", **(headers or {})}
    if body:
        merged.setdefault("Content-Type", "application/json")
    error: Exception | None = None
    for attempt in range(retries + 1):
        started = time.monotonic()
        try:
            with urllib.request.urlopen(
                urllib.request.Request(url, data=body, headers=merged, method=method),
                timeout=timeout,
            ) as response:
                return response.status, response.read(), time.monotonic() - started
        except (urllib.error.URLError, TimeoutError) as exc:
            error = exc
            if attempt < retries:
                time.sleep(0.25 * (2**attempt))
    raise RuntimeError(f"Falha ao acessar {url}: {error}") from error
