from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass, field


@dataclass(slots=True)
class Job:
    name: str
    interval_seconds: float
    action: Callable[[], object]
    last_run: float = field(default=0.0)


class Scheduler:
    def __init__(self) -> None:
        self.jobs: list[Job] = []

    def every(self, seconds: float, name: str, action: Callable[[], object]) -> None:
        if seconds <= 0:
            raise ValueError("Intervalo deve ser positivo")
        self.jobs.append(Job(name, seconds, action))

    def run_pending(self) -> list[tuple[str, object]]:
        now = time.monotonic()
        results = []
        for job in self.jobs:
            if now - job.last_run >= job.interval_seconds:
                results.append((job.name, job.action()))
                job.last_run = now
        return results

    def run_forever(self, tick: float = 1.0) -> None:
        while True:
            self.run_pending()
            time.sleep(tick)
